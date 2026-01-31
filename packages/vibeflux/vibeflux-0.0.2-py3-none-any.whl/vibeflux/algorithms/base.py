from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class AlgoResult:
    ok: bool
    metrics: Dict[str, float]
    payload: Dict[str, Any]

class BaseAlgorithm:
    """Minimal interface for VibeFlux algorithms."""
    name: str = "base"

    def run(self, inputs: Dict[str, Any]) -> AlgoResult:
        raise NotImplementedError
