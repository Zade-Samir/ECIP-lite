"""
Architecture Rules — Defines architectural smells, pattern violations, and technical debt rules.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ArchitectureRule:
    rule_id: str
    category: str
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    evaluate_fn: Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], List[Dict[str, Any]]]


def check_oversized_classes(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    violations = []
    for node in nodes:
        lines = node.get("lines_count", 0)
        methods = node.get("methods_count", 0)
        if lines > 500 or methods > 20:
            violations.append({
                "target": node.get("id", "Unknown"),
                "reason": f"Class has {lines} lines and {methods} methods (threshold: 500 lines / 20 methods).",
                "severity": "HIGH",
            })
    return violations


def check_layer_violations(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    violations = []
    # Controller directly accessing Repository without Service layer
    for edge in edges:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if "Controller" in src and "Repository" in tgt:
            violations.append({
                "target": f"{src} -> {tgt}",
                "reason": "Direct dependency from Controller layer to Repository layer bypasses Service layer.",
                "severity": "HIGH",
            })
    return violations


DEFAULT_RULES = [
    ArchitectureRule("oversized_class", "Modularity", "Detects God/Oversized classes", "HIGH", check_oversized_classes),
    ArchitectureRule("layer_violation", "Layering", "Detects architectural layer bypass", "HIGH", check_layer_violations),
]
