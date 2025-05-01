def find_roots(graph):
    """Identify root elements in a hierarchical graph structure.

    Root elements are defined as nodes with no parent (parent attribute is None
    or missing). Useful for finding top-level elements in tree-like data structures.

    Args:
    - graph (dict): A dictionary representing the graph where:
        - Keys: Element identifiers (str)
        - Values: Dictionaries containing element data with optional 'parent' key

    Returns:
    - list: Element identifiers of root nodes (elements with no parent)
    """
    roots = []
    for elem in graph:
        if graph[elem].get('parent', None) is None:
            roots.append(elem)
    return roots


__all__ = ['find_roots']
