from unittest import mock

from django.test import SimpleTestCase
from pymongo.errors import ServerSelectionTimeoutError
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from rest.db import client
from .repository import TodoRepository
from .validators import MAX_DESCRIPTION_LENGTH, validate_description
from .views import TodoListView


class FakeTodoRepository:
    def __init__(self, todos=None, error=None):
        self.todos = list(todos or [])
        self.error = error

    def list_all(self):
        if self.error:
            raise self.error
        return self.todos

    def create(self, description):
        todo = {
            'id': str(len(self.todos) + 1),
            'description': description,
            'created_at': '2026-01-01T00:00:00+00:00',
        }
        self.todos.append(todo)
        return todo


class ValidateDescriptionTests(SimpleTestCase):
    def test_returns_stripped_description(self):
        self.assertEqual(validate_description({'description': '  Buy milk '}), 'Buy milk')

    def test_rejects_invalid_input(self):
        cases = [
            {},
            {'description': None},
            {'description': '   '},
            {'description': 42},
            {'description': 'x' * (MAX_DESCRIPTION_LENGTH + 1)},
        ]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                validate_description(data)

    def test_rejects_body_that_is_not_an_object(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_description(['not', 'a', 'dict'])
        self.assertIn('non_field_errors', ctx.exception.detail)


class TodoListViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def call(self, request, repository):
        return TodoListView.as_view(repository=repository)(request)

    def test_get_returns_all_todos(self):
        todos = [{'id': '1', 'description': 'Learn Docker'}]
        response = self.call(self.factory.get('/todos'), FakeTodoRepository(todos))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, todos)

    def test_post_creates_todo(self):
        repository = FakeTodoRepository()
        request = self.factory.post('/todos', {'description': 'Learn React'}, format='json')
        response = self.call(request, repository)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['description'], 'Learn React')
        self.assertEqual(len(repository.todos), 1)

    def test_post_with_invalid_body_returns_400_and_saves_nothing(self):
        repository = FakeTodoRepository()
        request = self.factory.post('/todos', {'description': ''}, format='json')
        response = self.call(request, repository)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'description': ['This field may not be blank.']})
        self.assertEqual(repository.todos, [])

    def test_database_error_returns_503(self):
        repository = FakeTodoRepository(error=ServerSelectionTimeoutError('down'))
        with self.assertLogs('rest.exceptions', level='ERROR'):
            response = self.call(self.factory.get('/todos'), repository)

        self.assertEqual(response.status_code, 503)


class TodoRoutingTests(SimpleTestCase):
    """Goes through the URLconf, so the optional trailing slash is covered."""

    def setUp(self):
        patcher = mock.patch.object(TodoListView, 'repository', FakeTodoRepository())
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_and_post_work_with_and_without_trailing_slash(self):
        for path in ('/todos', '/todos/'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
                response = self.client.post(
                    path, {'description': 'x'}, content_type='application/json'
                )
                self.assertEqual(response.status_code, 201)

    def test_post_rejects_non_json_body(self):
        response = self.client.post('/todos', {'description': 'x'})  # multipart form
        self.assertEqual(response.status_code, 415)


class TodoRepositoryTests(SimpleTestCase):
    """Runs against the real mongo container, in a throwaway database."""

    def setUp(self):
        self.db = client['test_db_tests']
        self.repository = TodoRepository(self.db['todos'])

    def tearDown(self):
        client.drop_database('test_db_tests')

    def test_create_then_list_in_insertion_order(self):
        first = self.repository.create('first')
        second = self.repository.create('second')

        self.assertEqual(self.repository.list_all(), [first, second])

    def test_returned_todo_is_json_friendly(self):
        todo = self.repository.create('Learn Mongo')

        self.assertIsInstance(todo['id'], str)
        self.assertIsInstance(todo['created_at'], str)
        self.assertEqual(set(todo), {'id', 'description', 'created_at'})
