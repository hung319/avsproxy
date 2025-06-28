from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, FileResponse
from curl_cffi.requests import AsyncSession
import asyncio
import os
import hashlib # Thư viện để tạo tên file an toàn

app = FastAPI()

# Thư mục để lưu cache trên server Render
CACHE_DIR = "video_cache"
# Tạo thư mục cache nếu nó chưa tồn tại
os.makedirs(CACHE_DIR, exist_ok=True)

session = AsyncSession(impersonate="chrome120")

@app.get("/proxy")
async def proxy_request(request: Request):
    target_url = request.query_params.get("url")
    referer = request.query_params.get("referer")

    if not target_url:
        raise HTTPException(status_code=400, detail="Missing 'url' parameter")

    # Tạo một tên file cache duy nhất và an toàn từ URL gốc
    cache_filename = hashlib.md5(target_url.encode()).hexdigest()
    cache_filepath = os.path.join(CACHE_DIR, cache_filename)

    # === BƯỚC 1: KIỂM TRA CACHE ===
    if os.path.exists(cache_filepath):
        print(f"--> CACHE HIT for: {target_url}")
        # Nếu file đã tồn tại trong cache, trả về trực tiếp từ đĩa
        return FileResponse(cache_filepath)

    # === BƯỚC 2: TẢI MỚI NẾU KHÔNG CÓ CACHE (CACHE MISS) ===
    print(f"--> CACHE MISS for: {target_url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': referer or ''
    }

    try:
        resp = await session.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        resp.raise_for_status()

        final_content = resp.content
        
        # === BƯỚC 3: LƯU VÀO CACHE ===
        # Ghi nội dung vừa tải được vào file cache trên đĩa
        with open(cache_filepath, "wb") as f:
            f.write(final_content)
        print(f"--> SAVED to cache: {cache_filepath}")

        # Trả về nội dung cho người dùng lần đầu
        final_content_length = len(final_content)
        response_headers = {
            'Content-Type': resp.headers.get('Content-Type', 'application/octet-stream'),
            'Content-Length': str(final_content_length) 
        }

        return Response(
            content=final_content,
            status_code=resp.status_code,
            headers=response_headers
        )

    except Exception as e:
        print(f"[ERROR] Proxy for {target_url} failed: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch content: {e}")
