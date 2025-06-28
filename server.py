from fastapi import FastAPI, Request, HTTPException
# THAY ĐỔI: Import thêm 'Response' để trả về nội dung đầy đủ thay vì stream
from fastapi.responses import StreamingResponse, Response
from curl_cffi.requests import AsyncSession
import asyncio

app = FastAPI()

# Sử dụng profile mạo danh mà chúng ta biết là được hỗ trợ và hoạt động
session = AsyncSession(impersonate="chrome120")

@app.get("/proxy")
async def proxy_request(request: Request):
    target_url = request.query_params.get("url")
    referer = request.query_params.get("referer")

    if not target_url:
        raise HTTPException(status_code=400, detail="Missing 'url' parameter")

    # Header tối giản để gửi đi
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': referer or ''
    }

    try:
        print(f"--> PROXYING: {target_url}")
        resp = await session.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        
        print(f"<-- RESPONSE: Status={resp.status_code}, Content-Type={resp.headers.get('Content-Type')}")

        resp.raise_for_status()

        # === THAY ĐỔI LỚN: TẢI TOÀN BỘ NỘI DUNG VÀO BỘ NHỚ ===
        # Thay vì resp.iter_content(), chúng ta dùng resp.content
        # để lấy toàn bộ nội dung của segment.
        final_content = resp.content
        
        # Lấy kích thước chính xác của nội dung đã tải về.
        final_content_length = len(final_content)

        # Sao chép các header quan trọng từ phản hồi gốc.
        response_headers = {
            'Content-Type': resp.headers.get('Content-Type', 'application/octet-stream'),
            # Đặt Content-Length với kích thước chính xác của nội dung đã giải nén.
            'Content-Length': str(final_content_length) 
        }

        # Dùng 'Response' thay vì 'StreamingResponse' để gửi toàn bộ nội dung cùng lúc.
        return Response(
            content=final_content,
            status_code=resp.status_code,
            headers=response_headers
        )
        # === KẾT THÚC THAY ĐỔI ===

    except Exception as e:
        print(f"[ERROR] Proxy for {target_url} failed: {e}")
        try:
            print(f"[ERROR BODY] {e.response.text}")
        except:
            pass
        raise HTTPException(status_code=502, detail=f"Failed to fetch content: {e}")
