from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import FileSpan, CandidateMatch


class ReadTool:
    def __init__(self, max_file_size: Optional[int] = None, ignore_file: Optional[str] = None):
        self.max_file_size = max_file_size or int(os.getenv('READ_MAX_FILE_SIZE', '5048576'))
        self.ignore_file = ignore_file or self._find_ignore_file()
        self.ignore_patterns = self._load_ignore_patterns()

    def _find_ignore_file(self) -> Optional[str]:
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            rgignore_path = current_dir / '.rgignore'
            if rgignore_path.exists():
                return str(rgignore_path)
            current_dir = current_dir.parent

        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            gitignore_path = current_dir / '.gitignore'
            if gitignore_path.exists():
                return str(gitignore_path)
            current_dir = current_dir.parent

        package_dir = Path(__file__).parent.parent
        bundled_rgignore = package_dir / '.rgignore'
        if bundled_rgignore.exists():
            return str(bundled_rgignore)

        return None

    def _load_ignore_patterns(self) -> List[str]:
        patterns = []
        if self.ignore_file and os.path.exists(self.ignore_file):
            try:
                with open(self.ignore_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except (OSError, UnicodeDecodeError):
                pass
        return patterns

    def _should_ignore_file(self, file_path: str) -> bool:
        import fnmatch

        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
            parts = Path(file_path).parts
            for i in range(len(parts)):
                path_part = '/'.join(parts[i:])
                if fnmatch.fnmatch(path_part, pattern):
                    return True
        return False

    def read_file(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        window_size: Optional[int] = None,
        encoding: str = "utf-8"
    ) -> FileSpan:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if self._should_ignore_file(file_path):
            raise ValueError(f"File is ignored by ignore patterns: {file_path}")

        if os.path.getsize(file_path) > self.max_file_size:
            raise ValueError(f"File too large: {file_path}")

        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            lines = f.readlines()

        if start_line is not None:
            start_idx = max(0, start_line - 1)
        else:
            start_idx = 0

        if end_line is not None:
            end_idx = min(len(lines), end_line)
        else:
            end_idx = min(len(lines), start_line + window_size + 1 if start_line is not None and window_size is not None else len(lines))

        if window_size is not None and start_line is not None:
            start_idx = max(0, start_idx - window_size)
            end_idx = min(len(lines), start_line + window_size + 1)

        selected_lines = lines[start_idx:end_idx]
        content = ''.join(selected_lines).rstrip()

        actual_start_line = start_idx + 1
        actual_end_line = start_idx + len(selected_lines)

        return FileSpan(
            path=file_path,
            start_line=actual_start_line,
            end_line=actual_end_line,
            text=content
        )

    def read_spans_from_candidates(
        self,
        candidates: List[CandidateMatch],
        window_size: Optional[int] = None
    ) -> List[FileSpan]:
        results = self.read_spans_from_candidates_with_line_number(candidates, window_size)
        return [r['span'] for r in results]

    def read_spans_from_candidates_with_line_number(
        self,
        candidates: List[CandidateMatch],
        window_size: Optional[int] = None
    ) -> List[Dict[str, Union[FileSpan, int]]]:
        """Returns list of dicts with 'span' and 'original_line_number' keys."""
        window_size = window_size if window_size is not None else int(os.getenv('CONTEXT_WINDOW_SIZE', '10'))

        unique_candidates = []
        seen = set()

        for candidate in candidates:
            file_path = candidate.path
            if self._should_ignore_file(file_path):
                continue

            key = (file_path, candidate.line_number)
            if key in seen:
                continue

            seen.add(key)
            unique_candidates.append(candidate)

        max_workers = min(len(unique_candidates), int(os.getenv('READ_MAX_WORKERS', '64')))

        if max_workers == 0:
            return []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                (executor.submit(self._read_candidate_file, candidate, window_size), candidate.line_number)
                for candidate in unique_candidates
            ]
            
            results = []
            for future, original_line in futures:
                try:
                    span = future.result()
                    if span:
                        results.append({'span': span, 'original_line_number': original_line})
                except (FileNotFoundError, ValueError, Exception):
                    pass

        return results

    def _read_candidate_file(
        self,
        candidate: CandidateMatch,
        window_size: int
    ) -> Optional[FileSpan]:
        try:
            return self.read_file(
                file_path=candidate.path,
                start_line=candidate.line_number,
                end_line=None,
                window_size=window_size
            )
        except (FileNotFoundError, ValueError, Exception):
            return None

    def search_and_read(
        self,
        file_path: str,
        search_terms: List[str],
        context_lines: Optional[int] = None,
        case_sensitive: bool = False
    ) -> List[FileSpan]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        matches = []
        context_lines = context_lines or 10

        for line_num, line in enumerate(lines, 1):
            line_text = line.strip()
            search_text = line_text if case_sensitive else line_text.lower()

            for term in search_terms:
                search_term = term if case_sensitive else term.lower()

                if search_term in search_text:
                    start_line = max(1, line_num - context_lines)
                    end_line = min(len(lines), line_num + context_lines)

                    span = self.read_file(
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line
                    )
                    matches.append(span)
                    break

        return matches

    def extract_function_or_class(
        self,
        file_path: str,
        target_name: str,
        language: str = "auto"
    ) -> Optional[FileSpan]:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        if language == "auto":
            language = self._detect_language_from_path(file_path)

        language = language.lower()
        if language == "python":
            return self._extract_python_definition(lines, target_name)
        elif language == "javascript" or language == "js":
            return self._extract_javascript_definition(lines, target_name)
        elif language == "typescript" or language == "ts":
            return self._extract_typescript_definition(lines, target_name)
        elif language == "java":
            return self._extract_java_definition(lines, target_name)
        elif language == "go" or language == "golang":
            return self._extract_go_definition(lines, target_name)
        elif language == "rust" or language == "rs":
            return self._extract_rust_definition(lines, target_name)
        elif language == "cpp" or language == "c++" or language == "c":
            return self._extract_cpp_definition(lines, target_name)
        elif language == "php":
            return self._extract_php_definition(lines, target_name)
        elif language == "ruby" or language == "rb":
            return self._extract_ruby_definition(lines, target_name)
        elif language == "csharp" or language == "c#" or language == "cs":
            return self._extract_csharp_definition(lines, target_name)
        else:
            return self._extract_generic_definition(lines, target_name, language)

    def _extract_python_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        pattern = re.compile(rf'^\s*(def|class)\s+{re.escape(target_name)}\s*\(')

        for i, line in enumerate(lines):
            if pattern.match(line):
                start_line = i + 1
                base_indent = len(line) - len(line.lstrip())

                end_line = len(lines)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= base_indent:
                        if not lines[j].strip().startswith('#'):
                            end_line = j + 1
                            break

                return FileSpan(
                    path="",
                    start_line=start_line,
                    end_line=end_line,
                    text=''.join(lines[start_line - 1:end_line - 1]).rstrip()
                )

        return None

    def _detect_language_from_path(self, file_path: str) -> str:
        path = Path(file_path)
        extension = path.suffix.lower()

        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.mjs': 'javascript',
            '.cjs': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.c': 'c',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.php': 'php',
            '.rb': 'ruby',
            '.cs': 'csharp',
            '.vb': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.dart': 'dart',
            '.lua': 'lua',
            '.r': 'r',
            '.m': 'objective-c',
            '.sh': 'shell',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
        }

        return extension_map.get(extension, 'unknown')

    def _extract_javascript_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*function\s+{re.escape(target_name)}\s*\([^)]*\)\s*\{{',
            rf'^\s*const\s+{re.escape(target_name)}\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{{',
            rf'^\s*const\s+{re.escape(target_name)}\s*=\s*(?:async\s+)?function\s*\([^)]*\)',
            rf'^\s*let\s+{re.escape(target_name)}\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{{',
            rf'^\s*var\s+{re.escape(target_name)}\s*=\s*(?:async\s+)?function\s*\([^)]*\)',
            rf'^\s*{re.escape(target_name)}\s*:\s*(?:async\s+)?function\s*\([^)]*\)',
            rf'^\s*class\s+{re.escape(target_name)}\b',
            rf'^\s*{re.escape(target_name)}\s*=\s*\{{',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_bracket_block(lines, i, target_name)

        return None

    def _extract_typescript_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*function\s+{re.escape(target_name)}\s*\([^)]*\)\s*:',
            rf'^\s*(?:public|private|protected)?\s*(?:static)?\s*(?:async)?\s*{re.escape(target_name)}\s*\([^)]*\)\s*:',
            rf'^\s*const\s+{re.escape(target_name)}\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*',
            rf'^\s*class\s+{re.escape(target_name)}\b',
            rf'^\s*interface\s+{re.escape(target_name)}\b',
            rf'^\s*type\s+{re.escape(target_name)}\s*=',
            rf'^\s*(?:export\s+)?(?:default\s+)?class\s+{re.escape(target_name)}',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_bracket_block(lines, i, target_name)

        return None

    def _extract_java_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*(?:public|private|protected)?\s*(?:static)?\s*(?:final|abstract|synchronized)?\s*(?:\w+\s+)?{re.escape(target_name)}\s*\([^)]*\)',
            rf'^\s*(?:public|private|protected)?\s*(?:static)?\s*(?:final|abstract)?\s*class\s+{re.escape(target_name)}',
            rf'^\s*(?:public|private|protected)?\s*interface\s+{re.escape(target_name)}',
            rf'^\s*(?:public|private|protected)?\s*enum\s+{re.escape(target_name)}',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_bracket_block(lines, i, target_name)

        return None

    def _extract_go_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*func\s+(?:\([^)]*\)\s+)?{re.escape(target_name)}\s*\([^)]*\)(?:\s*[^{{]*)?\s*\{{',
            rf'^\s*type\s+{re.escape(target_name)}\s+(?:struct|interface)',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_bracket_block(lines, i, target_name)

        return None

    def _extract_rust_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*(?:pub\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+{re.escape(target_name)}\s*\([^)]*\)(?:\s*->\s*\w+)?',
            rf'^\s*(?:pub\s+)?struct\s+{re.escape(target_name)}',
            r'^\s*(?:pub\s+)?impl\s+.*\s+\{[^}]*\bfn\s+' + re.escape(target_name),
            rf'^\s*(?:pub\s+)?trait\s+{re.escape(target_name)}',
            rf'^\s*(?:pub\s+)?enum\s+{re.escape(target_name)}',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_bracket_block(lines, i, target_name)

        return None

    def _extract_cpp_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*(?:\w+\s+)*{re.escape(target_name)}\s*\([^)]*\)(?:\s*const)?\s*(?:override\s+)?(?:final\s+)?\{{',
            rf'^\s*(?:virtual\s+)?{re.escape(target_name)}\s*\([^)]*\)(?:\s*=\s*0)?',
            rf'^\s*class\s+{re.escape(target_name)}',
            rf'^\s*struct\s+{re.escape(target_name)}',
            rf'^\s*(?:template\s*<[^>]*>\s*)?class\s+{re.escape(target_name)}',
            rf'^\s*(?:template\s*<[^>]*>\s*)?struct\s+{re.escape(target_name)}',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_bracket_block(lines, i, target_name)

        return None

    def _extract_php_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*function\s+{re.escape(target_name)}\s*\([^)]*\)',
            rf'^\s*(?:public|private|protected)?\s*(?:static)?\s*function\s+{re.escape(target_name)}\s*\([^)]*\)',
            rf'^\s*class\s+{re.escape(target_name)}',
            rf'^\s*interface\s+{re.escape(target_name)}',
            rf'^\s*trait\s+{re.escape(target_name)}',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_bracket_block(lines, i, target_name)

        return None

    def _extract_ruby_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*def\s+(?:self\.)?{re.escape(target_name)}',
            rf'^\s*class\s+{re.escape(target_name)}',
            rf'^\s*module\s+{re.escape(target_name)}',
            rf'^\s*(?:private|protected|public)\s*:.*\ndef\s+{re.escape(target_name)}',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_indentation_block(lines, i, target_name)

        return None

    def _extract_csharp_definition(self, lines: List[str], target_name: str) -> Optional[FileSpan]:
        import re

        patterns = [
            rf'^\s*(?:public|private|protected|internal)?\s*(?:static)?\s*(?:async)?\s*(?:virtual|override|abstract)?\s*\w+\s+{re.escape(target_name)}\s*\([^)]*\)',
            rf'^\s*(?:public|private|protected|internal)?\s*(?:static)?\s*(?:abstract)?\s*class\s+{re.escape(target_name)}',
            rf'^\s*(?:public|private|protected|internal)?\s*interface\s+{re.escape(target_name)}',
            rf'^\s*(?:public|private|protected|internal)?\s*struct\s+{re.escape(target_name)}',
            rf'^\s*(?:public|private|protected|internal)?\s*enum\s+{re.escape(target_name)}',
        ]

        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return self._extract_bracket_block(lines, i, target_name)

        return None

    def _extract_generic_definition(self, lines: List[str], target_name: str, language: str) -> Optional[FileSpan]:
        for i, line in enumerate(lines):
            if target_name in line:
                window = 10
                start_line = max(1, i + 1 - window)
                end_line = min(len(lines), i + 1 + window)
                return self.read_file("", start_line, end_line)
        return None

    def _extract_bracket_block(self, lines: List[str], start_idx: int, target_name: str) -> Optional[FileSpan]:
        start_line = start_idx + 1
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        brace_count = 0
        for j in range(start_idx, len(lines)):
            if '{' in lines[j]:
                brace_count += lines[j].count('{')
                if brace_count > 0:
                    start_line = j + 1
                    break

        end_line = len(lines)
        for j in range(start_line - 1, len(lines)):
            brace_count += lines[j].count('{')
            brace_count -= lines[j].count('}')
            if brace_count == 0:
                end_line = j + 1
                break

        return FileSpan(
            path="",
            start_line=start_line,
            end_line=end_line,
            text=''.join(lines[start_line - 1:end_line - 1]).rstrip()
        )

    def _extract_indentation_block(self, lines: List[str], start_idx: int, target_name: str) -> Optional[FileSpan]:
        start_line = start_idx + 1
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        end_line = len(lines)
        for j in range(start_idx + 1, len(lines)):
            if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= base_indent:
                if not lines[j].strip().startswith('#'):
                    end_line = j + 1
                    break

        return FileSpan(
            path="",
            start_line=start_line,
            end_line=end_line,
            text=''.join(lines[start_line - 1:end_line - 1]).rstrip()
        )
