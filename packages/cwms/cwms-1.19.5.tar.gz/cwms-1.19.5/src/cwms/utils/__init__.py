"""Utility modules for context window management.

This package provides shared utilities used across the cwms
package, avoiding circular dependencies.
"""

from __future__ import annotations

from cwms.utils.text import _extract_proper_nouns, extract_keywords

__all__ = ["extract_keywords", "_extract_proper_nouns"]
