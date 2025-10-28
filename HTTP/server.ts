import * as net from "net";

// ===== Types =====
type TCPConn = {
  socket: net.Socket;
};

type DynBuf = {
  data: Buffer;
  length: number;
};

type HTTPReq = {
  method: string;
  uri: Buffer;
  version: string;
  headers: Buffer[];
};

type HTTPRes = {
  code: number;
  headers: Buffer[];
  body: BodyReader;
};

type BodyReader = {
  length: number;
  read: () => Promise<Buffer>;
};

// ===== Constants =====
const kMaxHeaderLen = 1024 * 8; // 8 KB

// ===== Error Class =====
class HTTPError extends Error {
  code: number;
  constructor(code: number, message: string) {
    super(message);
    this.code = code;
  }
}

// ===== Buffer Utilities =====
function bufPush(buf: DynBuf, data: Buffer): void {
  const newLen = buf.length + data.length;
  if (buf.data.length < newLen) {
    let cap = Math.max(buf.data.length, 32);
    while (cap < newLen) {
      cap *= 2;
    }
    const grown = Buffer.alloc(cap);
    buf.data.copy(grown, 0, 0);
    buf.data = grown;
  }
  data.copy(buf.data, buf.length, 0);
  buf.length = newLen;
}

function bufPop(buf: DynBuf, len: number): void {
  buf.data.copyWithin(0, len, buf.length);
  buf.length -= len;
}

// ===== Socket Reading =====
async function soRead(conn: TCPConn): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const onData = (chunk: Buffer) => {
      cleanup();
      resolve(chunk);
    };
    const onEnd = () => {
      cleanup();
      resolve(Buffer.alloc(0));
    };
    const onError = (err: Error) => {
      cleanup();
      reject(err);
    };
    const cleanup = () => {
      conn.socket.off("data", onData);
      conn.socket.off("end", onEnd);
      conn.socket.off("error", onError);
    };
    conn.socket.once("data", onData);
    conn.socket.once("end", onEnd);
    conn.socket.once("error", onError);
  });
}

// ===== HTTP Parsing =====
function splitLines(data: Buffer): Buffer[] {
  const lines: Buffer[] = [];
  let start = 0;

  for (let i = 0; i < data.length - 1; i++) {
    if (data[i] === 13 && data[i + 1] === 10) {
      lines.push(data.subarray(start, i));
      start = i + 2;
      i++;
    }
  }

  if (start < data.length) {
    lines.push(data.subarray(start));
  }

  return lines;
}

function parseRequestLine(line: Buffer): {
  method: string;
  uri: Buffer;
  version: string;
} {
  const parts: Buffer[] = [];
  let start = 0;

  for (let i = 0; i < line.length; i++) {
    if (line[i] === 32) {
      if (i > start) {
        parts.push(line.subarray(start, i));
      }
      start = i + 1;
    }
  }
  if (start < line.length) {
    parts.push(line.subarray(start));
  }

  if (parts.length !== 3) {
    throw new HTTPError(400, "bad request line");
  }

  const method = parts[0].toString("latin1");
  const uri = parts[1];
  const version = parts[2].toString("latin1");

  const validMethods = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "PATCH",
  ];
  if (!validMethods.includes(method)) {
    throw new HTTPError(405, "method not allowed");
  }

  if (version !== "HTTP/1.1" && version !== "HTTP/1.0") {
    throw new HTTPError(505, "HTTP version not supported");
  }

  return { method, uri, version };
}

function validateHeader(header: Buffer): void {
  const colonIdx = header.indexOf(58);

  if (colonIdx <= 0) {
    throw new HTTPError(400, "bad header format");
  }

  const name = header.subarray(0, colonIdx);

  for (let i = 0; i < name.length; i++) {
    const c = name[i];
    const isValid =
      (c >= 65 && c <= 90) ||
      (c >= 97 && c <= 122) ||
      (c >= 48 && c <= 57) ||
      c === 45;

    if (!isValid) {
      throw new HTTPError(400, "invalid header name");
    }
  }

  if (name.length === 0) {
    throw new HTTPError(400, "empty header name");
  }
}

