from django.urls import re_path

from .views import TodoListView

urlpatterns = [
    # Optional slash: APPEND_SLASH can't redirect a POST to /todos
    re_path(r'^todos/?$', TodoListView.as_view(), name='todos'),
]
