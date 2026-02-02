"""
DBGear Document Generator Plugin

This package provides documentation generation capabilities for DBGear.
It generates documentation from database schema definitions using custom templates.
"""

from .generator import generate_docs

__all__ = [
    "generate_docs",
]
