"""
onto2wiki - Python client for ontology-based wiki content management.

This package provides tools for interacting with MediaWiki instances to manage
ontology-driven content, including automated page creation, hierarchy generation,
and configuration management.

Key Components:
- Onto2WikiClient: Main class for wiki API interactions
- BaseParser/TTLParser: Ontology parsing implementations
- find_roots: Utility for hierarchical data processing
- LoginException: Custom authentication error handling

Example Usage:
    >>> from onto2wiki import Onto2WikiClient, TTLParser
    >>> client = Onto2WikiClient()
    >>> parser = TTLParser()
    >>> ontology = parser("ontology.ttl")
    >>> client.login()
    >>> client.create_pages(ontology)

Dependencies:
- requests: HTTP session management
- python-dotenv: Configuration handling
- logging: Activity tracking
"""
from .exceptions import LoginException
from .parser import BaseParser, TTLParser
from .utils import find_roots
from .web_client import Onto2WikiClient


__all__ = [
    'Onto2WikiClient',
    'LoginException',
    'find_roots',
    'BaseParser',
    'TTLParser'
]
