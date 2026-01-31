from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .schema import GraphNode, GraphEdge


@dataclass(slots=True)
class LineageSnapshot:
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)




