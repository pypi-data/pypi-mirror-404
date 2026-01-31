from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Any

@dataclass(frozen=True)
class ComponentSpec:
    name: str
    kind: str  # "algorithm" | "panel" | "workflow" ...
    factory: Callable[[], Any]
    description: str = ""

_REGISTRY: Dict[str, ComponentSpec] = {}

def register(name: str, kind: str, factory: Callable[[], Any], description: str = "") -> None:
    key = f"{kind}:{name}".lower()
    if key in _REGISTRY:
        raise ValueError(f"Component already registered: {key}")
    _REGISTRY[key] = ComponentSpec(name=name, kind=kind, factory=factory, description=description)

def get(name: str, kind: str) -> ComponentSpec:
    key = f"{kind}:{name}".lower()
    if key not in _REGISTRY:
        raise KeyError(f"Component not found: {key}")
    return _REGISTRY[key]

def list_components(kind: Optional[str] = None) -> Dict[str, ComponentSpec]:
    if kind is None:
        return dict(_REGISTRY)
    prefix = f"{kind}:".lower()
    return {k: v for k, v in _REGISTRY.items() if k.startswith(prefix)}
