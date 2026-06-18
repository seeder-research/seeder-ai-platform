export async function login(username: string, password: string) {
  const formData = new URLSearchParams({ username, password });
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/auth/login`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  });
  if (!res.ok) throw new Error('Invalid credentials');
  return res.json();
}

export async function logout() {
  await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/auth/logout`, {
    method: 'POST',
    credentials: 'same-origin',
  });
  window.location.href = '/login';
}
