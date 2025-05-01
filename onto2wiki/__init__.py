"""
onto2wiki - Python client for ontology-based wiki content management.

This package provides tools for interacting with MediaWiki instances to manage
ontology-driven content, including automated page creation, hierarchy generation,
and configuration management.

**Key Components:**

- ``Onto2WikiClient``: Main class for wiki API interactions
- ``BaseParser``/``TTLParser``: Ontology parsing implementations
- ``find_roots``: Utility for hierarchical data processing
- ``LoginException``: Custom authentication error handling

**Example Usage:**

.. code-block:: python

    >>> from onto2wiki.web_client import Onto2WikiClient
    >>> from onto2wiki.parser import TTLParser
    >>> client = Onto2WikiClient()
    >>> ttl_parser = TTLParser()
    >>> ontology = ttl_parser("ontology.ttl", namespace="http://example.org/ontology")
    >>> client.login()
    >>> for page in ontology.values():
    >>>     client.add_new_page(page)

**Dependencies:**

- ``requests``: HTTP session management
- ``python-dotenv``: Configuration handling
- ``logging``: Activity tracking

**Workflow:**
1. Initialize client and parser
2. Load ontology data
3. Authenticate with wiki API
4. Process and upload content
5. Generate navigation hierarchies
"""
from onto2wiki.exceptions import LoginException
from onto2wiki.parser import BaseParser, TTLParser
from onto2wiki.web_client import Onto2WikiClient


__all__ = [
    'Onto2WikiClient',
    'LoginException',
    'BaseParser',
    'TTLParser'
]
