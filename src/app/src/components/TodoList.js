export function TodoList({ todos, loading, error }) {
  if (loading) return <p>Loading...</p>;
  if (error) return <p role="alert">{error}</p>;
  if (todos.length === 0) return <p>No TODOs yet.</p>;

  return (
    <ul>
      {todos.map((todo) => (
        <li key={todo.id}>{todo.description}</li>
      ))}
    </ul>
  );
}
