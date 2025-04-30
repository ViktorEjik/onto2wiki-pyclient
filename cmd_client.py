import cmd
import shlex
from importlib import import_module
from parser import TTLParser

from tqdm import tqdm

from utils import find_roots

from web_client import Onto2WikiClient


class CMDClient(cmd.Cmd):
    prompt = 'o2WiKi %-> '

    def __init__(self):
        super().__init__()
        self.client = Onto2WikiClient()
        self.curr_parser = TTLParser()
        self.parsers = {}
        self.pages = {}
        self.roots = []

    def do_list_config(self, arg):
        for k, v in self.client.config.items():
            print(f'  {k}: {v}')

    def do_current_parser(self, arg):
        print(' ', self.curr_parser.__class__.__name__)

    def do_set_config(self, arg):
        self.client.config = arg

    def do_set_parser(self, arg):
        if arg in self.parsers:
            self.curr_parser = self.parsers[arg]
        else:
            print('Invalid parser')

    def do_add_parser(self, args):
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
        print(' ', *map(str, self.parsers.keys()))

    def do_parse(self, arg):
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
        try:
            self.client.login()
        except Exception as e:
            print(f'Can`t login to {self.client.config["URL_API"]}. Error: {e}')

    def do_create_pages(self, args):
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
        self.client.add_hierarchy_page('. Иерархия тем', self.pages, self.roots)

    def do_remove_pages(self, args):
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
        args = shlex.split(args)
        if args:
            self.client.delete_hierarchy_page('. Иерархия тем', filter(lambda x: x in args, self.roots))
        else:
            self.client.delete_hierarchy_page('. Иерархия тем', self.roots)

    def do_create_all(self, args):
        self.do_create_pages(args)
        self.do_add_hierarchy_pages(args)

    def do_remove_all(self, args):
        self.do_remove_pages(args)
        self.do_remove_hierarchy_pages(args)

    def do_modify_main_pages(self, args):
        self.client.modify_main_page(args, self.roots, '. Иерархия тем')

    @staticmethod
    def do_exit(arg):
        return True


if __name__ == '__main__':
    CMDClient().cmdloop()