function parseHTTPReq(data: Buffer): HTTPReq {
  const lines = splitLines(data);

  if (lines.length < 2) {
    throw new HTTPError(400, "incomplete request");
  }

  const { method, uri, version } = parseRequestLine(lines[0]);

  const headers: Buffer[] = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];

    if (line.length === 0) {
      break;
    }

    validateHeader(line);
    headers.push(line);
  }

  return { method, uri, version, headers };
}

function cutMessage(buf: DynBuf): null | HTTPReq {
  const idx = buf.data.subarray(0, buf.length).indexOf("\r\n\r\n");

  if (idx < 0) {
    if (buf.length >= kMaxHeaderLen) {
      throw new HTTPError(413, "header is too large");
    }
    return null;
  }

  const msg = parseHTTPReq(buf.data.subarray(0, idx + 4));
  bufPop(buf, idx + 4);
  return msg;
}

// ===== Header Utilities =====
function fieldGet(headers: Buffer[], key: string): Buffer | null {
  const keyLower = key.toLowerCase();
  for (const header of headers) {
    const colonIdx = header.indexOf(58);
    if (colonIdx > 0) {
      const name = header
        .subarray(0, colonIdx)
        .toString("latin1")
        .toLowerCase()
        .trim();
      if (name === keyLower) {
        // Trim manually: skip leading/trailing whitespace
        let start = colonIdx + 1;
        let end = header.length;
        while (start < end && (header[start] === 32 || header[start] === 9))
          start++;
        while (end > start && (header[end - 1] === 32 || header[end - 1] === 9))
          end--;
        return header.subarray(start, end);
      }
    }
  }
  return null;
}

function parseDec(s: string): number {
  return parseInt(s, 10);
}

// ===== Body Reader =====
function readerFromConnLength(
  conn: TCPConn,
  buf: DynBuf,
  remain: number,
): BodyReader {
  return {
    length: remain,
    read: async (): Promise<Buffer> => {
      if (remain === 0) {
        return Buffer.alloc(0);
      }
      if (buf.length === 0) {
        const data = await soRead(conn);
        bufPush(buf, data);
        if (data.length === 0) {
          throw new HTTPError(400, "Unexpected EOF from HTTP body");
        }
      }
      const consume = Math.min(buf.length, remain);
      remain -= consume;
      const body = Buffer.from(buf.data.subarray(0, consume));
      buf.data.copyWithin(0, consume, buf.length);
      buf.length -= consume;
      return body;
    },
  };
}

function readerFromReq(conn: TCPConn, buf: DynBuf, req: HTTPReq): BodyReader {
  let bodyLen = -1;
  const contentLen = fieldGet(req.headers, "Content-Length");
  if (contentLen) {
    bodyLen = parseDec(contentLen.toString("latin1"));
    if (isNaN(bodyLen)) {
      throw new HTTPError(400, "bad Content-Length");
    }
  }

  const bodyAllowed = !(req.method === "GET" || req.method === "HEAD");
  const chunked =
    fieldGet(req.headers, "Transfer-Encoding")?.equals(
      Buffer.from("chunked"),
    ) || false;

  if (!bodyAllowed && (bodyLen > 0 || chunked)) {
    throw new HTTPError(400, "HTTP body not allowed");
  }
  if (!bodyAllowed) {
    bodyLen = 0;
  }

  if (bodyLen >= 0) {
    return readerFromConnLength(conn, buf, bodyLen);
  } else if (chunked) {
    throw new HTTPError(501, "TODO: chunked encoding");
  } else {
    throw new HTTPError(501, "TODO: read until EOF");
  }
}

// ===== Response Writing =====
async function writeHTTPResp(conn: TCPConn, resp: HTTPRes): Promise<void> {
  if (resp.body.length < 0) {
    throw new Error("chunked encoding is not supported");
  }

  const statusMessages: { [key: number]: string } = {
    200: "OK",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Payload Too Large",
    500: "Internal Server Error",
    501: "Not Implemented",
    505: "HTTP Version Not Supported",
  };

  const statusText = statusMessages[resp.code] || "Unknown";
  const statusLine = `HTTP/1.1 ${resp.code} ${statusText}\r\n`;

  conn.socket.write(statusLine);

  for (const header of resp.headers) {
    conn.socket.write(header);
    conn.socket.write("\r\n");
  }
  conn.socket.write("\r\n");

  while (true) {
    const chunk = await resp.body.read();
    if (chunk.length === 0) {
      break;
    }
    conn.socket.write(chunk);
  }
}

