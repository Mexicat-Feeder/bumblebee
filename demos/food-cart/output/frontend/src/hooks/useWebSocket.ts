import { useEffect } from 'react';

export function useWebSocket(path: string, onMessage: (data: any) => void) {
  useEffect(() => {
    let socket: WebSocket | null = null;
    let closed = false;
    let retry = 500;

    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      socket = new WebSocket(`${protocol}://${window.location.host}${path}`);
      socket.onmessage = event => onMessage(JSON.parse(event.data));
      socket.onopen = () => { retry = 500; };
      socket.onclose = () => {
        if (!closed) {
          window.setTimeout(connect, retry);
          retry = Math.min(retry * 2, 5000);
        }
      };
    }

    connect();
    return () => { closed = true; socket?.close(); };
  }, [path, onMessage]);
}
