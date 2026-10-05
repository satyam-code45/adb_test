from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest.db import db
from .repository import TodoRepository
from .validators import validate_description


class TodoListView(APIView):
    repository = TodoRepository(db['todos'])

    def get(self, request):
        return Response(self.repository.list_all(), status=status.HTTP_200_OK)

    def post(self, request):
        description = validate_description(request.data)
        todo = self.repository.create(description)
        return Response(todo, status=status.HTTP_201_CREATED)
