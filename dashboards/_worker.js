export default {
  async fetch(request, env) {
    const auth = request.headers.get("Authorization");
    if (auth && auth.startsWith("Basic ")) {
      const decoded = atob(auth.slice(6));
      const password = decoded.split(":").slice(1).join(":");
      if (password === env.DASHBOARD_PASSWORD) {
        return env.ASSETS.fetch(request);
      }
    }
    return new Response("Password required", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="First Rain Dashboard"',
        "Content-Type": "text/plain"
      }
    });
  }
};
