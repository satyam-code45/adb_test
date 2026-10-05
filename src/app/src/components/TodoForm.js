import { useState } from 'react';

// Same limit the API enforces
const MAX_LENGTH = 200;

export function TodoForm({ onSubmit }) {
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmed = description.trim();
    if (!trimmed) {
      setError('Please enter a TODO.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(trimmed);
      setDescription('');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="todo">ToDo: </label>
        <input
          id="todo"
          type="text"
          value={description}
          maxLength={MAX_LENGTH}
          onChange={(event) => setDescription(event.target.value)}
          disabled={submitting}
        />
      </div>
      <div style={{ marginTop: '5px' }}>
        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding...' : 'Add ToDo!'}
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
