from __future__ import annotations

import os
import time
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass

import httpx
from pydantic import BaseModel

import re
from concurrent.futures import ThreadPoolExecutor
from .pipeline.grep import GrepTool
from .pipeline.read import ReadTool
from .pipeline.base import CandidateMatch
from .pipeline.code_analyzer import FastCodeAnalyzer, CodeReference
from .pipeline.search_context import SearchContext


class SearchRequest(BaseModel):
    query: str
    candidates: List[Dict[str, Any]]
    max_results: Optional[int] = None


class SearchResult(BaseModel):
    path: str
    score: float
    highlights: List[Dict[str, Any]]
    summary: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    content: Optional[str] = None
    bm42_score: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_candidates: int
    query: str
    execution_time_ms: Optional[float] = None
    extracted_keywords: Optional[Dict[str, Any]] = None
    tools_used: Optional[List[str]] = None
    overall_reasoning: Optional[str] = None


@dataclass
class ClientConfig:
    api_key: str
    base_url: str
    timeout: int = 60
    max_retries: int = 3


class GrebClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        max_grep_results: int = None
    ):
        self.api_key = api_key or os.getenv("GREB_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set GREB_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = base_url or os.getenv("GREB_API_URL")
        if not self.base_url:
            raise ValueError("API base URL is required. Set GREB_API_URL environment variable or pass base_url parameter.")
        
        self.timeout = timeout
        self.max_retries = max_retries
        
        read_max_size = int(os.getenv("READ_MAX_FILE_SIZE", "5048576"))
        self.grep_tool = GrepTool()
        self.read_tool = ReadTool(max_file_size=read_max_size)
        self.code_analyzer = FastCodeAnalyzer()
        self.parallel_per_turn = 2
        
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "greb-python/1.4.0"
            },
        )
    
    def search(
        self,
        query: str,
        keywords: Dict[str, Any],
        directory: Optional[str] = None,
        file_patterns: Optional[List[str]] = None,
        max_results: Optional[int] = None
    ) -> SearchResponse:
        start_time = time.time()
        search_dir = os.path.abspath(directory) if directory else os.getcwd()
        top_k = max_results or int(os.getenv("TOP_K_RESULTS", "10"))
        search_context = SearchContext()
        
        raw_terms = keywords.get("primary_terms", [query])
        search_terms = self._select_best_search_terms(raw_terms, n=self.parallel_per_turn)
        if not search_terms:
            search_terms = raw_terms[:self.parallel_per_turn]
        
        all_candidates: List[CandidateMatch] = []
        
        turn1_candidates = self._turn1_primary_search(
            search_terms=search_terms,
            directory=search_dir,
            file_patterns=file_patterns or keywords.get("file_patterns"),
            search_context=search_context
        )
        all_candidates.extend(turn1_candidates)
        search_context.update_from_results(turn1_candidates)
        
        turn2_candidates = self._turn2_ast_references(
            previous_results=turn1_candidates,
            search_context=search_context,
            directory=search_dir,
            file_patterns=file_patterns or keywords.get("file_patterns")
        )
        all_candidates.extend(turn2_candidates)
        search_context.update_from_results(turn2_candidates)
        
        unique_matches = self._smart_deduplicate(all_candidates, search_terms)
        
        if not unique_matches:
            return SearchResponse(
                results=[],
                total_candidates=0,
                query=query,
                execution_time_ms=0.0,
                overall_reasoning="No matches found for the given query and keywords."
            )
        
        limited_matches = unique_matches[:200]
        
        match_lookup = {}
        for match in limited_matches:
            key = (match.path, match.line_number)
            if key not in match_lookup:
                match_lookup[key] = match
        
        spans_with_line = self.read_tool.read_spans_from_candidates_with_line_number(limited_matches, window_size=10)
        
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
            response = self.client.post(
                "/v1/gpu-rerank",
                json={
                    "query": query,
                    "candidates": candidates,
                    "keywords": {
                        "primary_terms": keywords.get("primary_terms", []),
                        "search_terms": keywords.get("primary_terms", []),
                        "file_patterns": keywords.get("file_patterns", []),
                        "intent": keywords.get("intent", query)
                    },
                    "top_k": top_k
                }
            )
            response.raise_for_status()
            gpu_results = response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API key")
            elif e.response.status_code == 402:
                raise ValueError("Insufficient credits. Add credits to continue.")
            elif e.response.status_code == 429:
                raise ValueError("Rate limit exceeded. Upgrade your plan for more requests.")
            else:
                raise ValueError(f"GPU rerank service error: {e}")
        except Exception as e:
            raise ValueError(f"Failed to call GPU rerank service: {e}")
        
        results = gpu_results.get("results", [])
        search_results = [
            SearchResult(
                path=result.get("path", "unknown"),
                score=result.get("score", 0.0),
                highlights=result.get("highlights", []),
                summary=result.get("highlights", [{}])[0].get("reason", "") if result.get("highlights") else None,
                start_line=result.get("start_line"),
                end_line=result.get("end_line"),
                content=result.get("content"),
                bm42_score=result.get("bm42_score")
            )
            for result in results
        ]
        
        execution_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=search_results,
            total_candidates=len(candidates),
            query=query,
            execution_time_ms=execution_time,
            overall_reasoning=results[0].get("overall_reasoning") if results else None
        )
    
    def _smart_deduplicate(
        self,
        candidates: List[CandidateMatch],
        keywords: List[str]
    ) -> List[CandidateMatch]:
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
    
    def _select_best_search_terms(self, terms: List[str], n: int) -> List[str]:
        scored_terms = []
        
        for term in terms:
            score = 0.0
            score += min(len(term) / 20.0, 0.5)
            if '_' in term or (term != term.lower() and term != term.upper()):
                score += 0.3
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', term):
                score += 0.2
            common_words = ['the', 'a', 'an', 'is', 'in', 'to', 'for', 'of', 'and', 'or']
            if term.lower() in common_words:
                score -= 0.8
            if len(term) < 3:
                score -= 0.3
            scored_terms.append((term, score))
        
        scored_terms.sort(key=lambda x: x[1], reverse=True)
        return [term for term, score in scored_terms[:n] if score > 0]
    
    def _turn1_primary_search(
        self,
        search_terms: List[str],
        directory: str,
        file_patterns: Optional[List[str]],
        search_context: SearchContext
    ) -> List[CandidateMatch]:
        for term in search_terms:
            search_context.add_pattern(term)
        
        candidates = []
        with ThreadPoolExecutor(max_workers=self.parallel_per_turn) as executor:
            futures = []
            for term in search_terms:
                future = executor.submit(
                    self.grep_tool.search,
                    query=term,
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
    
    def _turn2_ast_references(
        self,
        previous_results: List[CandidateMatch],
        search_context: SearchContext,
        directory: str,
        file_patterns: Optional[List[str]]
    ) -> List[CandidateMatch]:
        top_files = search_context.get_high_quality_files(n=5)
        if not top_files:
            top_files = [r.path for r in previous_results[:5]]
        
        all_references: List[CodeReference] = []
        for file_path in top_files:
            try:
                refs = self.code_analyzer.extract_references_fast(file_path)
                all_references.extend(refs)
            except Exception:
                continue
        
        top_refs = self._score_references(all_references, search_context)[:self.parallel_per_turn]
        
        candidates = []
        with ThreadPoolExecutor(max_workers=self.parallel_per_turn) as executor:
            futures = []
            
            for ref in top_refs:
                search_pattern = self._reference_to_search_pattern(ref)
                if search_pattern and not search_context.has_seen_pattern(search_pattern):
                    search_context.add_pattern(search_pattern)
                    future = executor.submit(
                        self.grep_tool.search,
                        query=search_pattern,
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
    
    def _score_references(
        self,
        references: List[CodeReference],
        search_context: SearchContext
    ) -> List[CodeReference]:
        unique_refs = []
        for ref in references:
            if search_context.has_seen_pattern(ref.name):
                continue
            unique_refs.append(ref)
        return unique_refs
    
    def _reference_to_search_pattern(self, ref: CodeReference) -> Optional[str]:
        if ref.type == 'import':
            return ref.name
        elif ref.type == 'function_call':
            return f"def {ref.name}"
        elif ref.type == 'function_def':
            return f"{ref.name}("
        elif ref.type == 'class_def':
            return f"class {ref.name}"
        elif ref.type == 'identifier':
            return ref.name
        return None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        directory: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any] | Iterator[Dict[str, Any]]:
        payload = {
            "model": "greb",
            "messages": messages,
            "stream": stream
        }
        
        if directory:
            payload["metadata"] = {"directory": directory}
        
        if stream:
            return self._stream_chat(payload)
        else:
            response = self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()
    
    def _stream_chat(self, payload: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() != "[DONE]":
                        yield eval(data)
    
    def get_file(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> Dict[str, Any]:
        params = {"file_path": file_path}
        if start_line is not None:
            params["start_line"] = start_line
        if end_line is not None:
            params["end_line"] = end_line
        
        response = self.client.get("/file", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_usage(self) -> Dict[str, Any]:
        response = self.client.get("/usage")
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        response = self.client.get("/health")
        response.raise_for_status()
        return response.json()
    
    def close(self):
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncGrebClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.getenv("GREB_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set GREB_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = base_url or os.getenv("GREB_API_URL")
        if not self.base_url:
            raise ValueError("API base URL is required. Set GREB_API_URL environment variable or pass base_url parameter.")
        
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "swe-grep-python/1.0.0"
            }
        )
    
    async def search(
        self,
        query: str,
        directory: Optional[str] = None,
        file_patterns: Optional[List[str]] = None,
        max_results: Optional[int] = None
    ) -> SearchResponse:
        request = SearchRequest(
            query=query,
            directory=directory,
            file_patterns=file_patterns,
            max_results=max_results
        )
        
        response = await self.client.post(
            "/search",
            json=request.model_dump(exclude_none=True)
        )
        response.raise_for_status()
        
        return SearchResponse(**response.json())
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        directory: Optional[str] = None,
        stream: bool = False
    ):
        payload = {
            "model": "greb",
            "messages": messages,
            "stream": stream
        }
        
        if directory:
            payload["metadata"] = {"directory": directory}
        
        if stream:
            return self._stream_chat(payload)
        else:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()
    
    async def _stream_chat(self, payload: Dict[str, Any]):
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() != "[DONE]":
                        yield eval(data)
    
    async def get_file(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> Dict[str, Any]:
        params = {"file_path": file_path}
        if start_line is not None:
            params["start_line"] = start_line
        if end_line is not None:
            params["end_line"] = end_line
        
        response = await self.client.get("/file", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_usage(self) -> Dict[str, Any]:
        response = await self.client.get("/usage")
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


__all__ = [
    "GrebClient",
    "AsyncGrebClient",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "ClientConfig",
]
