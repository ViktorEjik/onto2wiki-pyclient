from unittest.mock import Mock

from onto2wiki.web_client import Onto2WikiClient

import pytest


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


def test_add_new_page_success(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(json=lambda: {'edit': {'result': 'Success'}})

    test_page = {
        'title': 'Test_Page',
        'text': 'Initial content'
    }

    result = login_client.add_new_page(test_page)

    # Проверка основного запроса
    expected_main_data = {
        'action': 'edit',
        'format': 'json',
        'title': 'Test_Page',
        'text': 'Initial content Данная страница сгенерирована ботом, её необходимо заполнить.',
        'bot': 1,
        'token': 'testcsrftoken',
        'formatversion': '2'
    }
    mock_post.assert_any_call(
        url=login_client.config['URL_API'],
        data=expected_main_data,
        headers=login_client.headers
    )

    assert result is True


def test_add_new_page_with_children(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(json=lambda: {'edit': {'result': 'Success'}})

    test_page = {
        'title': 'Parent_Page',
        'children': ['Child_1', 'Child_2']
    }

    login_client.add_new_page(test_page)

    # Проверка запроса для раздела Children
    expected_children_data = {
        'action': 'edit',
        'format': 'json',
        'title': 'Parent_Page',
        'section': 'new',
        'sectiontitle': 'Childrens',
        'text': '* [[Child 1]]\n* [[Child 2]]\n',
        'bot': 1,
        'token': 'testcsrftoken',
        'formatversion': '2'
    }

    mock_post.assert_any_call(
        url=login_client.config['URL_API'],
        data=expected_children_data,
        headers=login_client.headers
    )


def test_add_new_page_with_parent(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(json=lambda: {'edit': {'result': 'Success'}})

    test_page = {
        'title': 'Child_Page',
        'parent': 'Parent_Page'
    }

    login_client.add_new_page(test_page)

    # Проверка запроса для раздела Parent
    expected_parent_data = {
        'action': 'edit',
        'format': 'json',
        'title': 'Child_Page',
        'section': 'new',
        'sectiontitle': 'Parent',
        'text': '* [[Parent Page]]\n',
        'token': 'testcsrftoken',
        'formatversion': '2'
    }

    mock_post.assert_any_call(
        url=login_client.config['URL_API'],
        data=expected_parent_data,
        headers=login_client.headers
    )


def test_add_new_page_error_handling(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(
        json=lambda: {'error': {'code': 'protectedpage', 'info': 'Page is protected'}},
        status_code=403
    )

    test_page = {'title': 'Protected_Page'}

    result = login_client.add_new_page(test_page)

    assert result is False


def test_dell_page_success(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(json=lambda: {}, status_code=200)

    test_page = {'title': 'Test_Page'}

    login_client.dell_page(test_page)

    expected_data = {
        'action': 'delete',
        'format': 'json',
        'title': 'Test_Page',
        'token': 'testcsrftoken',
        'formatversion': '2'
    }

    mock_post.assert_called_once_with(
        url=login_client.config['URL_API'],
        data=expected_data,
        headers=login_client.headers
    )


def test_empty_page_handling(login_client, mocker):

    mock_post = mocker.patch('requests.Session.post')

    login_client.dell_page({})

    mock_post.assert_not_called()
