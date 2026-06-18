'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/auth';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
      router.push('/chat');
    } catch {
      setError('Invalid username or password');
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950">
      <form onSubmit={handleSubmit} className="w-80 space-y-4 rounded-lg bg-neutral-900 p-8">
        <h1 className="text-lg font-medium text-neutral-100">Sign in</h1>
        <input
          value={username} onChange={(e) => setUsername(e.target.value)}
          placeholder="Username" autoComplete="username"
          className="w-full rounded border border-neutral-700 bg-neutral-800 px-3 py-2 text-neutral-100"
        />
        <input
          type="password" value={password} onChange={(e) => setPassword(e.target.value)}
          placeholder="Password" autoComplete="current-password"
          className="w-full rounded border border-neutral-700 bg-neutral-800 px-3 py-2 text-neutral-100"
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button type="submit" className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700">
          Sign in
        </button>
      </form>
    </div>
  );
}
