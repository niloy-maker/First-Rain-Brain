const COOKIE_NAME = "fr_auth";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

function readCookie(request, name) {
  const header = request.headers.get("Cookie") || "";
  for (const part of header.split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return decodeURIComponent(v.join("="));
  }
  return null;
}

async function serveAsset(request, env, setCookie) {
  const upstream = await env.ASSETS.fetch(request);
  const ct = upstream.headers.get("content-type") || "";
  const headers = new Headers(upstream.headers);
  if (ct.includes("text/html") || ct.includes("application/json")) {
    headers.set("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
    headers.set("Pragma", "no-cache");
    headers.set("Expires", "0");
  }
  if (setCookie) {
    headers.append(
      "Set-Cookie",
      `${COOKIE_NAME}=${encodeURIComponent(setCookie)}; Path=/; Max-Age=${COOKIE_MAX_AGE}; HttpOnly; Secure; SameSite=Lax`
    );
  }
  return new Response(upstream.body, { status: upstream.status, statusText: upstream.statusText, headers });
}

export default {
  async fetch(request, env) {
    const password = env.DASHBOARD_PASSWORD;

    // 1) Already signed in via long-lived cookie — no prompt.
    if (readCookie(request, COOKIE_NAME) === password) {
      return serveAsset(request, env, null);
    }

    // 2) Basic Auth header — accept and set the cookie so next visit skips the prompt.
    const auth = request.headers.get("Authorization");
    if (auth && auth.startsWith("Basic ")) {
      try {
        const decoded = atob(auth.slice(6));
        const supplied = decoded.split(":").slice(1).join(":");
        if (supplied === password) {
          return serveAsset(request, env, password);
        }
      } catch (_) { /* malformed header — fall through to challenge */ }
    }

    // 3) Otherwise, challenge.
    return new Response("Password required", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="First Rain Dashboard"',
        "Content-Type": "text/plain",
        "Cache-Control": "no-store"
      }
    });
  }
};
