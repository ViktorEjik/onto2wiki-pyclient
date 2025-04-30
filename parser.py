"""
Ontology parser module for Turtle (TTL) format files.

Provides functionality for parsing and normalizing ontology files with:
- Namespace management
- Class hierarchy generation
- Syntax normalization
- Cross-referencing between classes

Key Components:
1. BaseParser: Abstract base class for parser implementations
2. TTLParser: Concrete implementation for Turtle format processing

Features:
- Automatic namespace injection for class URIs
- Parent-child relationship detection
- Multi-language label support
- Syntax validation and normalization
- Output generation of modified TTL files

Typical Workflow:
1. Normalize class URIs with specified namespace
2. Generate modified TTL file with full URIs
3. Parse normalized file into hierarchical structure
4. Build parent-child relationships map

Dependencies:
- pathlib: Path handling
- re: Regular expression matching

File Operations:
- Creates *_pretty.ttl files with normalized syntax
- Maintains original file encoding (UTF-8 assumed)

Data Structures:
- Returns nested dictionaries with format:
    {
        'ClassName': {
            'title': str,
            'parent': Optional[str],
            'children': Optional[List[str]],
            'label@{lang}': str
        }
    }
"""
import pathlib
import re


class BaseParser:
    """Base class for ontology parser implementations."""

    def __init__(self):
        """Initialize base parser instance."""
        pass

    def __call__(self, path, **kwargs):
        """Parse ontology file (to be implemented by subclasses).

        Args:
            path: Path to ontology file
            **kwargs: Implementation-specific arguments

        Raises:
            NotImplementedError: Always raises for base class
        """
        raise NotImplementedError('Subclasses must implement __call__')

    def __str__(self):
        """Return string representation of parser class."""
        return self.__class__.__name__


class TTLParser(BaseParser):
    """Turtle format ontology parser with namespace normalization."""

    def __init__(self):
        """Initialize TTL parser instance."""
        super().__init__()

    @staticmethod
    def __rename_classes(path: str, namespace: str) -> str:
        """Normalize class names and update ontology file.

        Args:
            path: Path to original ontology file
            namespace: Namespace URI for class normalization

        Returns:
            str: Path to generated normalized ontology file

        Raises:
            FileNotFoundError: If input path doesn't exist or isn't a file
            Exception: For unsupported syntax patterns
        """
        old_new = {}
        classes = []
        new_file = []
        path = pathlib.Path(path)
        if not path.exists():
            raise FileNotFoundError('Path does not exist')
        elif not path.is_file():
            raise FileNotFoundError('Path is not a file')

        with open(path, 'r') as f:
            while line := f.readline():
                pars = re.search(r'(\S+) rdf:type (\S+) ;', line)
                if pars:
                    if pars.group(2) != 'owl:Class':
                        raise Exception('Unknown syntaxes')
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
                    if pars_class.group(2) != 'owl:Class':
                        raise Exception('Unknown syntaxes')
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
    def __parser_ttl(path: str) -> dict[str, dict[str, str | list[str]]]:
        """Parse normalized TTL file into hierarchical structure.

        Args:
            path: Path to normalized ontology file

        Returns:
            dict: Hierarchical structure of ontology classes with:
                - Keys: Class names
                - Values: Dictionaries containing:
                    - title: Class name
                    - parent: Parent class name (optional)
                    - children: List of child classes (optional)
                    - label@{lang}: Localized labels (optional)

        Raises:
            Exception: For unsupported syntax patterns
        """
        parent_children = {}
        classes = {}
        with open(path, 'r') as f:
            while line := f.readline():
                pars = re.search(r'(\S+) rdf:type (\S+) ;', line)
                if pars:
                    if pars.group(2) != 'owl:Class':
                        raise Exception('Unknown syntaxes')
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
                        if new_line[-1] == '.':
                            break
                    classes[pars] = page
        for parent, children in parent_children.items():
            classes[parent].update({'children': children})
        return classes

    def __call__(self, path, **kwargs):
        """Execute full parsing workflow.

        Args:
            path: Path to original ontology file
            **kwargs: Must contain 'namespace' argument

        Returns:
            dict: Parsed hierarchical structure

        Raises:
            AttributeError: If namespace not provided
        """
        namespace = kwargs.get('namespace', None)
        if namespace is None:
            raise AttributeError('Namespace must be specified')

        return self.__parser_ttl(self.__rename_classes(path, namespace))
