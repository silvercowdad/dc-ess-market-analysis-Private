"""Tavily 웹 검색 도구."""
import os
import httpx


async def tavily_search(query: str, max_results: int = 5) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "[웹 검색 불가: TAVILY_API_KEY 환경변수가 설정되지 않았습니다]"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_answer": True,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        parts = []
        if answer := data.get("answer"):
            parts.append(f"요약: {answer}\n")
        for r in data.get("results", []):
            parts.append(
                f"제목: {r['title']}\n"
                f"URL: {r['url']}\n"
                f"내용: {r.get('content', '')[:600]}\n"
            )
        return "\n---\n".join(parts) if parts else "검색 결과 없음"

    except Exception as e:
        return f"[검색 오류: {e}]"
