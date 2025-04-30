from unittest.mock import Mock

from onto2wiki.web_client import Onto2WikiClient

import pytest


@pytest.fixture
def unregistered_client():
    client = Onto2WikiClient()
    client._Onto2WikiClient__config = {
        'URL_API': 'https://wiki.example.org/api.php',
        'LOGIN': 'testuser',
        'PASSWORD': 'testpass'
    }

    return client


def test_login_headers_and_params(unregistered_client, mocker):

    mock_get = mocker.patch('requests.Session.get')
    mock_post = mocker.patch('requests.Session.post')

    mock_get.side_effect = [
        Mock(json=lambda: {'query': {'tokens': {'logintoken': 'test_token'}}}),
        Mock(json=lambda: {'query': {'tokens': {'csrftoken': 'csrf_token'}}})
    ]
    mock_post.return_value = Mock(
        json=lambda: {'login': {'result': 'Success', 'lgusername': 'testuser'}}
    )

    unregistered_client.login()

    assert mock_get.call_count == 2

    first_get_args = mock_get.call_args_list[0]
    assert first_get_args[1]['params'] == {
        'action': 'query',
        'meta': 'tokens',
        'type': 'login|csrf',
        'format': 'json'
    }

    second_get_args = mock_get.call_args_list[1]
    assert second_get_args[1]['params'] == {
        'action': 'query',
        'meta': 'tokens',
        'type': 'login|csrf',
        'format': 'json'
    }

    mock_post.assert_called_once_with(
        'https://wiki.example.org/api.php',
        data={
            'action': 'login',
            'lgname': 'testuser',
            'lgpassword': 'testpass',
            'lgtoken': 'test_token',
            'format': 'json'
        },
        headers=unregistered_client.headers
    )
