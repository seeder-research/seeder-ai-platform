// No token argument needed — the browser auto-attaches the httpOnly cookie
// on the WebSocket handshake automatically (cookie matching is domain/path
// based, not origin-based, so this works whether or not frontend and backend
// share the same host:port).
export function connectChatSocket(chatId: string, onMessage: (data: any) => void) {
  const fallbackProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const base = process.env.NEXT_PUBLIC_WS_URL || `${fallbackProtocol}://${window.location.host}/ws`;
  const ws = new WebSocket(`${base}/chat/${chatId}`);
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  return ws;
}
