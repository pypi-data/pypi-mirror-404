from __future__ import annotations

import os
import re
import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base import CandidateMatch


class GrepTool:
    def __init__(self, ignore_file: Optional[str] = None):
        self.rg_command = self._find_rg_command()
        self.ignore_file = ignore_file or self._find_ignore_file()

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

    def _find_rg_command(self) -> str:
        import platform
        import os
        from pathlib import Path

        package_dir = Path(__file__).parent.parent
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "windows":
            rg_path = package_dir / "binaries" / "rg.exe"
        elif system == "darwin":
            if machine in ["arm64", "aarch64"]:
                rg_path = package_dir / "binaries" / "rg-darwin-arm64"
            else:
                rg_path = package_dir / "binaries" / "rg-darwin-amd64"
        elif system == "linux":
            rg_path = package_dir / "binaries" / "rg-linux-amd64"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

        if not rg_path.exists():
            raise RuntimeError(f"Bundled ripgrep not found at {rg_path}. Please reinstall the cheetah-grep package.")

        if system != "windows":
            os.chmod(rg_path, 0o755)

        try:
            result = subprocess.run(
                [str(rg_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=False
            )
            if result.returncode == 0:
                return str(rg_path)
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Bundled ripgrep failed to execute: {e}. Please reinstall the cheetah-grep package.")

        raise RuntimeError(f"Bundled ripgrep at {rg_path} is not working. Please reinstall the cheetah-grep package.")

    def search(
        self,
        query: str,
        directory: Optional[str] = None,
        file_patterns: Optional[List[str]] = None,
        case_sensitive: bool = False,
        context_lines: int = 10
    ) -> List[CandidateMatch]:
        return self._search_with_ripgrep(query, directory, file_patterns, case_sensitive, context_lines)

    def _search_with_ripgrep(
        self,
        query: str,
        directory: Optional[str] = None,
        file_patterns: Optional[List[str]] = None,
        case_sensitive: bool = False,
        context_lines: int = 10
    ) -> List[CandidateMatch]:
        cmd = [self.rg_command, "--json", "--no-heading", "--line-number", "--fixed-strings"]

        if context_lines > 0:
            cmd.extend(["--context", str(context_lines)])

        if case_sensitive:
            cmd.append("--case-sensitive")
        else:
            cmd.append("--ignore-case")

        if self.ignore_file:
            cmd.extend(["--ignore-file", self.ignore_file])

        if file_patterns:
            for pattern in file_patterns:
                cmd.extend(["--glob", pattern])

        cmd.append(query)

        if directory:
            cmd.append(directory)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            try:
                stdout, stderr = process.communicate(timeout=3)
                
                if process.returncode != 0 and process.returncode != 1:
                    raise RuntimeError(f"ripgrep failed: {stderr}")
                
                return self._parse_rg_output(stdout)
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                partial_results = self._parse_rg_output(stdout)
                return partial_results
                
        except Exception as e:
            return []

    def _parse_rg_output(self, output: Optional[str]) -> List[CandidateMatch]:
        matches = []

        if not output or not output.strip():
            return matches

        context_buffer: Dict[str, List[Dict[str, Any]]] = {}

        for line in output.strip().split('\n'):
            try:
                data = json.loads(line)

                if data.get("type") == "match":
                    path = data["data"]["path"]["text"]
                    line_number = data["data"]["line_number"]
                    matched_text = data["data"]["lines"]["text"].strip()

                    context_before = ""
                    context_after = ""

                    if path in context_buffer:
                        context_items = context_buffer[path]
                        for item in context_items:
                            if item["line_number"] < line_number:
                                context_before += item["text"] + "\n"
                            else:
                                context_after += item["text"] + "\n"

                    match = CandidateMatch(
                        path=path,
                        line_number=line_number,
                        matched_text=matched_text,
                        context_before=context_before.strip(),
                        context_after=context_after.strip()
                    )
                    matches.append(match)

                    if path in context_buffer:
                        del context_buffer[path]

                elif data.get("type") == "context":
                    path = data["data"]["path"]["text"]
                    line_number = data["data"]["line_number"]
                    text = data["data"]["lines"]["text"].strip()

                    if path not in context_buffer:
                        context_buffer[path] = []
                    context_buffer[path].append({
                        "line_number": line_number,
                        "text": text
                    })

            except (json.JSONDecodeError, KeyError):
                continue

        return matches

    def search_patterns(
        self,
        patterns: List[str],
        directory: Optional[str] = None
    ) -> List[CandidateMatch]:
        all_matches = []

        for pattern in patterns:
            matches = self.search(
                query=pattern,
                directory=directory,
                case_sensitive=True
            )
            all_matches.extend(matches)

        unique_matches = self._deduplicate_matches(all_matches)
        return sorted(unique_matches, key=lambda m: (m.path, m.line_number))[:self.max_results]

    def _deduplicate_matches(self, matches: List[CandidateMatch]) -> List[CandidateMatch]:
        seen = set()
        unique_matches = []

        for match in matches:
            key = (match.path, match.line_number, match.matched_text)
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)

        return unique_matches
