def find_roots(graph):
    roots = []
    for elem in graph:
        if graph[elem].get('parent', None) is None:
            roots.append(elem)
    return roots