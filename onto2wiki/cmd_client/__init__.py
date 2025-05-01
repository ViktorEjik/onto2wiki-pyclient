"""
Onto2Wiki CLI - Interactive command shell for ontology management on MediaWiki.

This module provides a command-line interface for bulk operations with ontology-based
content on MediaWiki instances. Designed for administrators and ontology engineers.

Key Features:
- Interactive shell with autocompletion
- Multi-parser support for ontology formats
- Batch page creation/deletion
- Hierarchy management
- Configuration management
- Progress visualization

Command Structure:
All commands follow pattern: `command [args...]`
Use `help` to see available commands or `help <command>` for specific syntax.

Basic Workflow:
1. Configure API settings → login
2. Load ontology → modify content
3. Execute batch operations
4. Verify results

Example Session:
    o2WiKi %-> set_config .env
    o2WiKi %-> login
    o2WiKi %-> parse ontology.ttl namespace=http://example.org/ontology
    o2WiKi %-> create_all
    o2WiKi %-> exit
"""
import cmd
import shlex
from importlib import import_module

from colorama import Fore, Style

from tqdm import tqdm

from onto2wiki.parser import TTLParser
from onto2wiki.utils import find_roots
from onto2wiki.web_client import Onto2WikiClient


class CMDClient(cmd.Cmd):
    """Interactive shell for Onto2Wiki operations."""

    prompt = Fore.GREEN + 'o2WiKi %-> ' + Style.RESET_ALL

    def __init__(self):
        """Initialize command-line interface components.

        Sets up:
        - Wiki API client
        - Default ontology parser (TTL)
        - Parser registry
        - Page storage
        - Root element cache
        """
        super().__init__()
        self.client = Onto2WikiClient()
        self.parsers = {TTLParser.__name__: TTLParser()}
        self.curr_parser = self.parsers[TTLParser.__name__]
        self.pages = {}
        self.roots = []

    def do_list_config(self, arg):
        """Display current configuration"""
        for k, v in self.client.config.items():
            print(f'  {k}: {v}')

    def do_current_parser(self, arg):
        """Show active ontology parser"""
        print(' ', self.curr_parser.__class__.__name__)

    def do_set_config(self, arg):
        """Load configuration from .env file

        Usage: set_config /path/to/config.env
        """
        self.client.config = arg

    def do_set_parser(self, arg):
        """Change ontology parser

        Usage: set_parser parser_name
        """
        if arg in self.parsers:
            self.curr_parser = self.parsers[arg]
        else:
            print('Invalid parser')

    def do_add_parser(self, args):
        """Register new parser implementation

        Usage: add_parser ParserName module
        """
        parse_name, module = None, None
        try:
            parse_name, module = shlex.split(args)
        except ValueError:
            print('Invalid arguments')
        try:
            self.parsers[parse_name] = getattr(import_module(module), parse_name)()
        except Exception as e:
            print(f'Can`t add parser {parse_name}. Error: {e}')

    def do_list_parsers(self, arg):
        """List available ontology parsers"""
        print(' ', *map(str, self.parsers.keys()))

    def do_parse(self, arg):
        """Load and process ontology file

        Usage: parse /path/to/file.ttl [key=value...]
        """
        try:
            path, *args = shlex.split(arg)
        except ValueError:
            print('Invalid arguments')
            return
        kwargs = dict(map(lambda x: x.split('='), args))

        try:
            self.pages = self.curr_parser(path, **kwargs)
        except Exception as e:
            print(f'Can`t parse {path}. Error: {e}')

        self.roots = find_roots(self.pages)
        print(f'Detected {len(self.pages)} pages')

    def do_login(self, args):
        """Authenticate with wiki API"""
        try:
            self.client.login()
        except Exception as e:
            print(f'Can`t login to {self.client.config["URL_API"]}. Error: {e}')

    def do_create_pages(self, args):
        """Create pages from ontology

        Usage: create_pages [page1 page2...|empty=all]
        """
        pages = shlex.split(args)
        count = 0
        if not pages:
            for page in tqdm(self.pages.values()):
                count += self.client.add_new_page(page)
        else:
            for page in tqdm(pages):
                if page in self.pages:
                    count += self.client.add_new_page(self.pages[page])
        print(f'Created {count} pages')

    def do_add_hierarchy_pages(self, args):
        """Generate hierarchy navigation pages"""
        self.client.add_hierarchy_page('. Иерархия тем', self.pages, self.roots)

    def do_remove_pages(self, args):
        """Delete wiki pages

        Usage: remove_pages [page1 page2...|empty=all]
        """
        args = shlex.split(args)
        count = 0
        if args:
            for page_name in tqdm(args):
                page = self.pages.get(page_name)
                if page is not None:
                    self.client.dell_page(page)
                    count += 1
        else:
            for page in tqdm(self.pages.values()):
                self.client.dell_page(page)
                count += 1
        print(f'Removed {count} pages')

    def do_remove_hierarchy_pages(self, args):
        """Delete hierarchy pages

        Usage: remove_hierarchy_pages [root1...|empty=all]
        """
        args = shlex.split(args)
        if args:
            self.client.delete_hierarchy_page('. Иерархия тем', filter(lambda x: x in args, self.roots))
        else:
            self.client.delete_hierarchy_page('. Иерархия тем', self.roots)

    def do_create_all(self, args):
        """Create all pages + hierarchies (full deploy)"""
        self.do_create_pages(args)
        self.do_add_hierarchy_pages(args)

    def do_remove_all(self, args):
        """Remove all pages + hierarchies (full cleanup)"""
        self.do_remove_pages(args)
        self.do_remove_hierarchy_pages(args)

    def do_modify_main_pages(self, args):
        """Update main page sections

        Usage: modify_main_pages Main_Page
        """
        self.client.modify_main_page(args, self.roots, '. Иерархия тем')

    @staticmethod
    def do_exit(arg):
        """Exit the application"""
        return True

__all__ = [
    'CMDClient'
]
