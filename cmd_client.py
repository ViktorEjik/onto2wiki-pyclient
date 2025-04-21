import cmd
from itertools import count
from pprint import pprint
import shlex

from parser import TTLParser
from utils import find_roots
from web_client import Onto2WikiClient

class CMDClient(cmd.Cmd):
    prompt = 'o2WiKi %-> '
    def __init__(self):
        super().__init__()
        self.client = Onto2WikiClient()
        self.curr_parser = TTLParser()
        self.parsers = {self.curr_parser.__class__.__name__: self.curr_parser, 'llk': ';;;;'}
        self.pages = {}
        self.roots = []

    def do_list_config(self, arg):
        pprint(self.client.config)

    def do_current_parser(self, arg):
        print(self.curr_parser)

    def do_set_config(self, arg):
        self.client.config = arg

    def do_set_parser(self, arg):
        if arg in self.parsers:
            self.curr_parser = self.parsers[arg]
        else:
            print('Invalid parser')

    def do_add_parser(self, args):
        pass

    def do_list_parsers(self, arg):

        pprint(list(map(str, self.parsers.keys())))

    def do_parse(self, arg):
        path, namespace = shlex.split(arg)
        self.pages = self.curr_parser(path, namespace=namespace)
        self.roots = find_roots(self.pages)
        print(f'Detected {len(self.pages)} pages')

    def do_login(self, args):
        self.client.login()

    def do_create_pages(self, args):
        pages = shlex.split(args)
        if not pages:
            for page in self.pages.values():
                self.client.add_new_page(page)
            return
        for page in pages:
            if page in self.pages:
                self.client.add_new_page(self.pages[page])

    def do_add_hierarchy_pages(self, args):
        self.client.add_hierarchy_page('. Иерархия тем', self.pages, self.roots)

    def do_remove_pages(self, args):
        args = shlex.split(args)
        count = 0
        if args:
            for page_name in args:
                page = self.pages.get(page_name)
                if page is not None:
                    self.client.dell_page(page)
                    count += 1
        else:
            for page in self.pages.values():
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