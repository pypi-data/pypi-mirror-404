from __future__ import annotations
from .base import BaseAlgorithm, AlgoResult
from vibeflux.registry import register

class HelloAlgorithm(BaseAlgorithm):
    name = "hello"

    def run(self, inputs):
        who = inputs.get("who", "VibeFlux")
        return AlgoResult(
            ok=True,
            metrics={"demo_score": 1.0},
            payload={"message": f"Hello, {who}!"},
        )

def _factory():
    return HelloAlgorithm()

# 让 import vibeflux.algorithms 时就自动注册示例算法
register(
    name="hello",
    kind="algorithm",
    factory=_factory,
    description="A minimal demo algorithm that returns a hello message.",
)
