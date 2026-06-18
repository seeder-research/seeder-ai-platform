'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import { connectChatSocket } from '@/lib/ws';
import { logout } from '@/lib/auth';

interface Message { role: 'user' | 'assistant'; content: string; }

export default function ChatPage() {
  const router = useRouter();
  const [models, setModels] = useState<{ id: string }[]>([]);
  const [connectors, setConnectors] = useState<any[]>([]);
  const [selectedSource, setSelectedSource] = useState('');  // 'local:<id>' or 'connector:<id>'
  const [connectorModelName, setConnectorModelName] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    apiFetch('/models').then(setModels);
    apiFetch('/connectors').then((data) => setConnectors(data.filter((c: any) => c.is_configured)));
  }, []);

  useEffect(() => {
    apiFetch('/chats', { method: 'POST', body: JSON.stringify({ title: 'New Chat' }) }).then((chat) => {
      wsRef.current = connectChatSocket(chat.id, (data) => {
        if (data.type === 'error') {
          setErrorMsg(data.content);
          return;
        }
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (data.type === 'token' && last?.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.content }];
          }
          if (data.type === 'token') return [...prev, { role: 'assistant', content: data.content }];
          return prev;
        });
      });
    });
    return () => wsRef.current?.close();
  }, []);

  function sendMessage() {
    if (!input.trim() || !wsRef.current) return;
    const [kind, id] = selectedSource.split(':');
    if (!kind || !id || (kind === 'connector' && !connectorModelName.trim())) {
      setErrorMsg('Select a model or connector first (and enter a model name if using a connector).');
      return;
    }
    setErrorMsg('');
    setMessages((prev) => [...prev, { role: 'user', content: input }]);
    const payload = kind === 'connector'
      ? { connector_id: id, model_name: connectorModelName, content: input }
      : { model: id, content: input };
    wsRef.current.send(JSON.stringify(payload));
    setInput('');
  }

  return (
    <div className="flex h-screen flex-col bg-neutral-950 text-neutral-100">
      <header className="flex items-center justify-between border-b border-neutral-800 px-4 py-2">
        <div className="flex items-center gap-2">
          <select value={selectedSource} onChange={(e) => setSelectedSource(e.target.value)}
                  className="rounded bg-neutral-800 px-2 py-1 text-sm">
            <option value="">Select a model or connector…</option>
            <optgroup label="Local (Bose01)">
              {models.map((m) => <option key={m.id} value={`local:${m.id}`}>{m.id}</option>)}
            </optgroup>
            <optgroup label="Connectors">
              {connectors.map((c) => <option key={c.id} value={`connector:${c.id}`}>{c.label}</option>)}
            </optgroup>
          </select>
          {selectedSource.startsWith('connector:') && (
            <input value={connectorModelName} onChange={(e) => setConnectorModelName(e.target.value)}
                   placeholder="Model name (e.g. gpt-4o, claude-opus-4-1, gemini-2.5-pro)"
                   className="rounded bg-neutral-800 px-2 py-1 text-sm" />
          )}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => router.push('/connectors')} className="rounded bg-neutral-800 px-3 py-1 text-sm hover:bg-neutral-700">
            Connectors
          </button>
          <button onClick={() => logout()} className="rounded bg-neutral-800 px-3 py-1 text-sm hover:bg-neutral-700">
            Log out
          </button>
        </div>
      </header>

      {errorMsg && (
        <div className="bg-red-950 px-4 py-2 text-sm text-red-300">{errorMsg}</div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <span className={`inline-block rounded-lg px-3 py-2 ${m.role === 'user' ? 'bg-blue-600' : 'bg-neutral-800'}`}>
              {m.content}
            </span>
          </div>
        ))}
      </div>

      <div className="flex border-t border-neutral-800 p-3">
        <input
          value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          className="flex-1 rounded bg-neutral-800 px-3 py-2"
          placeholder="Message..."
        />
        <button onClick={sendMessage} className="ml-2 rounded bg-blue-600 px-4 py-2">Send</button>
      </div>
    </div>
  );
}
