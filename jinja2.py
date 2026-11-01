"""
Lightweight fallback for jinja2 Template rendering when jinja2 package is not installed.
"""

import re
from typing import Any


class Template:
    def __init__(self, template_str: str):
        self.template_str = template_str

    def render(self, **context: Any) -> str:
        res = re.sub(r'\{#.*?#\}', '', self.template_str, flags=re.DOTALL)
        for k, v in context.items():
            res = re.sub(r'\{\{\s*' + re.escape(str(k)) + r'\s*\}\}', str(v), res)
        return res


__all__ = ["Template"]

