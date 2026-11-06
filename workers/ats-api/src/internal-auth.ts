/**
 * HMAC request signing between gate and backend (server-only secrets; never exposed to browser).
 */

const MAX_SKEW_MS = 90_000;

export async function signInternalRequest(
  secret: string,
  method: string,
  path: string,
  bodyText: string,
  timestamp: number,
): Promise<string> {
  const bodyHash = await sha256Hex(bodyText);
  const msg = `${method}\n${path}\n${String(timestamp)}\n${bodyHash}`;
  const sig = await hmacSha256Hex(secret, msg);
  return `${timestamp}.${sig}`;
}

export async function verifyInternalRequest(
  secret: string,
  method: string,
  path: string,
  bodyText: string,
  headerVal: string | null,
): Promise<{ ok: true } | { ok: false; error: string }> {
  if (!headerVal || !headerVal.includes(".")) {
    return { ok: false, error: "missing internal auth" };
  }
  const dot = headerVal.indexOf(".");
  const tsStr = headerVal.slice(0, dot);
  const sigGiven = headerVal.slice(dot + 1);
  const ts = Number(tsStr);
  if (!Number.isFinite(ts)) {
    return { ok: false, error: "invalid timestamp" };
  }
  const now = Date.now();
  if (Math.abs(now - ts) > MAX_SKEW_MS) {
    return { ok: false, error: "stale internal request" };
  }
  const bodyHash = await sha256Hex(bodyText);
  const msg = `${method}\n${path}\n${String(ts)}\n${bodyHash}`;
  const expected = await hmacSha256Hex(secret, msg);
  if (!timingSafeEqualHex(sigGiven, expected)) {
    return { ok: false, error: "invalid internal signature" };
  }
  return { ok: true };
}

async function sha256Hex(text: string): Promise<string> {
  const data = new TextEncoder().encode(text);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return bufferToHex(buf);
}

async function hmacSha256Hex(secret: string, message: string): Promise<string> {
  const keyData = new TextEncoder().encode(secret);
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign(
    "HMAC",
    cryptoKey,
    new TextEncoder().encode(message),
  );
  return bufferToHex(sig);
}

function bufferToHex(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let hex = "";
  for (let i = 0; i < bytes.length; i++) {
    hex += bytes[i]!.toString(16).padStart(2, "0");
  }
  return hex;
}

function timingSafeEqualHex(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}
