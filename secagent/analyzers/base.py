"""Base class and protocol for SAST analyzers."""

from abc import ABC, abstractmethod
from typing import List
from secagent.state import VulnerabilityCandidate


class BaseAnalyzer(ABC):
    """Abstract interface for static analysis tools."""

    name: str = "base"

    @abstractmethod
    def scan(self, repo_path: str) -> List[VulnerabilityCandidate]:
        """Execute scanner on the target repository and return raw candidates."""
        raise NotImplementedError
