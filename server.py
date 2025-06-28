from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from curl_cffi.requests import AsyncSession
import asyncio

app = FastAPI()

# Tạo một session để tái sử dụng, giúp tăng tốc độ
# "chrome110" là một trong những profile mạo danh mạnh nhất
session = AsyncSession(impersonate="chrome110")

@app.get("/proxy")
async def proxy_request(request: Request):
    target_url = request.query_params.get("url")
    referer = request.query_params.get("referer")

    if not target_url:
        raise HTTPException(status_code=400, detail="Missing 'url' parameter")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Referer': referer or ''
    }

    try:
        # Dùng curl_cffi để gửi request
        resp = await session.get(target_url, headers=headers, timeout=30, allow_redirects=True)

        # Kiểm tra xem request có thành công không
        resp.raise_for_status()

        # Lấy các header từ response gốc để trả về cho client
        response_headers = {
            'Content-Type': resp.headers.get('Content-Type', 'application/octet-stream'),
            'Content-Length': resp.headers.get('Content-Length'),
        }
        # Loại bỏ các header rỗng
        response_headers = {k: v for k, v in response_headers.items() if v is not None}

        # Trả về dữ liệu dạng stream để tiết kiệm bộ nhớ
        return StreamingResponse(resp.iter_content(chunk_size=8192), headers=response_headers)

    except Exception as e:
        print(f"Error proxying {target_url}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch content: {e}")

# Để chạy server: mở terminal, gõ lệnh "uvicorn server:app --host 0.0.0.0 --port 8000"
