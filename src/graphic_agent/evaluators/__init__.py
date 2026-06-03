"""Pluggable evaluator system.

Each evaluator implements the ``Evaluator`` protocol and is registered by name
so that scenario YAML files can reference them in ``evaluators:`` lists.
"""

from graphic_agent.evaluators.registry import Evaluator, get_evaluator, list_evaluators

__all__ = ["Evaluator", "get_evaluator", "list_evaluators"]
