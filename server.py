from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
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
        
        # In log để debug
        print(f"<-- RESPONSE: Status={resp.status_code}, Content-Type={resp.headers.get('Content-Type')}")

        # Nếu server đích trả về lỗi, chúng ta cũng trả về lỗi đó
        resp.raise_for_status()

        # === THAY ĐỔI QUAN TRỌNG: SAO CHÉP HEADER GỐC ===
        # Loại bỏ các "hop-by-hop header" không nên được chuyển tiếp bởi proxy.
        excluded_headers = [
            'content-encoding', 
            'transfer-encoding', 
            'connection', 
            'content-length' # Sẽ được xử lý tự động bởi StreamingResponse
        ]
        
        # Sao chép tất cả các header còn lại từ phản hồi gốc.
        # Điều này đảm bảo Content-Type, Content-Disposition (nếu có), etc. được giữ nguyên.
        response_headers = {
            key: value for key, value in resp.headers.items() if key.lower() not in excluded_headers
        }
        
        # Trả về StreamingResponse với NỘI DUNG, MÃ TRẠNG THÁI, và HEADER gốc.
        return StreamingResponse(
            resp.iter_content(chunk_size=8192), 
            status_code=resp.status_code, 
            headers=response_headers
        )
        # === KẾT THÚC THAY ĐỔI ===

    except Exception as e:
        print(f"[ERROR] Proxy for {target_url} failed: {e}")
        # Cố gắng in ra nội dung lỗi từ server đích nếu có
        try:
            print(f"[ERROR BODY] {e.response.text}")
        except:
            pass
        raise HTTPException(status_code=502, detail=f"Failed to fetch content: {e}")
