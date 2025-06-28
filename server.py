from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from curl_cffi.requests import AsyncSession
import asyncio

app = FastAPI()

# Dùng profile desktop mà chúng ta biết là được hỗ trợ
session = AsyncSession(impersonate="chrome120")

@app.get("/proxy")
async def proxy_request(request: Request):
    target_url = request.query_params.get("url")
    referer = request.query_params.get("referer")

    if not target_url:
        raise HTTPException(status_code=400, detail="Missing 'url' parameter")

    # Chỉ giữ lại 2 header thiết yếu nhất cho request gửi đi
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': referer
    }

    try:
        print(f"Attempting to proxy URL: {target_url}")
        resp = await session.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        
        print(f"Upstream response status: {resp.status_code}")
        print(f"Upstream response content-type: {resp.headers.get('Content-Type')}")

        resp.raise_for_status()

        # === THAY ĐỔI QUAN TRỌNG ===
        # Trả về dữ liệu thô mà không đặt bất kỳ header nào.
        # Trình phát sẽ phải tự xác định loại nội dung.
        return StreamingResponse(resp.iter_content(chunk_size=8192))
        # === KẾT THÚC THAY ĐỔI ===

    except Exception as e:
        print(f"Error during proxy for {target_url}: {e}")
        try:
            print(f"Response body from failed request: {e.response.text}")
        except:
            pass
        raise HTTPException(status_code=502, detail=f"Failed to fetch content: {e}")
