import asyncio
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, TypedDict
from concurrent.futures import ThreadPoolExecutor

import httpx
from mcp.server.fastmcp import FastMCP

logging.getLogger("httpx").setLevel(logging.WARNING)
mcp = FastMCP("greb-mcp")
GPU_API_URL = os.getenv("GREB_API_URL") or os.getenv("GREB_GPU_API_URL") or "https://search.grebmcp.com"
USER_AGENT = "greb-mcp/2.1.0"


class ExtractedKeywords(TypedDict):
    primary_terms: List[str]
    file_patterns: List[str]
    intent: str
    code_patterns: Optional[List[str]]


def reciprocal_rank_fusion(
    ranked_lists: List[List[Any]],
    k: int = 60,
    max_results: int = 200
) -> List[Any]:
    score_map = {}
    
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list):
            key = f"{item.path}:{item.line_number}"
            rrf_score = 1 / (k + rank + 1)
            
            if key in score_map:
                score_map[key]['score'] += rrf_score
            else:
                score_map[key] = {'score': rrf_score, 'item': item}
    
    sorted_items = sorted(score_map.values(), key=lambda x: x['score'], reverse=True)
    return [entry['item'] for entry in sorted_items[:max_results]]


def stratified_sample(
    candidates: List[Any],
    max_candidates: int = 200,
    min_per_stratum: int = 5
) -> List[Any]:
    if len(candidates) <= max_candidates:
        return candidates
    
    strata = {}
    for candidate in candidates:
        ext = candidate.path.split('.')[-1].lower() if '.' in candidate.path else 'unknown'
        if ext not in strata:
            strata[ext] = []
        strata[ext].append(candidate)
    
    strata_count = len(strata)
    selected = []
    
    guaranteed_per_stratum = min(min_per_stratum, max_candidates // strata_count)
    
    for items in strata.values():
        selected.extend(items[:guaranteed_per_stratum])
    
    remaining = max_candidates - len(selected)
    if remaining > 0:
        total_remaining = len(candidates) - len(selected)
        
        for ext, items in strata.items():
            already_taken = guaranteed_per_stratum
            remaining_in_stratum = items[already_taken:]
            
            if remaining_in_stratum and total_remaining > 0:
                proportion = len(remaining_in_stratum) / total_remaining
                allocation = int(remaining * proportion) + 1
                selected.extend(remaining_in_stratum[:allocation])
    
    seen = set()
    deduped = []
    for item in selected:
        key = f"{item.path}:{item.line_number}"
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    
    return deduped[:max_candidates]


def score_by_keyword_coverage(
    candidates: List[Any],
    keywords: List[str],
    path_boost_multiplier: int = 2
) -> List[Any]:
    normalized_keywords = [k.lower() for k in keywords]
    
    for candidate in candidates:
        content = (
            (candidate.context_before or '') +
            candidate.matched_text +
            (candidate.context_after or '')
        ).lower()
        
        path_lower = candidate.path.lower()
        
        content_hits = sum(1 for kw in normalized_keywords if kw in content)
        path_hits = sum(1 for kw in normalized_keywords if kw in path_lower)
        
        candidate.keyword_coverage = content_hits + (path_hits * path_boost_multiplier)
    
    return sorted(candidates, key=lambda c: getattr(c, 'keyword_coverage', 0), reverse=True)


async def make_greb_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=json_data)
            else:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API request error: {e}", file=sys.stderr)
            return None


def _smart_deduplicate(candidates: List, keywords: List[str]) -> List:
    from collections import defaultdict
    
    file_candidates = defaultdict(list)
    for candidate in candidates:
        file_candidates[candidate.path].append(candidate)
    
    result = []
    
    for file_path, file_cands in file_candidates.items():
        best_per_keyword = {}
        
        for candidate in file_cands:
            matched_text_lower = candidate.matched_text.lower()
            context_lower = (
                (candidate.context_before or '') +
                matched_text_lower +
                (candidate.context_after or '')
            ).lower()
            
            matched_keyword = None
            for kw in keywords:
                if kw.lower() in context_lower:
                    if matched_keyword is None:
                        matched_keyword = kw
            
            if matched_keyword:
                if matched_keyword not in best_per_keyword:
                    best_per_keyword[matched_keyword] = candidate
                else:
                    existing = best_per_keyword[matched_keyword]
                    existing_context = len(existing.context_before or '') + len(existing.context_after or '')
                    new_context = len(candidate.context_before or '') + len(candidate.context_after or '')
                    if new_context > existing_context:
                        best_per_keyword[matched_keyword] = candidate
            else:
                if 'no_keyword' not in best_per_keyword:
                    best_per_keyword['no_keyword'] = candidate
        
        seen_ranges = []
        
        def ranges_overlap(s1, e1, s2, e2):
            return s1 <= e2 and s2 <= e1
        
        for keyword, candidate in best_per_keyword.items():
            start_line = candidate.line_number
            context_lines = len((candidate.context_after or '').split('\n')) if candidate.context_after else 0
            end_line = start_line + context_lines
            
            if any(ranges_overlap(start_line, end_line, s, e) for s, e in seen_ranges):
                continue
            
            seen_ranges.append((start_line, end_line))
            result.append(candidate)
    
    return result


