"""Search provider boundary. Tavily is the default; no MCP process is required."""
import requests
import os
import time

from .models import AIPlatformSettings, AIUsageRecord


def tavily_search(query, limit=5, domains=None, days=None, user=None):
    query = (query or "").strip()
    if not query:
        return []
    config = AIPlatformSettings.get_solo()
    key = config.get_tavily_api_key() or os.getenv("TAVILY_API_KEY", "")
    if not key:
        return []
    payload = {"api_key": key, "query": query, "max_results": min(int(limit), 10),
               "search_depth": "basic", "include_answer": False}
    if domains:
        payload["include_domains"] = list(domains)
    if days:
        payload["days"] = int(days)
    started = time.monotonic()
    try:
        response = requests.post("https://api.tavily.com/search", json=payload,
                                 timeout=min(config.request_timeout_seconds, 30))
        response.raise_for_status()
        results = [{"title": item.get("title", ""), "url": item.get("url", ""),
                    "snippet": item.get("content", "")}
                   for item in response.json().get("results", [])]
        AIUsageRecord.objects.create(
            user=user, provider="tavily", request_count=1, search_credits=1,
            latency_ms=int((time.monotonic() - started) * 1000),
        )
        return results
    except requests.RequestException as exc:
        AIUsageRecord.objects.create(
            user=user, provider="tavily", request_count=1, status="error",
            error_code=type(exc).__name__,
            latency_ms=int((time.monotonic() - started) * 1000),
        )
        raise
