"""mitmproxy addon - PLACEHOLDER.  Owner: Ipek.

Right now the proxy only passes traffic through.
TODO: for each request, send the URL to BACKEND_URL (env var) and block bad ones.
After editing: docker compose restart proxy
"""
from mitmproxy import http, ctx

def request(flow: http.HTTPFlow) -> None:
    ctx.log.info(f"Protocol: {flow.request.scheme}")
    ctx.log.info(f"Host: {flow.request.host}")
    ctx.log.info(f"URL: {flow.request.pretty_url}")