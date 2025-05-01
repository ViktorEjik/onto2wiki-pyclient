from pathlib import Path
from doit.tools import CmdAction

def task_install_deps():
    return {
        "actions": [CmdAction("pipenv --python 3.13; pipenv install --all-dev") ],
        "verbosity": 2,
    }

def task_test():
    return {
        "actions": [CmdAction("pytest -v")],
        "file_dep": [*Path("tests").glob("*.py")],
        "verbosity": 2,
    }

def task_build():
    return {
        "actions": [CmdAction("python -m build --wheel")],
        "task_dep": ["test"],
        "targets": ["dist/onto2wiki-*.whl"],
        "verbosity": 2,
    }

def task_doc():
    return {
        'actions': [CmdAction('make -C docs html')],
        'file_dep': [*Path("docs/source").glob("index.rst"), *Path("docs/source").glob("conf.py")],
        'targets': ['docs/build/html/index.html'],
        "verbosity": 2,
    }

def task_rm_generic():
    return {
        "actions": ["rm -rf build/* dist/* onto2wiki.egg-info/* docs/build/*"],
        "verbosity": 2,
    }