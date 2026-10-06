const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch {
    throw new Error('Could not reach the server.');
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(errorMessage(body) || `Request failed with status ${response.status}.`);
  }
  return body;
}

// DRF errors come back as {detail: "..."} or {field: ["..."]}
function errorMessage(body) {
  if (!body) return null;
  if (body.detail) return body.detail;
  const [first] = Object.values(body);
  return Array.isArray(first) ? first[0] : first;
}

export function fetchTodos() {
  return request('/todos/');
}

export function createTodo(description) {
  return request('/todos/', {
    method: 'POST',
    body: JSON.stringify({ description }),
  });
}