// ===== Request Handler =====
async function handleReq(req: HTTPReq, body: BodyReader): Promise<HTTPRes> {
  const uri = req.uri.toString("latin1");
  console.log(`Request: ${req.method} ${uri}`);

  let bodyData = Buffer.alloc(0);
  while (true) {
    const chunk = await body.read();
    if (chunk.length === 0) break;
    bodyData = Buffer.concat([bodyData, chunk]);
  }

  if (uri === "/echo") {
    return {
      code: 200,
      headers: [
        Buffer.from("Content-Type: text/plain"),
        Buffer.from(`Content-Length: ${bodyData.length}`),
      ],
      body: {
        length: bodyData.length,
        read: async () => {
          const result = bodyData;
          bodyData = Buffer.alloc(0);
          return result;
        },
      },
    };
  }

  const responseText = `Hello from HTTP server!\nYou requested: ${uri}\n`;
  const responseBuffer = Buffer.from(responseText);

  return {
    code: 200,
    headers: [
      Buffer.from("Content-Type: text/plain"),
      Buffer.from(`Content-Length: ${responseBuffer.length}`),
    ],
    body: {
      length: responseBuffer.length,
      read: async () => {
        const result = responseBuffer;
        return result;
      },
    },
  };
}

// ===== Server Client Handler =====
async function serverClient(conn: TCPConn): Promise<void> {
  const buf: DynBuf = { data: Buffer.alloc(0), length: 0 };

  try {
    while (true) {
      const msg: null | HTTPReq = cutMessage(buf);
      if (!msg) {
        const data = await soRead(conn);
        bufPush(buf, data);
        if (data.length === 0) {
          console.log("Client disconnected");
          break;
        }
        continue;
      }

      const reqBody: BodyReader = readerFromReq(conn, buf, msg);
      const res: HTTPRes = await handleReq(msg, reqBody);
      await writeHTTPResp(conn, res);

      if (
        fieldGet(msg.headers, "Connection")
          ?.toString("latin1")
          .toLowerCase() === "close"
      ) {
        break;
      }

      const contentLen = fieldGet(msg.headers, "Content-Length");
      if (!contentLen && msg.method !== "GET" && msg.method !== "HEAD") {
        break;
      }
    }
  } catch (err) {
    if (err instanceof HTTPError) {
      console.error(`HTTP Error ${err.code}: ${err.message}`);
      const errorMsg = Buffer.from(err.message);
      const errorResp: HTTPRes = {
        code: err.code,
        headers: [
          Buffer.from("Content-Type: text/plain"),
          Buffer.from(`Content-Length: ${errorMsg.length}`),
        ],
        body: {
          length: errorMsg.length,
          read: async () => errorMsg,
        },
      };
      try {
        await writeHTTPResp(conn, errorResp);
      } catch (writeErr) {
        console.error("Failed to write error response:", writeErr);
      }
    } else {
      console.error("Unexpected error:", err);
    }
  } finally {
    conn.socket.end();
  }
}

// ===== Main Server =====
function startServer(port: number): void {
  const server = net.createServer((socket) => {
    console.log("New client connected");
    const conn: TCPConn = { socket };
    serverClient(conn).catch((err) => {
      console.error("Error handling client:", err);
    });
  });

  server.listen(port, () => {
    console.log(`HTTP server listening on port ${port}`);
    console.log(`Try: curl http://localhost:${port}/`);
    console.log(
      `Try: curl -X POST -d "test data" http://localhost:${port}/echo`,
    );
  });
}

// Start the server
startServer(8080);

function foo(blaz: {
  oddly: "long" | "type";
  but: "hey" | "this" | "is" | number;
}) {}

function new_fn(bar: number) {}
