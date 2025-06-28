from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from curl_cffi.requests import AsyncSession
import asyncio

app = FastAPI()

# Đổi profile mạo danh sang phiên bản mới hơn
session = AsyncSession(impersonate="chrome120")

@app.get("/proxy")
async def proxy_request(request: Request):
    target_url = request.query_params.get("url")
    referer = request.query_params.get("referer")

    if not target_url:
        raise HTTPException(status_code=400, detail="Missing 'url' parameter")

    # THÊM CÁC HEADER BROWSER HIỆN ĐẠI
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Referer': referer or '',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?1',
        'Sec-Ch-Ua-Platform': '"Android"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        resp = await session.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        resp.raise_for_status()

        response_headers = {
            'Content-Type': resp.headers.get('Content-Type', 'application/octet-stream'),
            'Content-Length': resp.headers.get('Content-Length'),
        }
        response_headers = {k: v for k, v in response_headers.items() if v is not None}

        return StreamingResponse(resp.iter_content(chunk_size=8192), headers=response_headers)

    except Exception as e:
        print(f"Error proxying {target_url}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch content: {e}")
