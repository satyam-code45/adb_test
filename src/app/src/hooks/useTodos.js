import { useCallback, useEffect, useState } from 'react';
import { createTodo, fetchTodos } from '../api/todos';

export function useTodos() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadTodos = useCallback(async () => {
    try {
      setTodos(await fetchTodos());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTodos();
  }, [loadTodos]);

  // Errors from create are rethrown so the form can show them
  const addTodo = useCallback(
    async (description) => {
      await createTodo(description);
      await loadTodos();
    },
    [loadTodos]
  );

  return { todos, loading, error, addTodo };
}
