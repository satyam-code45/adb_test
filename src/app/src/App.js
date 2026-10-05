import './App.css';
import { TodoForm } from './components/TodoForm';
import { TodoList } from './components/TodoList';
import { useTodos } from './hooks/useTodos';

export function App() {
  const { todos, loading, error, addTodo } = useTodos();

  return (
    <div className="App">
      <div>
        <h1>List of TODOs</h1>
        <TodoList todos={todos} loading={loading} error={error} />
      </div>
      <div>
        <h1>Create a ToDo</h1>
        <TodoForm onSubmit={addTodo} />
      </div>
    </div>
  );
}

export default App;
