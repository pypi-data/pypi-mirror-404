"""Workflow DSL parser."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .types import (
    NodeType,
    Position,
    NodeSpec,
    EdgeSpec,
    WorkflowSpec,
    Workflow,
)


class WorkflowValidationError(Exception):
    """Workflow validation error."""
    
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Workflow validation failed: {'; '.join(errors)}")


class WorkflowParser:
    """Workflow DSL parser."""
    
    def parse(self, source: str | Path) -> Workflow:
        """Parse YAML file or string."""
        raw = self._load_yaml(source)
        spec = self._parse_spec(raw)
        
        errors = self.validate(spec)
        if errors:
            raise WorkflowValidationError(errors)
        
        return self._build_workflow(spec)
    
    def _load_yaml(self, source: str | Path) -> dict[str, Any]:
        """Load YAML from file or string."""
        if isinstance(source, Path):
            with open(source, 'r') as f:
                return yaml.safe_load(f)
        elif isinstance(source, str):
            if source.endswith('.yaml') or source.endswith('.yml'):
                with open(source, 'r') as f:
                    return yaml.safe_load(f)
            else:
                return yaml.safe_load(source)
        raise ValueError(f"Invalid source type: {type(source)}")
    
    def _parse_spec(self, raw: dict[str, Any]) -> WorkflowSpec:
        """Parse raw dict to WorkflowSpec."""
        nodes = []
        for n in raw.get("nodes", []):
            pos_data = n.get("position", {"x": 0, "y": 0})
            position = Position(x=pos_data.get("x", 0), y=pos_data.get("y", 0))
            
            node = NodeSpec(
                id=n["id"],
                type=NodeType(n["type"]),
                position=position,
                agent=n.get("agent"),
                config=n.get("config", {}),
                inputs=n.get("inputs", {}),
                output=n.get("output"),
                when=n.get("when"),
                branches=n.get("branches"),
                steps=n.get("steps"),
                expression=n.get("expression"),
                then_node=n.get("then"),
                else_node=n.get("else"),
            )
            nodes.append(node)
        
        edges = []
        for e in raw.get("edges", []):
            edge = EdgeSpec(
                from_node=e["from"],
                to_node=e["to"],
                when=e.get("when"),
            )
            edges.append(edge)
        
        return WorkflowSpec(
            name=raw["name"],
            version=raw.get("version", "1.0"),
            description=raw.get("description"),
            state=raw.get("state", {}),
            inputs=raw.get("inputs", {}),
            nodes=nodes,
            edges=edges,
        )
    
    def validate(self, spec: WorkflowSpec) -> list[str]:
        """Validate workflow spec."""
        errors = []
        node_ids = {n.id for n in spec.nodes}
        
        # Check edge references
        for edge in spec.edges:
            if edge.from_node not in node_ids:
                errors.append(f"Edge references unknown node: {edge.from_node}")
            if edge.to_node not in node_ids:
                errors.append(f"Edge references unknown node: {edge.to_node}")
        
        # Check for trigger node
        triggers = [n for n in spec.nodes if n.type == NodeType.TRIGGER]
        if not triggers:
            errors.append("Workflow must have at least one trigger node")
        
        # Check for cycles
        if self._has_cycle(spec):
            errors.append("Workflow contains cycles")
        
        # Check agent nodes
        for node in spec.nodes:
            if node.type == NodeType.AGENT and not node.agent:
                errors.append(f"Agent node '{node.id}' must specify 'agent' type")
        
        # Check condition nodes
        for node in spec.nodes:
            if node.type == NodeType.CONDITION:
                if not node.expression:
                    errors.append(f"Condition node '{node.id}' must have 'expression'")
                if not node.then_node:
                    errors.append(f"Condition node '{node.id}' must have 'then'")
        
        return errors
    
    def _has_cycle(self, spec: WorkflowSpec) -> bool:
        """Detect cycles using DFS."""
        visited: set[str] = set()
        rec_stack: set[str] = set()
        
        adj: dict[str, list[str]] = {n.id: [] for n in spec.nodes}
        for edge in spec.edges:
            adj[edge.from_node].append(edge.to_node)
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in spec.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True
        
        return False
    
    def _build_workflow(self, spec: WorkflowSpec) -> Workflow:
        """Build executable workflow."""
        node_map = {n.id: n for n in spec.nodes}
        
        incoming_edges: dict[str, list[str]] = {n.id: [] for n in spec.nodes}
        outgoing_edges: dict[str, list[str]] = {n.id: [] for n in spec.nodes}
        edge_conditions: dict[tuple[str, str], str | None] = {}
        
        for edge in spec.edges:
            incoming_edges[edge.to_node].append(edge.from_node)
            outgoing_edges[edge.from_node].append(edge.to_node)
            edge_conditions[(edge.from_node, edge.to_node)] = edge.when
        
        return Workflow(
            spec=spec,
            node_map=node_map,
            incoming_edges=incoming_edges,
            outgoing_edges=outgoing_edges,
            edge_conditions=edge_conditions,
        )
