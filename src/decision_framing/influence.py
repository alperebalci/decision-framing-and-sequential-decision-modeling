"""Structural influence-diagram dependency audit, without probabilistic inference.

Arcs are declared by an analyst. Topology validation prevents impossible
information timing and cycles; it does not establish causal identifiability.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InfluenceNode:
    name: str
    kind: str  # chance, decision, value

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("influence node name must be nonempty")
        if self.kind not in ("chance", "decision", "value"):
            raise ValueError("influence node kind must be chance, decision or value")


@dataclass(frozen=True)
class InfluenceArc:
    source: str
    target: str
    relation: str  # causal -> chance, information -> decision, utility -> value


@dataclass(frozen=True)
class InfluenceGraph:
    nodes: tuple[InfluenceNode, ...]
    arcs: tuple[InfluenceArc, ...]

    def validate(self) -> tuple[str, ...]:
        """Return a topological order or reject malformed/retrocausal graphs."""
        kinds = {node.name: node.kind for node in self.nodes}
        if not self.nodes or len(kinds) != len(self.nodes):
            raise ValueError("influence nodes must be nonempty and have unique names")
        graph: dict[str, set[str]] = {name: set() for name in kinds}
        indegree: dict[str, int] = {name: 0 for name in kinds}
        seen = set()
        for arc in self.arcs:
            if arc.source not in kinds or arc.target not in kinds:
                raise ValueError("influence arc refers to an unknown node")
            if arc.source == arc.target:
                raise ValueError("self-reference creates a dependency cycle")
            if (arc.source, arc.target, arc.relation) in seen:
                raise ValueError("duplicate influence arc")
            seen.add((arc.source, arc.target, arc.relation))
            if arc.target in graph[arc.source]:
                raise ValueError("only one relation is allowed for each ordered node pair")

            legal = (
                arc.relation == "causal"
                and kinds[arc.source] in ("decision", "chance")
                and kinds[arc.target] == "chance"
            ) or (
                arc.relation == "information"
                and kinds[arc.source] == "chance"
                and kinds[arc.target] == "decision"
            ) or (
                arc.relation == "utility"
                and kinds[arc.source] in ("chance", "decision")
                and kinds[arc.target] == "value"
            )
            if not legal:
                raise ValueError("invalid influence arc relation or node kinds")
            graph[arc.source].add(arc.target)
            indegree[arc.target] += 1

        ready = [name for name in kinds if indegree[name] == 0]
        order = []
        while ready:
            name = ready.pop(0)
            order.append(name)
            for target in sorted(graph[name]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
        if len(order) != len(kinds):
            raise ValueError("influence graph has a dependency cycle or impossible information timing")
        if not any(node.kind == "decision" for node in self.nodes):
            raise ValueError("influence graph must contain a decision node")
        return tuple(order)
