"""
Ensure ANTHROPIC_API_KEY is present before any app module is imported.
app.config reads it at import time via os.environ["ANTHROPIC_API_KEY"].
"""
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-unit-tests")
