from requests import Session
from dotenv import dotenv_values

from parser import BaseParser, TTLParser
from utils import find_roots

class Onto2WikiClient(Session):

    @property
    def parser(self):
        return self.__parser

    @parser.setter
    def parser(self, value):
        if not isinstance(value, BaseParser):
            raise TypeError()
        self.__parser = value

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, value):
        self.__config = dotenv_values(value)

    def __init__(self, dotenv_path='.env', parser=TTLParser()):
        super().__init__()
        self.headers = {
            'User-Agent': 'Onto2WikiClient',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
        self.__parser = parser
        self.__config = dotenv_values(dotenv_path)

    def login(self):
        params = {
            'action':"query",
            'meta':"tokens",
            "type": "login|csrf",
            'format':"json"
        }
        req = self.get(url=self.config['URL_API'], params=params, headers=self.headers)
        self.config.update(req.json()['query']['tokens'])

        if "LOGIN" in self.config and "PASSWORD" in self.config:
            log_params = {
                "action": "login",
                'lgname': self.config['LOGIN'],
                'lgpassword': self.config['PASSWORD'],
                'lgtoken': self.config['logintoken'],
                'format': "json"
            }
            req = self.post(self.config['URL_API'], data=log_params, headers=self.headers).json()
            if req['login']['result'].lower() != 'success':
                raise Exception("Login failed: " + req['login']['reason'])
            self.config.update({'lgusername': req['login']['lgusername']})
            req = self.get(url=self.config['URL_API'], params=params, headers=self.headers)
            print(req.text)
            self.config.update(req.json()['query']['tokens'])
            print(self.config)
        else: raise Exception("Login failed")

    def get_hierarchy_page(self, pages, me, visited, i):
        text = f'{"*" * i} [[{' '.join(me.split('_'))}]]\n'
        visited.append(me)
        for children in pages[me].get('children', ''):
            if children not in visited:
                text += self.get_hierarchy_page(pages, children, visited, i + 1)
        return text

    def add_hierarchy_page(self, postfix: str, pages, roots):
        for root in roots:
            me = root
            visited = ['']
            i = 1
            text = self.get_hierarchy_page(pages, me, visited, i)
            params = {
                "action": "edit",
                "format": "json",
                "title": ' '.join(root.split('_')) + postfix,
                "text": "Данная страница сгенерирована ботом, её необходимо заполнить.\n" + text,
                "bot": 1,
                "token": self.config['csrftoken'],
                "formatversion": "2"
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            print(req)

    def delete_hierarchy_page(self, postfix: str, roots):
        for root in roots:
            params = {
                "action": "delete",
                "format": "json",
                "title": ' '.join(root.split('_')) + postfix,
                "bot": 1,
                "token": self.config['csrftoken'],
                "formatversion": "2"
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            print(req)

    def add_new_page(self, page):

        text = page.get('text', '')
        params = {
            "action": "edit",
            "format": "json",
            "title":  page['title'],
            "text": text + "Данная страница сгенерирована ботом, её необходимо заполнить.",
            "bot": 1,
            "token": self.config['csrftoken'],
            "formatversion": "2"
        }
        req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
        print(req)

        if 'children' in page:
            childrens = ''
            for children in page['children']:
                childrens += '* [[' + ' '.join(children.split("_")) + ']]' + '\n'
            params = {
                "action": "edit",
                "format": "json",
                "title": page['title'],
                "section": "new",
                "sectiontitle": "Childrens",
                "text": childrens,
                "bot": 1,
                "token": self.config['csrftoken'],
                "formatversion": "2"
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            print(req)

        if 'parent' in page:
            params = {
                "action": "edit",
                "format": "json",
                "title": page['title'],
                "section": "new",
                "sectiontitle": "Parent",
                "text": '* [[' + ' '.join(page['parent'].split('_')) + ']]' + '\n',
                "token": self.config['csrftoken'],
                "formatversion": "2"
            }
            req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
            print(req)

    def dell_page(self, page):
        params = {
            "action": "delete",
            "format": "json",
            "title": page['title'],
            "token": self.config['csrftoken'],
            "formatversion": "2"
        }
        req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
        print(req)

    def modify_main_page(self, main_page, roots, postfix):
        parse_params = {
            "action": "parse",
            "format": "json",
            "page": main_page,
            "formatversion": "2"
        }

        req = self.post(url=self.config['URL_API'], data=parse_params, headers=self.headers).json()
        # pprint(req)
        if 'error' in req:
            raise Exception(f'Can`t parse {main_page}: {req["error"]["info"]}')
        sections = req['parse']['sections']
        params = {
            "action": "edit",
            "format": "json",
            "title": main_page,
            "section": "new",
            "formatversion": "2"
        }
        roots = sorted(roots)
        for root in roots:
            root_section = list(filter(lambda x: ' '.join(root.split('_')) + postfix == x['line'], sections))
            if len(root_section) == 0:
                req = self.post(url=self.config['URL_API'],
                                data=params|{"text": f"== [[{' '.join(root.split('_'))}{postfix}]] ==",
                                             "bot": 1,
                                             "token": self.config['csrftoken']},
                                headers=self.headers).json()
                print(req)
            elif len(root_section) == 1:
                print('Section exists')
            else:
                raise Exception("Find more then 1 section named " + root + " иерархия тем")
        # req = self.post(url=self.config['URL_API'], data=params, headers=self.headers).json()
        # print(req)


    def __call__(self, ontology_path, main_page):
        self.login()
        pages = self.parser(ontology_path)
        for page in pages.values():
            self.dell_page(page)
            self.add_new_page(page)
        roots = find_roots(pages)
        self.add_hierarchy_page('. Иерархия тем', pages, roots)
        self.modify_main_page(main_page, roots, '. Иерархия тем')