def _select_search_terms(terms: List[str], n: int) -> List[str]:
    return terms[:n] if terms else []


def _turn2_ast_references(
    grep_tool,
    previous_results: List,
    search_context,
    directory: str,
    file_patterns: Optional[List[str]]
) -> List:
    from .pipeline.code_analyzer import FastCodeAnalyzer
    
    code_analyzer = FastCodeAnalyzer()
    
    top_files = search_context.get_high_quality_files(n=5)
    if not top_files:
        top_files = [r.path for r in previous_results[:5]]
    
    all_references = []
    for file_path in top_files:
        try:
            refs = code_analyzer.extract_references_fast(file_path)
            all_references.extend(refs)
        except Exception:
            continue
    
    unique_refs = []
    for ref in all_references:
        if search_context.has_seen_pattern(ref.name):
            continue
        unique_refs.append(ref)
    
    top_refs = unique_refs[:2]
    
    candidates = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for ref in top_refs:
            if ref.type == 'import':
                pattern = ref.name
            elif ref.type == 'function_call':
                pattern = f"def {ref.name}"
            elif ref.type == 'function_def':
                pattern = f"{ref.name}("
            elif ref.type == 'class_def':
                pattern = f"class {ref.name}"
            else:
                pattern = ref.name
            
            if pattern and not search_context.has_seen_pattern(pattern):
                search_context.add_pattern(pattern)
                future = executor.submit(
                    grep_tool.search,
                    query=pattern,
                    directory=directory,
                    file_patterns=file_patterns,
                    case_sensitive=False,
                    context_lines=10
                )
                futures.append(future)
        
        for future in futures:
            try:
                results = future.result(timeout=3)
                candidates.extend(results)
            except Exception:
                continue
    
    return candidates


