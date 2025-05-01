"""
Wiki API client for ontology-based content management.

This module provides the Onto2WikiClient class for automated interaction with a wiki website's API.
It handles ontology processing, page hierarchy generation, and bulk content operations while maintaining session state.

**Key Features:**

- Session management with persistent connections
- Ontology parsing and transformation to wiki content
- Automated page creation/deletion with hierarchy support
- Configuration through environment variables
- Integrated logging with rotation

**Dependencies:**

- ``requests``: HTTP session management
- ``python-dotenv``: Environment configuration
- ``logging``: Activity tracking and debugging

**Example Usage:**

.. code-block:: python

    >>> from onto2wiki.web_client import Onto2WikiClient
    >>> client = Onto2WikiClient(dotenv_path="config.env")
    >>> client("ontology.ttl", "Main_Page")

**Workflow:**

1. Authentication using provided credentials
2. Ontology parsing with configurable parser
3. Content synchronization (remove old → create new pages)
4. Hierarchy generation and main page updates

**Note:** Requires valid .env configuration with:

- ``URL_API``: Wiki API endpoint
- ``LOGIN``/``PASSWORD``: Authentication credentials (if needed)
- ``CSRFToken``: Cross-site request forgery token
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from sys import prefix

from dotenv import dotenv_values

from requests import Session

from .exceptions import LoginException
from .parser import BaseParser, TTLParser
from .utils import find_roots


class Onto2WikiClient(Session):
    """A client for interacting with a wiki website via its API.

    Provides functionality for managing pages, processing ontologies,
    and automating content generation. Inherits from `requests.Session` to maintain session state.

    :param str dotenv_path: Path to the .env configuration file (default: ".env")
    :param BaseParser parser: Parser for ontology processing (default: `TTLParser`)
    """

    @property
    def parser(self):
        """Current ontology parser instance.

        :type: BaseParser
        """
        return self.__parser

    @parser.setter
    def parser(self, value):
        """Set the ontology parser.

        :param BaseParser value: Parser instance
        :raises TypeError: If invalid parser type is provided
        """
        if not isinstance(value, BaseParser):
            raise TypeError("Parser must be subclass of BaseParser")
        self.__parser = value

    @property
    def config(self):
        """Loaded configuration dictionary.

        :type: dict
        """
        return self.__config

    @config.setter
    def config(self, value):
        """Update configuration from .env file.

        :param str value: Path to the .env file
        """
        self.__config = dotenv_values(value)

    def __init__(self, dotenv_path='.env', parser=None):
        """Initialize the client.

        :param str dotenv_path: Path to the .env configuration file
        :param BaseParser parser: Ontology parser (default: TTLParser)
        """
        super().__init__()
        self.headers = {
            'User-Agent': 'Onto2WikiClient',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }

        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler = RotatingFileHandler(
            filename=os.getcwd() + '/' + self.__class__.__name__ + '.log',
            maxBytes=1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__logger.addHandler(file_handler)
        self.__logger.setLevel(logging.DEBUG)

        self.__parser = TTLParser() if parser is None else parser
        self.__config = dotenv_values(dotenv_path)

    def login(self):
        """Authenticate with the wiki using credentials from configuration.

        Uses:
        - ``LOGIN``: Username from config
        - ``PASSWORD``: Password from config

        :raises LoginException: On authentication failure
        :raises Exception: On network/API errors
        """
        params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'login|csrf',
            'format': 'json'
        }
        try:
            req = self.get(url=self.config['URL_API'], params=params, headers=self.headers)
        except Exception as e:
            self.__logger.error(e)
            raise e
        self.config.update(req.json()['query']['tokens'])

        if 'LOGIN' in self.config and 'PASSWORD' in self.config:
            log_params = {
                'action': 'login',
                'lgname': self.config['LOGIN'],
                'lgpassword': self.config['PASSWORD'],
                'lgtoken': self.config['logintoken'],
                'format': 'json'
            }
            try:
                req = self.post(self.config['URL_API'], data=log_params, headers=self.headers).json()
            except Exception as e:
                self.__logger.error(e)
                raise e

            if req['login']['result'].lower() != 'success':
                self.__logger.error(f'Can`t login to {self.config["URL_API"]} with {self.config["LOGIN"]}')
                raise LoginException('Login failed: ' + req['login']['reason'])

            self.__logger.debug(f'Connected to {self.config["URL_API"]} with name {self.config["LOGIN"]}')

            self.config.update({'lgusername': req['login']['lgusername']})
            req = self.get(url=self.config['URL_API'], params=params, headers=self.headers)
            self.config.update(req.json()['query']['tokens'])

        else:
            self.__logger.error('Unspecified login or password.')
            raise LoginException('Unspecified login or password.')

    def get_hierarchy_page(self, pages, me, visited, i):
        """Recursively generate wiki-formatted hierarchy text.

        :param dict pages: Dictionary of pages
        :param str me: Current page name
        :param list visited: List of visited pages
        :param int i: Nesting level
        :return: Hierarchy text in wiki markup
        :rtype: str
        """
        text = f'{"*" * i} [[{" ".join(me.split("_"))}]]\n'
        visited.append(me)
        for children in pages[me].get('children', ''):
            if children not in visited:
                text += self.get_hierarchy_page(pages, children, visited, i + 1)
        return text

    def add_hierarchy_page(self, postfix: str, pages, roots):
        """Create hierarchy pages for root elements.

        :param str postfix: Suffix for page titles (e.g., ".Hierarchy")
        :param dict pages: Dictionary of pages
        :param list roots: Root elements of the hierarchy
        """
        for root in roots:
            me = root
            visited = ['']
            i = 1
            text = self.get_hierarchy_page(pages, me, visited, i)

            params = {
                'action': 'edit',
                'format': 'json',
                'title': ' '.join(root.split('_')) + postfix,
                'text': 'Данная страница сгенерирована ботом, её необходимо заполнить.\n' + text,
                'bot': 1,
                'token': self.config['csrftoken'],
                'formatversion': '2'
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            if 'error' in req:
                self.__logger.error(f'Can`t create page {params["title"]}: {req["error"]["info"]}')
            if req['edit']['result'].lower() == 'success':
                self.__logger.debug(f'Created page {params["title"]}')

    def delete_hierarchy_page(self, postfix: str, roots):
        """Delete hierarchy pages associated with root elements.

        :param str postfix: Suffix to append to root names
        :param Iterable roots: Collection of root page names
        """
        for root in roots:
            params = {
                'action': 'delete',
                'format': 'json',
                'title': ' '.join(root.split('_')) + postfix,
                'bot': 1,
                'token': self.config['csrftoken'],
                'formatversion': '2'
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            if 'error' in req:
                self.__logger.error(f'Can`t delete page {params["title"]}: {req["error"]["info"]}')
            else:
                self.__logger.debug(f'Deleted page {params["title"]}')

    def add_new_page(self, page) -> bool:
        """Create new page with related sections.

        :param dict page: Dictionary with page data containing:

            - title (str): Page title
            - text (str): Page content
            - children (list): Optional child pages
            - parent (str): Optional parent page
        :return: True if page was created successfully
        :rtype: bool
        """
        added_flag = False
        text = page.get('text', '')
        params = {
            'action': 'edit',
            'format': 'json',
            'title': page['title'],
            'text': text + ' Данная страница сгенерирована ботом, её необходимо заполнить.',
            'bot': 1,
            'token': self.config['csrftoken'],
            'formatversion': '2'
        }
        req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
        if 'error' in req:
            self.__logger.error(f'Can`t create page {params["title"]}: {req["error"]["info"]}')
        else:
            added_flag = req['edit']['result'].lower() == 'success'

        if added_flag:
            self.__logger.debug(f'Created page {params["title"]}')

        if 'children' in page:
            childrens = ''
            for children in page['children']:
                childrens += '* [[' + ' '.join(children.split('_')) + ']]' + '\n'
            params = {
                'action': 'edit',
                'format': 'json',
                'title': page['title'],
                'section': 'new',
                'sectiontitle': 'Childrens',
                'text': childrens,
                'bot': 1,
                'token': self.config['csrftoken'],
                'formatversion': '2'
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            if 'error' in req:
                self.__logger.error(f'Can`t create page {params["title"]}: {req["error"]["info"]}')

        if 'parent' in page:
            params = {
                'action': 'edit',
                'format': 'json',
                'title': page['title'],
                'section': 'new',
                'sectiontitle': 'Parent',
                'text': '* [[' + ' '.join(page['parent'].split('_')) + ']]' + '\n',
                'token': self.config['csrftoken'],
                'formatversion': '2'
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            if 'error' in req:
                self.__logger.error(f'Can`t create page {params["title"]}: {req["error"]["info"]}')

        return added_flag

    def dell_page(self, page):
        """Delete wiki page.

        :param dict page: Dictionary containing page title
        """
        if page:
            params = {
                'action': 'delete',
                'format': 'json',
                'title': page['title'],
                'token': self.config['csrftoken'],
                'formatversion': '2'
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            if 'error' in req:
                self.__logger.error(f'Can`t delete page {params["title"]}: {req["error"]["info"]}')
            else:
                self.__logger.debug(f'Deleted page {params["title"]}')

    def modify_main_page(self, main_page: str, roots: list, postfix: str) -> None:
        """Update main page with new hierarchy sections.

        :param str main_page: Name of main page
        :param list roots: Root elements to display
        :param str postfix: Suffix for section titles
        """
        parse_params = {
            'action': 'parse',
            'format': 'json',
            'page': main_page,
            'formatversion': '2'
        }

        req = self.post(url=self.config['URL_API'], data=parse_params, headers=self.headers).json()

        if 'error' in req:
            self.__logger.error(f'Can`t create page {main_page}: {req["error"]["info"]}')
            raise Exception(f'Can`t parse {main_page}: {req["error"]["info"]}')
        sections = req['parse']['sections']
        params = {
            'action': 'edit',
            'format': 'json',
            'title': main_page,
            'section': 'new',
            'formatversion': '2'
        }
        roots = sorted(roots)
        for root in roots:
            root_section = list(filter(lambda x: ' '.join(root.split('_')) + postfix == x['line'], sections))
            if len(root_section) == 0:
                req = self.post(url=self.config['URL_API'],
                                data=params | {'text': f'== [[{" ".join(root.split("_"))}{postfix}]] ==',
                                               'bot': 1,
                                               'token': self.config['csrftoken']},
                                headers=self.headers).json()
                if 'error' in req:
                    self.__logger.error(f'Can`t modify page {main_page}: {req["error"]["info"]}')
                else:
                    self.__logger.debug(f'Modified page {main_page}')
            elif len(root_section) > 1:
                self.__logger.error(f'Find more then 1 section named {root + prefix}')
                raise Exception('Find more then 1 section named ' + root + prefix)

    def __call__(self, ontology_path: str, main_page: str, **kwargs) -> None:
        """Execute full workflow.

        Workflow steps:
        1. Authenticate
        2. Delete old pages
        3. Create new pages
        4. Generate hierarchies
        5. Update main page

        :param str ontology_path: Path to ontology file
        :param str main_page: Name of main page
        """
        self.login()
        pages = self.parser(ontology_path, **kwargs)
        for page in pages.values():
            self.dell_page(page)
            self.add_new_page(page)
        roots = find_roots(pages)
        self.add_hierarchy_page('. Иерархия тем', pages, roots)
        self.modify_main_page(main_page, roots, '. Иерархия тем')