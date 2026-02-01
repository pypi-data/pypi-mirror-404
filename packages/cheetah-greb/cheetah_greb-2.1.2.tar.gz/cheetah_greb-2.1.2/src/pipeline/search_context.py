from __future__ import annotations

from typing import List, Set
from dataclasses import dataclass, field
from .base import CandidateMatch


@dataclass
class SearchContext:
    seen_patterns: Set[str] = field(default_factory=set)
    high_quality_files: Set[str] = field(default_factory=set)

    def update_from_results(self, candidates: List[CandidateMatch]):
        for candidate in candidates:
            if self._is_high_quality_match(candidate):
                self.high_quality_files.add(candidate.path)

    def _is_high_quality_match(self, candidate: CandidateMatch) -> bool:
        if len(candidate.matched_text) > 50:
            return True
        if candidate.context_before or candidate.context_after:
            return True
        definition_keywords = ['def ', 'class ', 'function ', 'const ', 'interface ', 'type ']
        if any(kw in candidate.matched_text for kw in definition_keywords):
            return True
        return False

    def get_high_quality_files(self, n: int = 5) -> List[str]:
        return list(self.high_quality_files)[:n]

    def add_pattern(self, pattern: str):
        self.seen_patterns.add(pattern.lower())

    def has_seen_pattern(self, pattern: str) -> bool:
        return pattern.lower() in self.seen_patterns
