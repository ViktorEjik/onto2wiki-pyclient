import re
import sys
import pathlib

class BaseParser:
    def __init__(self):
        pass
    def __call__(self, path, *args, **kwargs):
        pass

    def __str__(self):
        return self.__class__.__name__

class TTLParser(BaseParser):
    def __init__(self):
        super().__init__()

    @staticmethod
    def __rename_classes(path: str, namespace: str):
        old_new = dict()
        classes = []
        new_file = []
        path = pathlib.Path(path)
        if not path.exists():
            raise FileNotFoundError('Path does not exist')
        elif not path.is_file():
            raise FileNotFoundError('Path dose not a file')

        with open(path, 'r') as f:
            while line := f.readline():
                pars = re.search(r'(\S+) rdf:type (\S+) ;', line)
                if pars:
                    if pars.group(2) != 'owl:Class': raise Exception('Unknown syntaxes')
                    if pars.group(1).startswith(':'):
                        classes.append(pars.group(1)[1:])
                        old_new[pars.group(1)[1:]] = namespace + '#' + pars.group(1)[1:]
                    else:
                        classes.append(pars.group(1).split('#')[1][:-1])

        with open(path, 'r') as f:
            while line := f.readline():
                pars_class = re.search(r'(\S+) rdf:type (\S+) ;', line)
                parse_subclass = re.search(r'rdfs:subClassOf :(\S+)', line[:-2])
                if pars_class:
                    if pars_class.group(2) != 'owl:Class': raise Exception('Unknown syntaxes')
                    if pars_class.group(1).startswith(':'):
                        line = line.replace(pars_class.group(1), '<' + old_new[pars_class.group(1)[1:]] + '>')
                elif parse_subclass and parse_subclass.group(1) in old_new:
                    line = line.replace(parse_subclass.group(1), '<' + old_new[parse_subclass.group(1)] + '>')
                new_file.append(line)

        new_path = path.parent / pathlib.PurePath(path.stem + '_pretty.ttl')
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(''.join(new_file))
        return str(new_path)

    @staticmethod
    def __parser_ttl(path: str) -> dict[str, dict[str, str|list[str]]]:
        parent_children = dict()
        classes = dict()
        with open(path, 'r') as f:
            while line := f.readline():
                pars = re.search(r'(\S+) rdf:type (\S+) ;', line)
                if pars:
                    if pars.group(2) != 'owl:Class': raise Exception('Unknown syntaxes')
                    pars = pars.group(1).split('#')[1][:-1]
                    page = {'title': pars}
                    while new_line := f.readline().strip():
                        pars_parent = re.search(r'rdfs:subClassOf (\S+)', new_line[:-1])
                        if pars_parent:
                            pars_parent = pars_parent.group(1).split('#')
                            if len(pars_parent) == 2:
                                pars_parent = pars_parent[1][:-1]
                            else:
                                raise Exception('Unknown syntaxes')

                            page.update({'parent': pars_parent})
                            if pars_parent not in parent_children:
                                parent_children[pars_parent] = [pars, ]
                            else:
                                parent_children[pars_parent].append(pars)
                        pars_label = re.search(r'rdfs:label "(.+)"@(\S+)', new_line[:-1])
                        if pars_label:
                            page.update({f'label@{pars_label.group(2)}': pars_label.group(1)})
                        if new_line[-1] == '.': break
                    classes[pars] = page
        for parent, children in parent_children.items():
            classes[parent].update({'children': children})
        return classes

    def __call__(self, path, *args, **kwargs):
        namespace = kwargs.get('namespace', None)
        if namespace is None:
            raise AttributeError('Namespace must be specified')

        return self.__parser_ttl(self.__rename_classes(path, namespace))

if __name__ == '__main__':
    TTLParser()('./data/ontology.ttl', namespace='http://www.semanticweb.org/григорий/ontologies/2024/10/untitled-ontology-19')