@mcp.tool()
async def code_search(
    query: str,
    keywords: ExtractedKeywords,
    directory: str = "."
) -> str:
    """Search code using natural language queries powered by AI.

    Args:
        query: Natural language query describing what you're looking for
        keywords: Keywords extracted by the AI agent. Must include:
            - primary_terms: CRITICAL - Must be SINGLE WORDS only, not phrases. Examples: ["auth", "jwt", "login", "session"] NOT ["user authentication", "login flow"]. These are grep search terms.
            - code_patterns: Optional. Literal code patterns to grep for. Use specific patterns like "function authenticate(", "jwt.verify", "class AuthService"
            - file_patterns: File extensions to search (e.g., ["*.py", "*.js"])
            - intent: Brief description of what you're looking for
        directory: IMPORTANT - Run `pwd` command to get the current working directory path, then use that exact path here. Do NOT make up paths or guess directory names. Do NOT use relative paths like "." or "src". Always use the absolute path from pwd.
    """
    api_key = os.getenv("GREB_API_KEY")
    if not api_key:
        return "Error: GREB_API_KEY environment variable is required"

    # Use provided directory, fallback to cwd if not provided or invalid
    if not directory or directory == "." or directory == "":
        directory = os.getcwd()
    
    # If relative path, use cwd
    if not os.path.isabs(directory):
        directory = os.getcwd()
    
    # If directory doesn't exist, fallback to cwd
    if not os.path.exists(directory):
        directory = os.getcwd()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }

    from .pipeline.grep import GrepTool
    from .pipeline.search_context import SearchContext
    
    grep_tool = GrepTool()
    search_context = SearchContext()
    
    code_patterns = keywords.get("code_patterns", [])
    semantic_terms = keywords.get("primary_terms", [])
    file_pats = keywords.get("file_patterns")
    
    grep_terms = _select_search_terms(code_patterns, n=4)
    semantic_grep_terms = _select_search_terms(semantic_terms, n=2)
    
    all_search_terms = grep_terms + semantic_grep_terms
    for term in all_search_terms:
        search_context.add_pattern(term)
    
    code_pattern_results = []
    semantic_results = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        code_futures = []
        for term in grep_terms:
            future = executor.submit(
                grep_tool.search,
                query=term,
                directory=directory,
                file_patterns=file_pats,
                case_sensitive=False,
                context_lines=10
            )
            code_futures.append(future)
        
        for future in code_futures:
            try:
                results = future.result(timeout=3)
                if results:
                    code_pattern_results.append(results)
            except Exception:
                continue
        
        semantic_futures = []
        for term in semantic_grep_terms:
            future = executor.submit(
                grep_tool.search,
                query=term,
                directory=directory,
                file_patterns=file_pats,
                case_sensitive=False,
                context_lines=10
            )
            semantic_futures.append(future)
        
        for future in semantic_futures:
            try:
                results = future.result(timeout=3)
                if results:
                    semantic_results.append(results)
            except Exception:
                continue
    
    all_ranked_lists = code_pattern_results + semantic_results
    
    if len(all_ranked_lists) > 1:
        fused_candidates = reciprocal_rank_fusion(all_ranked_lists, k=60, max_results=500)
    elif len(all_ranked_lists) == 1:
        fused_candidates = all_ranked_lists[0]
    else:
        fused_candidates = []
    
    search_context.update_from_results(fused_candidates)
    
    turn2_candidates = _turn2_ast_references(
        grep_tool=grep_tool,
        previous_results=fused_candidates,
        search_context=search_context,
        directory=directory,
        file_patterns=file_pats
    )
    
    if turn2_candidates:
        fused_candidates = reciprocal_rank_fusion(
            [fused_candidates, turn2_candidates],
            k=60,
            max_results=600
        )
    search_context.update_from_results(turn2_candidates)
    
    unique_matches = _smart_deduplicate(fused_candidates, all_search_terms)
    
    if not unique_matches:
        return f"No results found for query: '{query}'"
    
    scored_matches = score_by_keyword_coverage(unique_matches, all_search_terms, path_boost_multiplier=2)
    limited_matches = stratified_sample(scored_matches, max_candidates=200, min_per_stratum=10)
    
    from .pipeline.read import ReadTool
    
    read_tool = ReadTool(max_file_size=500000)
    match_lookup = {}
    for match in limited_matches:
        key = (match.path, match.line_number)
        if key not in match_lookup:
            match_lookup[key] = match
    
    spans_with_line = read_tool.read_spans_from_candidates_with_line_number(limited_matches, window_size=10)
    
    candidates = []
    for item in spans_with_line:
        span = item['span']
        original_line = item['original_line_number']
        key = (span.path, original_line)
        original_match = match_lookup.get(key)
        
        candidate = {
            "path": span.path,
            "start_line": span.start_line,
            "end_line": span.end_line,
            "content": span.text,
        }
        if original_match:
            candidate["matched_text"] = original_match.matched_text
            candidate["context_before"] = original_match.context_before or ""
            candidate["context_after"] = original_match.context_after or ""
            candidate["line_number"] = original_match.line_number
            candidates.append(candidate)
        else:
            continue
    
    try:
        gpu_response = await make_greb_request(
            method="POST",
            url=f"{GPU_API_URL}/v1/gpu-rerank",
            headers=headers,
            json_data={
                "query": query,
                "candidates": candidates,
                "keywords": {
                    "primary_terms": keywords.get("primary_terms", []),
                    "code_patterns": keywords.get("code_patterns", []),
                    "search_terms": keywords.get("primary_terms", []),
                    "file_patterns": keywords.get("file_patterns", []),
                    "intent": keywords.get("intent", query)
                },
                "top_k": 10
            }
        )
        
        if not gpu_response:
            return "Error: GPU rerank service unavailable"
        
        results = gpu_response.get('results', [])
        overall_reasoning = gpu_response.get('overall_reasoning')
        
    except Exception as e:
        return f"Error calling GPU rerank service: {e}"
    
    if not results:
        return f"No results found for query: '{query}'"

    merged_by_file = {}
    for result in results:
        file_path = result.get('path', 'unknown')
        if file_path not in merged_by_file:
            merged_by_file[file_path] = []
        merged_by_file[file_path].append({
            'score': result.get('score', 0.0),
            'start_line': result.get('start_line', 1),
            'end_line': result.get('end_line', 1),
            'content': result.get('content', ''),
            'reasoning': result.get('reasoning', '')
        })

    formatted_results = [f"## Found {len(merged_by_file)} files for: {query}\n"]
    
    for file_index, (file_path, spans) in enumerate(merged_by_file.items(), 1):
        spans.sort(key=lambda s: s['start_line'])
        max_score = max(s['score'] for s in spans)
        
        formatted_result = f"\n### {file_index}. {file_path}\n"
        formatted_result += f"**Relevance Score:** {max_score:.3f}\n"
        
        for span_idx, span in enumerate(spans):
            if len(spans) > 1:
                formatted_result += f"\n**Span {span_idx + 1} (Lines {span['start_line']}-{span['end_line']}):**\n"
            else:
                formatted_result += f"**Lines:** {span['start_line']}-{span['end_line']}\n"
            if span['content']:
                formatted_result += f"```\n{span['content']}\n```\n"
        
        formatted_results.append(formatted_result)

    if overall_reasoning:
        formatted_results.append(f"\n**Summary:**\n{overall_reasoning}")

    return "\n".join(formatted_results)


def main():
    import sys
    
    api_key = os.getenv("GREB_API_KEY")
    if not api_key:
        print("ERROR: GREB_API_KEY environment variable is required", file=sys.stderr)
        print("Set it in your MCP client configuration:", file=sys.stderr)
        print('  "env": { "GREB_API_KEY": "grb_your_api_key_here" }', file=sys.stderr)
        sys.exit(1)
    
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"MCP Server Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
