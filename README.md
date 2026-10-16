# Video generator cho 10 công ty

FastAPI này tạo một video hoàn chỉnh khoảng **30 giây**: ba clip Veo 3.1 (24 giây) chạy song song, sau đó ghép CTA có sẵn (thường 6 giây) ở cuối:

1. Hook (ảnh `before`)
2. Content / quy trình (ảnh `during`)
3. Thành phẩm (ảnh `after`)

Truyền CTA qua `cta_video_path`. Service chuẩn hoá khung hình/codec, thêm silent audio nếu một đoạn không có audio, và giữ audio sẵn có của từng clip. Prompt chủ động cấm chữ/logo/watermark sinh bởi AI; CTA chứa text đọc được được giữ nguyên ở đoạn cuối. Prompt cũng ưu tiên cảnh không người; nếu buộc phải có thợ, chỉ cho phép một người ở góc rộng và cấm lỗi giải phẫu như dư tay/ngón hoặc biến dạng cơ thể.

## Chạy local

```bash
cd n8n/create-video-for-10-companies
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Gọi từ n8n

### Docker Compose dùng chung với n8n

`docker-compose.yml` đã có service `video-generator` và đặt nó cùng network với n8n. Không cần publish port `8000` ra Internet; trong mọi node n8n (kể cả worker), gọi URL nội bộ:

```text
http://video-generator:8000/generate-video/
```

Tất cả container n8n/worker và `video-generator` dùng chung host directory `${DEPLOY_FOLDER}/local_files`, với container path là `/files`. `/files` là thư mục workflow dùng để đọc/ghi ảnh và video; không dùng nó làm `N8N_BINARY_DATA_STORAGE_PATH`, vì n8n sẽ chặn node **Read/Write Files from Disk** ghi vào binary-data directory của chính n8n. Compose giới hạn file node ở `/files` qua `N8N_RESTRICT_FILE_ACCESS_TO`.

> `before_images_path`, `during_images_path`, `after_images_path` đều không bắt buộc. Có thể bỏ hẳn field, gửi `[]`, hoặc `null`; service vẫn tạo clip bằng brief công ty. `cta_video_path` là bắt buộc và phải trỏ đến video CTA có thật trong `/files/...`. Không dùng `/tmp/...`: `/tmp` của n8n và Python là hai filesystem riêng. Video kết quả nằm ở `/files/generated-videos/<job-id>/video-30s.mp4`, nên n8n có thể đọc trực tiếp bằng node Read/Write Files from Disk.

Trước khi redeploy, pin `N8N_IMAGE` trong `.env` thành tag n8n hiện chạy (đừng để `latest` tự đổi phiên bản). Sau đó chạy:

```bash
cd <thu-muc-deploy>
docker compose up -d --build video-generator
docker compose up -d
```

Kiểm tra service từ container n8n:

```bash
docker compose exec n8n wget -qO- http://video-generator:8000/health
```

### HTTP Request node

Sử dụng node **HTTP Request**:

- Method: `POST`
- URL: `http://video-generator:8000/generate-video/`
- Body Content Type: `JSON`
- JSON Body: dữ liệu từ [sample-request.json](sample-request.json). Truyền key qua expression của n8n, không hard-code vào workflow.
- Timeout: `900000` ms (15 phút), vì GeminiGen có thể poll tối đa 10 phút.

### Import cURL vào HTTP Request node

Trong n8n, thêm node **HTTP Request** → chọn menu ba chấm → **Import cURL** → dán nguyên khối lệnh dưới đây. n8n sẽ tự tạo method, URL, header và JSON body. Đây không phải lệnh để chạy trong terminal.

```bash
curl --max-time 900 \
  -X POST 'http://video-generator:8000/generate-video/' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "openai_api_key": "<OPENAI_API_KEY>",
    "geminigen_api_key": "<GEMINIGEN_API_KEY>",
    "imgbb_api_key": "<IMGBB_API_KEY>",
    "model": "veo-3.1",
    "resolution": "1080p",
    "aspect_ratio": "9:16",
    "duration": 8,
    "company_information": [
      {
        "json": {
          "Company Name": "SlabX Kitchens & Countertops",
          "Video and Image Style": "Premium, design-led, confident",
          "Services List": "Quartz countertops, custom cabinetry"
        },
        "pairedItem": {"item": 0}
      }
    ],
    "before_images_path": "/files/slabx/before-1.jpg,/files/slabx/before-2.jpg",
    "during_images_path": "",
    "after_images_path": null,
    "cta_video_path": "/files/cta.mp4"
  }'
```

Sau khi import, thay các giá trị `"<..._API_KEY>"` bằng **Expression** lấy từ node Config/credential của bạn; không lưu API key thật trong node. Đặt **Options → Timeout** là `900000` ms nếu Import cURL chưa tự thiết lập timeout.

Các field ảnh là optional. API hỗ trợ chuỗi đường dẫn phân cách bằng dấu phẩy (như payload từ n8n), mảng hoặc `null`. `cta_video_path` là bắt buộc. Nếu có ảnh local, `imgbb_api_key` là bắt buộc: service upload tối đa 5 ảnh mỗi nhóm lên ImgBB (expiration 60.000 giây), sau đó truyền direct URL từ ImgBB trong `ref_images` cho GeminiGen. Ảnh và CTA phải tồn tại trong `${DEPLOY_FOLDER}/local_files` trên VPS, tương ứng với `/files/...` trong container. Response chứa `video_path`, ví dụ `/files/generated-videos/<job-id>/video-30s.mp4`.

Ví dụ response:

```json
{
  "video_path": "/files/generated-videos/<job-id>/video-30s.mp4",
  "video_url": "/videos/<job-id>/video-30s.mp4",
  "duration_seconds": 30.0,
  "prompts": ["...", "...", "..."]
}
```

`video_path` là đường dẫn dùng chung giữa n8n và Python (`/files/generated-videos/...`). API chỉ nhận các đường dẫn ảnh có thật và dùng tối đa 5 ảnh cho mỗi nhóm.

## Tích hợp Veo đã phân tích

Mỗi clip gọi:

```text
POST https://api.geminigen.ai/uapi/v1/video-gen/veo
x-api-key: <geminigen_api_key>
multipart/form-data:
  prompt, model=veo-3.1, resolution=1080p, aspect_ratio=9:16,
  duration=8, ref_images=<các direct URL ImgBB phân cách bằng dấu phẩy, optional>
```

Sau đó API đọc `uuid` trong response và poll:

```text
GET https://api.geminigen.ai/uapi/v1/history/{uuid}
x-api-key: <geminigen_api_key>
```

Logic được lấy trực tiếp từ workflow n8n đã cung cấp: `status = 2` thì lấy URL video để tải xuống; `status = 3` thì dừng với lỗi; các status khác thì đợi 30 giây và gọi lại. Mặc định tối đa 20 lần (10 phút); chỉnh được bằng `GEMINIGEN_POLL_SECONDS` và `GEMINIGEN_MAX_POLLS`.

Service không ghi log API key. Prompt được yêu cầu từ OpenAI Responses API dưới dạng JSON schema (đúng ba prompt). Trước khi gửi brief sang OpenAI, nó loại chính xác các trường: `CTA Video Link`, `Logo File`, `Booking or quote links`, `Address`, `Phone Number`, `Background Music`, `row_number`.
