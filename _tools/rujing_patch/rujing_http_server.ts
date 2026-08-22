import { socket } from '@kit.NetworkKit';
import { BusinessError } from '@kit.BasicServicesKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { fileIo } from '@kit.CoreFileKit';
import { application } from '@kit.AbilityKit';
import { importCardPackage } from './ImportService';

const SERVER_TAG = 'rujing.HttpServer';
const LISTEN_PORT = 18999;

interface IncomingRequest {
  method: string;
  path: string;
  body: string;
}

let serverInstance: socket.TCPSocketServer | null = null;
let currentConnection: socket.LocalSocketConnection | null = null;
let lastReceivedText: string = '';
let lastImportResult: string = '';

export function startRujingServer(): void {
  if (serverInstance) {
    hilog.info(0x0000, SERVER_TAG, 'server already started');
    return;
  }
  const tcp = socket.constructTCPSocketServerInstance();
  const addr: socket.LocalAddress = {
    address: '0.0.0.0',
    port: LISTEN_PORT,
    family: 1 // IPv4
  };
  hilog.info(0x0000, SERVER_TAG, 'listen on 0.0.0.0:' + LISTEN_PORT);
  tcp.listen(addr).then(() => {
    hilog.info(0x0000, SERVER_TAG, 'listening on port ' + LISTEN_PORT);
    serverInstance = tcp;
  }).catch((err: BusinessError) => {
    hilog.error(0x0000, SERVER_TAG, 'listen fail: code=' + err.code + ' msg=' + err.message);
  });
  tcp.on('connect', (conn: socket.LocalSocketConnection) => {
    hilog.info(0x0000, SERVER_TAG, 'client connected');
    currentConnection = conn;
    let buffer = '';
    conn.on('message', (data: socket.SocketMessageInfo) => {
      try {
        const chunk = new TextDecoder('utf-8').decode(new Uint8Array(data.message));
        buffer += chunk;
        hilog.info(0x0000, SERVER_TAG, 'recv chunk ' + chunk.length + ' bytes, buffer=' + buffer.length);
        // 检查是否收到完整 HTTP request（双 CRLF 标记 headers 结束）
        const headerEnd = buffer.indexOf('\r\n\r\n');
        if (headerEnd < 0) return;
        const headerPart = buffer.substring(0, headerEnd);
        const bodyStart = headerEnd + 4;
        // 解析 Content-Length
        let contentLength = 0;
        const m = headerPart.match(/Content-Length:\s*(\d+)/i);
        if (m) contentLength = parseInt(m[1]);
        if (buffer.length < bodyStart + contentLength) {
          hilog.info(0x0000, SERVER_TAG, 'waiting for body, have ' + (buffer.length - bodyStart) + ' of ' + contentLength);
          return;
        }
        const body = buffer.substring(bodyStart, bodyStart + contentLength);
        // 解析第一行
        const firstLine = headerPart.split('\r\n')[0];
        const parts = firstLine.split(' ');
        const method = parts[0] ?? 'GET';
        const reqPath = parts[1] ?? '/';
        hilog.info(0x0000, SERVER_TAG, 'request: ' + method + ' ' + reqPath + ' body=' + body.length);
        handleRequest(conn, method, reqPath, body);
      } catch (e) {
        const err = e as BusinessError;
        hilog.error(0x0000, SERVER_TAG, 'message handler fail: ' + err.message);
      }
    });
    conn.on('close', () => {
      hilog.info(0x0000, SERVER_TAG, 'client disconnected');
      currentConnection = null;
    });
    conn.on('error', (err: BusinessError) => {
      hilog.error(0x0000, SERVER_TAG, 'conn error: ' + err.message);
    });
  });
  tcp.on('error', (err: BusinessError) => {
    hilog.error(0x0000, SERVER_TAG, 'server error: ' + err.message);
  });
}

async function handleRequest(conn: socket.LocalSocketConnection, method: string, path: string, body: string): Promise<void> {
  // 健康检查
  if (method === 'GET' && (path === '/' || path === '/health')) {
    sendResponse(conn, 200, 'OK', '{"status":"rujing ready","cards_loaded":0}');
    return;
  }
  // 接收卡片 JSON
  if (method === 'POST' && (path === '/upload' || path === '/import')) {
    hilog.info(0x0000, SERVER_TAG, 'POST ' + path + ' body=' + body.length);
    lastReceivedText = body;
    const filesDir = application.getApplicationContext().filesDir;
    const dest = filesDir + '/rujing_cards.json';
    try {
      const f = fileIo.openSync(dest, fileIo.OpenMode.CREATE | fileIo.OpenMode.WRITE_ONLY | fileIo.OpenMode.TRUNC);
      const enc = new TextEncoder();
      const data = enc.encodeInto(body);
      fileIo.writeSync(f.fd, data.buffer as ArrayBuffer);
      fileIo.closeSync(f);
      hilog.info(0x0000, SERVER_TAG, 'cached to ' + dest);
      const result = await importCardPackage(body);
      lastImportResult = 'OK: ' + result.cards + ' cards / ' + result.chains + ' chains';
      hilog.info(0x0000, SERVER_TAG, 'import OK: ' + result.cards + ' cards');
      sendResponse(conn, 200, 'OK', JSON.stringify({ status: 'imported', cards: result.cards, chains: result.chains }));
    } catch (e) {
      const err = e as BusinessError;
      lastImportResult = 'FAIL: ' + err.message;
      hilog.error(0x0000, SERVER_TAG, 'import fail: ' + err.message);
      sendResponse(conn, 500, 'Internal Server Error', JSON.stringify({ status: 'failed', error: err.message }));
    }
    return;
  }
  sendResponse(conn, 404, 'Not Found', '{"error":"unknown endpoint"}');
}

function sendResponse(conn: socket.LocalSocketConnection, code: number, status: string, body: string): void {
  const reason = code === 200 ? 'OK' : (code === 500 ? 'Internal Server Error' : 'Not Found');
  const resp =
    'HTTP/1.1 ' + code + ' ' + reason + '\r\n' +
    'Content-Type: application/json; charset=utf-8\r\n' +
    'Content-Length: ' + Buffer.byteLength(body, 'utf-8') + '\r\n' +
    'Access-Control-Allow-Origin: *\r\n' +
    'Connection: close\r\n' +
    '\r\n' +
    body;
  const enc = new TextEncoder();
  const data = enc.encodeInto(resp);
  conn.send({ data: data.buffer as ArrayBuffer }).then(() => {
    hilog.info(0x0000, SERVER_TAG, 'response sent ' + code);
    setTimeout(() => {
      try { conn.close(); } catch (_) {}
    }, 200);
  }).catch((err: BusinessError) => {
    hilog.error(0x0000, SERVER_TAG, 'send fail: ' + err.message);
  });
}

export function getServerStatus(): string {
  if (!serverInstance) return 'server not started';
  return 'listening on 0.0.0.0:' + LISTEN_PORT + (lastImportResult ? ' | last: ' + lastImportResult : ' | waiting...');
}

export function stopRujingServer(): void {
  if (currentConnection) {
    try { currentConnection.close(); } catch (_) {}
    currentConnection = null;
  }
  if (serverInstance) {
    try { serverInstance.close(); } catch (_) {}
    serverInstance = null;
  }
}
