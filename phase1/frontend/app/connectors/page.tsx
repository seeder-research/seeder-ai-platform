'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface Connector {
  id: string;
  provider: string;
  label: string;
  base_url: string;
  is_configured: boolean;
  key_preview: string | null;
  is_seeded: boolean;
  is_active: boolean;
}

export default function ConnectorsPage() {
  const router = useRouter();
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [keyInputs, setKeyInputs] = useState<Record<string, string>>({});
  const [savingId, setSavingId] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  const [newLabel, setNewLabel] = useState('');
  const [newBaseUrl, setNewBaseUrl] = useState('');
  const [newApiKey, setNewApiKey] = useState('');

  function load() {
    apiFetch('/connectors').then(setConnectors);
  }

  useEffect(() => { load(); }, []);

  async function saveKey(id: string) {
    const apiKey = keyInputs[id];
    if (!apiKey) return;
    setSavingId(id);
    try {
      await apiFetch(`/connectors/${id}`, { method: 'PATCH', body: JSON.stringify({ api_key: apiKey }) });
      setKeyInputs((prev) => ({ ...prev, [id]: '' }));
      setMessage('Saved.');
      load();
    } catch (e: any) {
      setMessage(`Failed to save: ${e.message}`);
    } finally {
      setSavingId(null);
    }
  }

  async function createCustom() {
    if (!newLabel.trim() || !newBaseUrl.trim() || !newApiKey.trim()) {
      setMessage('Label, base URL, and API key are all required for a custom connector.');
      return;
    }
    try {
      await apiFetch('/connectors', {
        method: 'POST',
        body: JSON.stringify({ provider: 'custom', label: newLabel, base_url: newBaseUrl, api_key: newApiKey }),
      });
      setNewLabel(''); setNewBaseUrl(''); setNewApiKey('');
      setMessage('Custom connector added.');
      load();
    } catch (e: any) {
      setMessage(`Failed to add: ${e.message}`);
    }
  }

  async function deleteCustom(id: string) {
    if (!confirm('Delete this connector?')) return;
    try {
      await apiFetch(`/connectors/${id}`, { method: 'DELETE' });
      load();
    } catch (e: any) {
      setMessage(`Failed to delete: ${e.message}`);
    }
  }

  const seeded = connectors.filter((c) => c.is_seeded);
  const custom = connectors.filter((c) => !c.is_seeded);

  return (
    <div className="min-h-screen bg-neutral-950 p-6 text-neutral-100">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-medium">Connectors</h1>
          <button onClick={() => router.push('/chat')} className="rounded bg-neutral-800 px-3 py-1 text-sm hover:bg-neutral-700">
            Back to chat
          </button>
        </div>

        {message && <p className="text-sm text-neutral-400">{message}</p>}

        <section className="space-y-3">
          <h2 className="text-sm font-medium text-neutral-400">Default providers</h2>
          {seeded.map((c) => (
            <div key={c.id} className="rounded-lg bg-neutral-900 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{c.label}</p>
                  <p className="text-xs text-neutral-500">{c.base_url}</p>
                </div>
                <span className={`text-xs ${c.is_configured ? 'text-green-400' : 'text-neutral-500'}`}>
                  {c.is_configured ? `Configured (${c.key_preview})` : 'Not configured'}
                </span>
              </div>
              <div className="mt-2 flex gap-2">
                <input
                  type="password"
                  placeholder="API key"
                  value={keyInputs[c.id] || ''}
                  onChange={(e) => setKeyInputs((prev) => ({ ...prev, [c.id]: e.target.value }))}
                  className="flex-1 rounded bg-neutral-800 px-3 py-1.5 text-sm"
                />
                <button
                  onClick={() => saveKey(c.id)}
                  disabled={savingId === c.id || !keyInputs[c.id]}
                  className="rounded bg-blue-600 px-3 py-1.5 text-sm disabled:opacity-50"
                >
                  {savingId === c.id ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          ))}
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-medium text-neutral-400">Custom connectors</h2>
          {custom.map((c) => (
            <div key={c.id} className="rounded-lg bg-neutral-900 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{c.label}</p>
                  <p className="text-xs text-neutral-500">{c.base_url}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs ${c.is_configured ? 'text-green-400' : 'text-neutral-500'}`}>
                    {c.is_configured ? `Configured (${c.key_preview})` : 'Not configured'}
                  </span>
                  <button onClick={() => deleteCustom(c.id)} className="text-xs text-red-400 hover:text-red-300">
                    Delete
                  </button>
                </div>
              </div>
              <div className="mt-2 flex gap-2">
                <input
                  type="password"
                  placeholder="API key"
                  value={keyInputs[c.id] || ''}
                  onChange={(e) => setKeyInputs((prev) => ({ ...prev, [c.id]: e.target.value }))}
                  className="flex-1 rounded bg-neutral-800 px-3 py-1.5 text-sm"
                />
                <button
                  onClick={() => saveKey(c.id)}
                  disabled={savingId === c.id || !keyInputs[c.id]}
                  className="rounded bg-blue-600 px-3 py-1.5 text-sm disabled:opacity-50"
                >
                  {savingId === c.id ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          ))}

          <div className="rounded-lg border border-dashed border-neutral-700 p-4">
            <p className="mb-2 text-sm font-medium">Add custom connector</p>
            <div className="space-y-2">
              <input value={newLabel} onChange={(e) => setNewLabel(e.target.value)} placeholder="Label (e.g. Lab vLLM Server)"
                     className="w-full rounded bg-neutral-800 px-3 py-1.5 text-sm" />
              <input value={newBaseUrl} onChange={(e) => setNewBaseUrl(e.target.value)} placeholder="Base URL"
                     className="w-full rounded bg-neutral-800 px-3 py-1.5 text-sm" />
              <input type="password" value={newApiKey} onChange={(e) => setNewApiKey(e.target.value)} placeholder="API key"
                     className="w-full rounded bg-neutral-800 px-3 py-1.5 text-sm" />
              <button onClick={createCustom} className="rounded bg-blue-600 px-3 py-1.5 text-sm">
                Add
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
