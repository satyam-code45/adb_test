import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import { createTodo, fetchTodos } from './api/todos';

jest.mock('./api/todos');

afterEach(() => jest.resetAllMocks());

test('renders todos from the API', async () => {
  fetchTodos.mockResolvedValue([{ id: '1', description: 'Learn Docker' }]);
  render(<App />);

  expect(await screen.findByText('Learn Docker')).toBeInTheDocument();
});

test('creates a todo and refreshes the list', async () => {
  fetchTodos
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce([{ id: '1', description: 'Learn React' }]);
  createTodo.mockResolvedValue({ id: '1', description: 'Learn React' });
  render(<App />);

  expect(await screen.findByText('No TODOs yet.')).toBeInTheDocument();
  userEvent.type(screen.getByLabelText(/todo/i), '  Learn React ');
  userEvent.click(screen.getByRole('button', { name: /add todo/i }));

  expect(await screen.findByText('Learn React')).toBeInTheDocument();
  expect(createTodo).toHaveBeenCalledWith('Learn React');
  expect(fetchTodos).toHaveBeenCalledTimes(2);
  expect(screen.getByLabelText(/todo/i)).toHaveValue('');
});

test('does not submit an empty todo', async () => {
  fetchTodos.mockResolvedValue([]);
  render(<App />);

  await screen.findByText('No TODOs yet.');
  userEvent.click(screen.getByRole('button', { name: /add todo/i }));

  expect(screen.getByRole('alert')).toHaveTextContent('Please enter a TODO.');
  expect(createTodo).not.toHaveBeenCalled();
});

test('shows the API error when creating fails', async () => {
  fetchTodos.mockResolvedValue([]);
  createTodo.mockRejectedValue(new Error('Must be at most 200 characters.'));
  render(<App />);

  await screen.findByText('No TODOs yet.');
  userEvent.type(screen.getByLabelText(/todo/i), 'too long');
  userEvent.click(screen.getByRole('button', { name: /add todo/i }));

  await waitFor(() =>
    expect(screen.getByRole('alert')).toHaveTextContent('Must be at most 200 characters.')
  );
});

test('shows an error when the list cannot be loaded', async () => {
  fetchTodos.mockRejectedValue(new Error('Could not reach the server.'));
  render(<App />);

  expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the server.');
});
