const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });

  if (res.status === 401) {
    const refreshRes = await fetch(`${API_BASE}/auth/refresh`, { method: 'POST', credentials: 'same-origin' });
    if (refreshRes.ok) return apiFetch(path, options);
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) throw new Error(await res.text());
  if (res.status === 204) return null;
  return res.json();
}
