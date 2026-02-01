from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class FileSpan:
    path: str
    start_line: int
    end_line: int
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text
        }


@dataclass
class CandidateMatch:
    path: str
    line_number: int
    matched_text: str
    context_before: str = ""
    context_after: str = ""

    def to_span(self, window_size: int = 10) -> FileSpan:
        return FileSpan(
            path=self.path,
            start_line=max(1, self.line_number - window_size),
            end_line=self.line_number + window_size,
            text=self.context_before + self.matched_text + self.context_after
        )