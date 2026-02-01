"""
Enrichment plugins are simple classes with:
- a unique string 'name'
- an 'enrich(row: dict[str, str]) -> dict[str, str]' method

They are discovered dynamically at runtime.
"""
