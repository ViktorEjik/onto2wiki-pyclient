import pytest
from unittest.mock import Mock
from onto2wiki.web_client import Onto2WikiClient
import requests


@pytest.fixture
def login_client():
    client = Onto2WikiClient()
    client._Onto2WikiClient__config = {
        'URL_API': 'https://wiki.example.org/api.php',
        'LOGIN': 'testuser',
        'PASSWORD': 'testpass',
        "csrftoken": 'testcsrftoken',
    }

    return client


def test_modify_main_page_success(login_client, mocker):
    """Проверка успешного обновления главной страницы"""
    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(
        json=lambda: {"parse": {"sections": [{"line": "Existing Section"}]}},
        status_code=200
    )

    test_roots = ["New_Section"]
    login_client.modify_main_page("Main_Page", test_roots, ".Hierarchy")

    # Проверяем добавление нового раздела
    expected_data = {
        'action': 'edit',
        'format': 'json',
        'title': 'Main_Page',
        'section': 'new',
        'text': '== [[New Section.Hierarchy]] ==',
        'bot': 1,
        'token': 'testcsrftoken',
        'formatversion': '2'
    }

    mock_post.assert_any_call(
        url=login_client.config['URL_API'],
        data={
            'action': 'parse',
            'format': 'json',
            'page': 'Main_Page',
            'formatversion': '2'
        },
        headers=login_client.headers
    )

    mock_post.assert_called_with(
        url=login_client.config['URL_API'],
        data=expected_data,
        headers=login_client.headers
    )


def test_modify_existing_section(login_client, mocker):
    """Проверка пропуска существующих разделов"""
    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(
        json=lambda: {"parse": {"sections": [{"line": "Existing Section.Hierarchy"}]}},
        status_code=200
    )

    login_client.modify_main_page("Main_Page", ["Existing_Section"], ".Hierarchy")
    mock_post.assert_called_once_with(
        url=login_client.config['URL_API'],
        data= {
            'action': 'parse',
            'format': 'json',
            'page': 'Main_Page',
            'formatversion': '2'
        },
        headers=login_client.headers
    )


def test_modify_main_page_error_handling(login_client, mocker, caplog):
    """Проверка обработки ошибок парсинга"""
    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(
        json=lambda: {"error": {"code": "missingtitle", "info": "Page not found"}},
        status_code=404
    )

    with pytest.raises(Exception):
        login_client.modify_main_page("Invalid_Page", ["Test"], ".Hierarchy")


@pytest.mark.parametrize("input_root, postfix, expected", [
    ("Test_Page", ".Hierarchy", "== [[Test Page.Hierarchy]] =="),
    ("Another_Root", "_suffix", "== [[Another Root_suffix]] =="),
    ("NoPostfix", "", "== [[NoPostfix]] ==")
])
def test_section_generation(login_client, mocker, input_root, postfix, expected):
    """Параметризованный тест генерации разделов"""
    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(json=lambda: {"parse": {"sections": []}})

    login_client.modify_main_page("Main_Page", [input_root], postfix)

    assert mock_post.call_args[1]['data']['text'] == expected


def test_multiple_sections_handling(login_client, mocker):
    """Проверка обработки нескольких разделов"""
    mock_post = mocker.patch('requests.Session.post')
    mock_post.return_value = Mock(
        json=lambda: {"parse": {"sections": [
            {"line": "First Section.Hierarchy"},
            {"line": "First Section.Hierarchy"}
        ]}},
        status_code=200
    )

    with pytest.raises(Exception) as excinfo:
        login_client.modify_main_page("Main_Page", ["First_Section"], ".Hierarchy")
    assert "Find more then 1 section named" in str(excinfo.value)


def test_empty_roots_handling(login_client, mocker):
    """Проверка обработки пустого списка корней"""
    mock_post = mocker.patch('requests.Session.post')

    login_client.modify_main_page("Main_Page", [], ".Hierarchy")

    mock_post.assert_called_once_with(
        url=login_client.config['URL_API'],
        data={
            'action': 'parse',
            'format': 'json',
            'page': 'Main_Page',
            'formatversion': '2'
        },
        headers=login_client.headers
    )
