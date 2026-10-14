# Video generator cho 10 công ty

FastAPI này tạo một video **24 giây** từ ba clip Veo 3.1 chạy song song:

1. Hook (ảnh `before`)
2. Content / quy trình (ảnh `during`)
3. Thành phẩm (ảnh `after`)

CTA 6 giây có sẵn **không** được chèn vào API này. Hãy nối nó sau trong n8n để có video 30 giây. Prompt chủ động cấm chữ/logo/watermark sinh bởi AI; CTA và text có thể đọc được nên được overlay/ghép ở bước riêng.

## Chạy local

```bash
cd n8n/create-video-for-10-companies
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Cần cài `ffmpeg`. Có thể dùng Docker:

```bash
docker build -t veo-video-api .
docker run --rm -p 8000:8000 -v "$(pwd)/generated-videos:/data/generated-videos" veo-video-api
```

## Gọi từ n8n

Sử dụng node **HTTP Request**:

- Method: `POST`
- URL: `http://<host-api>:8000/generate-video/`
- Body Content Type: `JSON`
- JSON Body: dữ liệu từ [sample-request.json](sample-request.json). Truyền key qua expression của n8n, không hard-code vào workflow.

Ví dụ response:

```json
{
  "video_path": "/data/generated-videos/<job-id>/video-24s.mp4",
  "video_url": "/videos/<job-id>/video-24s.mp4",
  "duration_seconds": 24,
  "prompts": ["...", "...", "..."]
}
```

`video_path` là đường dẫn của máy/chứa container đang chạy API. Nếu n8n ở máy khác, dùng `http://<host-api>:8000` + `video_url` để tải file. API chỉ nhận các đường dẫn ảnh có thật và dùng tối đa 5 ảnh cho mỗi nhóm.

## Tích hợp Veo đã phân tích

Mỗi clip gọi:

```text
POST https://api.geminigen.ai/uapi/v1/video-gen/veo
x-api-key: <geminigen_api_key>
multipart/form-data:
  prompt, model=veo-3.1, resolution=1080p, aspect_ratio=9:16,
  duration=8, ref_images=<một hoặc nhiều file ảnh>
```

Sau đó API đọc `uuid` trong response và poll:

```text
GET https://api.geminigen.ai/uapi/v1/history/{uuid}
x-api-key: <geminigen_api_key>
```

Logic được lấy trực tiếp từ workflow n8n đã cung cấp: `status = 2` thì lấy URL video để tải xuống; `status = 3` thì dừng với lỗi; các status khác thì đợi 30 giây và gọi lại. Mặc định tối đa 20 lần (10 phút); chỉnh được bằng `GEMINIGEN_POLL_SECONDS` và `GEMINIGEN_MAX_POLLS`.

Service không ghi log API key. Prompt được yêu cầu từ OpenAI Responses API dưới dạng JSON schema (đúng ba prompt). Trước khi gửi brief sang OpenAI, nó loại chính xác các trường: `CTA Video Link`, `Logo File`, `Booking or quote links`, `Address`, `Phone Number`, `Background Music`, `row_number`.
