from unittest.mock import Mock

from onto2wiki.web_client import Onto2WikiClient

import pytest

import requests


@pytest.fixture
def login_client():
    client = Onto2WikiClient()
    client._Onto2WikiClient__config = {
        'URL_API': 'https://wiki.example.org/api.php',
        'LOGIN': 'testuser',
        'PASSWORD': 'testpass',
        'csrftoken': 'testcsrftoken',
    }

    return client


def test_add_hierarchy_page_success(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(
        json=lambda: {'edit': {'result': 'Success'}},
        status_code=200
    )

    # Тестовые данные
    test_pages = {
        'RootPage': {'children': ['ChildPage']},
        'ChildPage': {'parent': 'RootPage'}
    }
    test_roots = ['RootPage']

    login_client.add_hierarchy_page('.Hierarchy', test_pages, test_roots)

    expected_data = {
        'action': 'edit',
        'format': 'json',
        'title': 'RootPage.Hierarchy',
        'text': 'Данная страница сгенерирована ботом, её необходимо заполнить.\n* [[RootPage]]\n** [[ChildPage]]\n',
        'bot': 1,
        'token': login_client.config['csrftoken'],
        'formatversion': '2'
    }

    mock_post.assert_called_once_with(
        url=login_client.config['URL_API'],
        data=expected_data,
        headers=login_client.headers
    )


def test_multiple_roots_processing(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(json=lambda: {'edit': {'result': 'Success'}})

    test_data = {
        'pages': {
            'Root1': {'children': ['Child1']},
            'Child1': {'parent': 'Root1'},
            'Root2': {'children': ['Child2']},
            'Child2': {'parent': 'Root2'},
        },
        'roots': ['Root1', 'Root2']
    }

    login_client.add_hierarchy_page('.Hierarchy', test_data['pages'], test_data['roots'])

    assert mock_post.call_count == 2
    called_titles = {call[1]['data']['title'] for call in mock_post.call_args_list}
    assert called_titles == {'Root1.Hierarchy', 'Root2.Hierarchy'}


@pytest.mark.parametrize('input_title, expected', [
    ('Test_Page', 'Test Page.Hierarchy'),
    ('Another_Example', 'Another Example.Hierarchy'),
    ('NoSpacesHere', 'NoSpacesHere.Hierarchy')
])
def test_title_generation_add(login_client, mocker, input_title, expected):

    mocker.patch('requests.Session.post')

    login_client.add_hierarchy_page('.Hierarchy', {input_title: {}}, [input_title])

    _, kwargs = requests.Session.post.call_args
    assert kwargs['data']['title'] == expected


def test_delete_hierarchy_page_success(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(json=lambda: {}, status_code=200)

    test_roots = ['RootPage', 'AnotherRoot']
    login_client.delete_hierarchy_page('.Hierarchy', test_roots)

    assert mock_post.call_count == 2
    expected_calls = [
        mocker.call(
            url=login_client.config['URL_API'],
            data={
                'action': 'delete',
                'format': 'json',
                'title': 'RootPage.Hierarchy',
                'bot': 1,
                'token': 'testcsrftoken',
                'formatversion': '2'
            },
            headers=login_client.headers
        ),
        mocker.call(
            url=login_client.config['URL_API'],
            data={
                'action': 'delete',
                'format': 'json',
                'title': 'AnotherRoot.Hierarchy',
                'bot': 1,
                'token': 'testcsrftoken',
                'formatversion': '2'
            },
            headers=login_client.headers
        )
    ]
    mock_post.assert_has_calls(expected_calls, any_order=True)


def test_delete_hierarchy_page_error(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(
        json=lambda: {'error': {'code': 'missingtitle', 'info': 'Page does not exist'}},
        status_code=404
    )

    login_client.delete_hierarchy_page('.Hierarchy', ['NonExistingPage'])


@pytest.mark.parametrize('input_title, postfix, expected', [
    ('Test_Page', '.Hierarchy', 'Test Page.Hierarchy'),
    ('Snake_Case_Example', '_test', 'Snake Case Example_test'),
    ('NoSpaces', '', 'NoSpaces')
])
def test_title_generation_delete(login_client, mocker, input_title, postfix, expected):

    mock_post = mocker.patch('requests.Session.post')

    login_client.delete_hierarchy_page(postfix, [input_title])

    _, kwargs = mock_post.call_args
    assert kwargs['data']['title'] == expected


def test_empty_roots(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')

    login_client.delete_hierarchy_page('.Hierarchy', [])

    mock_post.assert_not_called()
