"""API tạo một video dọc 24 giây từ ba clip Veo 3.1."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

BASE_DIR = Path(os.getenv("VIDEO_OUTPUT_DIR", "./generated-videos")).resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)
VEO_URL = "https://api.geminigen.ai/uapi/v1/video-gen/veo"
GEMINIGEN_HISTORY_URL = "https://api.geminigen.ai/uapi/v1/history/{uuid}"
# Khớp với flow n8n được cung cấp: poll mỗi 30 giây; tối đa 20 lần = 10 phút.
GEMINIGEN_POLL_SECONDS = float(os.getenv("GEMINIGEN_POLL_SECONDS", "30"))
GEMINIGEN_MAX_POLLS = int(os.getenv("GEMINIGEN_MAX_POLLS", "20"))
IGNORED_COMPANY_FIELDS = {
    "CTA Video Link", "Logo File", "Booking or quote links", "Address",
    "Phone Number", "Background Music", "row_number",
}
VIDEO_URL_KEYS = {"video_url", "videoUrl", "url", "download_url", "downloadUrl"}
JOB_UUID_KEYS = {"uuid", "id", "task_uuid", "taskId"}


class GenerateVideoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    openai_api_key: str = Field(min_length=1)
    geminigen_api_key: str = Field(min_length=1)
    model: str = "veo-3.1"
    resolution: Literal["720p", "1080p"] = "1080p"
    aspect_ratio: Literal["9:16", "16:9"] = "9:16"
    duration: int = Field(default=8, ge=1, le=8)
    company_information: list[dict[str, Any]] = Field(min_length=1)
    before_images_path: list[Any] = Field(default_factory=list)
    during_images_path: list[Any] = Field(default_factory=list)
    after_images_path: list[Any] = Field(default_factory=list)

    @field_validator("company_information")
    @classmethod
    def company_must_have_name(cls, companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not any(str(c.get("Company Name", "")).strip() for c in companies):
            raise ValueError("company_information phải có 'Company Name'.")
        return companies


class GenerateVideoResponse(BaseModel):
    video_path: str
    video_url: str
    duration_seconds: int
    prompts: list[str]


app = FastAPI(title="Veo video generator", version="1.0.0")


def clean_company(company: dict[str, Any]) -> dict[str, Any]:
    """Loại dữ liệu không hữu ích/nhạy cảm trước khi gửi sang OpenAI."""
    return {key: value for key, value in company.items() if key not in IGNORED_COMPANY_FIELDS and value not in (None, "")}


def flatten_paths(value: Any) -> list[str]:
    """Chấp nhận cả ["/tmp/a.jpg"] lẫn [{"images": ["/tmp/a.jpg"]}]."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in flatten_paths(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in flatten_paths(child)]
    return []


def existing_image_paths(value: list[Any], label: str) -> list[Path]:
    paths: list[Path] = []
    for raw_path in flatten_paths(value):
        path = Path(raw_path)
        if not path.is_file():
            raise HTTPException(422, f"Không tìm thấy ảnh trong {label}: {raw_path}")
        paths.append(path)
    # Tránh request multipart cực lớn; Veo chỉ cần một số ảnh đại diện mỗi phân cảnh.
    return paths[:5]


async def create_prompts(request: GenerateVideoRequest, company: dict[str, Any]) -> list[str]:
    brief = json.dumps(clean_company(company), ensure_ascii=False, indent=2)
    instructions = """You write production-ready prompts for Veo 3.1. Return the structured output requested by the schema, with exactly three English prompt strings.
The three 8-second vertical clips form one premium local-service ad: (1) hook using the BEFORE state, (2) craftsmanship/process using DURING state, (3) beautiful finished result using AFTER state. Preserve the company style, services and brand colors when supplied. Make each clip visually simple: one primary subject/action, clean composition, realistic materials, smooth camera motion, sharp well-lit footage, no clutter. Do not invent offers, prices, guarantees, addresses, phone numbers, logos, or facts absent from the brief. Do NOT ask the video model to render readable words, captions, logos, UI, watermarks, signage, or a CTA: text generation is unreliable and any CTA will be appended separately. The final shot must leave clean negative space for a later CTA overlay. Explicitly avoid garbled text and watermarks."""
    user_input = f"""Company brief:
{brief}

Create the three prompts. Each must state it is a {request.duration}-second {request.aspect_ratio} video and name its visual role (HOOK, PROCESS, or RESULT)."""
    client = AsyncOpenAI(api_key=request.openai_api_key)
    try:
        response = await client.responses.create(
            model=os.getenv("OPENAI_PROMPT_MODEL", "gpt-4.1-mini"),
            instructions=instructions,
            input=user_input,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "veo_prompts",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "prompts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 3,
                                "maxItems": 3,
                            }
                        },
                        "required": ["prompts"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        prompts = json.loads(response.output_text)["prompts"]
    except Exception as exc:
        # Do not include API credentials in error details or logs.
        logger.exception("Prompt generation failed")
        raise HTTPException(502, "Không thể tạo prompt bằng OpenAI.") from exc
    if not isinstance(prompts, list) or len(prompts) != 3 or not all(isinstance(p, str) and p.strip() for p in prompts):
        raise HTTPException(502, "OpenAI không trả về đúng 3 prompt hợp lệ.")
    return prompts


def find_video_url(payload: Any) -> str | None:
    """Tìm URL mp4 ở các cấu trúc JSON thường gặp của nhà cung cấp."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in VIDEO_URL_KEYS and isinstance(value, str) and urlparse(value).scheme in {"http", "https"}:
                return value
        for value in payload.values():
            found = find_video_url(value)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = find_video_url(value)
            if found:
                return found
    return None


def find_job_uuid(payload: Any) -> str | None:
    """Lấy uuid để gọi GET /uapi/v1/history/{uuid} từ response tạo video."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in JOB_UUID_KEYS and isinstance(value, str) and value.strip():
                return value
        for value in payload.values():
            found = find_job_uuid(value)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = find_job_uuid(value)
            if found:
                return found
    return None


def geminigen_status(payload: Any) -> int | None:
    """Trạng thái n8n dùng số 2 (success) và 3 (failed)."""
    if isinstance(payload, dict):
        status = payload.get("status")
        if isinstance(status, int):
            return status
        if isinstance(status, str) and status.strip().isdigit():
            return int(status.strip())
        for value in payload.values():
            found = geminigen_status(value)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = geminigen_status(value)
            if found is not None:
                return found
    return None


async def wait_for_geminigen_video(
    client: httpx.AsyncClient, api_key: str, job_uuid: str
) -> str:
    """Poll đúng flow n8n: status=2 thành công, status=3 thất bại, khác thì chờ."""
    headers = {"x-api-key": api_key}
    for attempt in range(GEMINIGEN_MAX_POLLS):
        response = await client.get(GEMINIGEN_HISTORY_URL.format(uuid=job_uuid), headers=headers)
        response.raise_for_status()
        payload = response.json()
        status = geminigen_status(payload)
        if status == 2:
            video_url = find_video_url(payload)
            if not video_url:
                raise ValueError("GeminiGen success response does not contain a video URL")
            return video_url
        if status == 3:
            raise ValueError("GeminiGen marked the generation as failed")
        if attempt < GEMINIGEN_MAX_POLLS - 1:
            await asyncio.sleep(GEMINIGEN_POLL_SECONDS)
    raise TimeoutError("GeminiGen generation did not finish before poll limit")


async def generate_veo_clip(
    client: httpx.AsyncClient, request: GenerateVideoRequest, prompt: str, image_paths: list[Path], output_file: Path
) -> Path:
    files: list[tuple[str, tuple[str, bytes, str]]] = []
    for image in image_paths:
        mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
        files.append(("ref_images", (image.name, image.read_bytes(), mime)))
    data = {
        "prompt": prompt,
        "model": request.model,
        "resolution": request.resolution,
        "aspect_ratio": request.aspect_ratio,
        "duration": str(request.duration),
    }
    try:
        generation = await client.post(VEO_URL, headers={"x-api-key": request.geminigen_api_key}, data=data, files=files)
        generation.raise_for_status()
        payload = generation.json()
        video_url = find_video_url(payload)
        if not video_url:
            job_uuid = find_job_uuid(payload)
            if not job_uuid:
                raise ValueError("Create response does not contain a video URL or uuid")
            video_url = await wait_for_geminigen_video(client, request.geminigen_api_key, job_uuid)
        download = await client.get(video_url)
        download.raise_for_status()
        output_file.write_bytes(download.content)
    except (httpx.HTTPError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
        logger.exception("Veo generation/download failed")
        raise HTTPException(502, "GeminiGen/Veo không tạo được clip. Kiểm tra API key và phản hồi nhà cung cấp.") from exc
    return output_file


def concatenate(clips: list[Path], output: Path, aspect_ratio: str) -> None:
    """Chuẩn hoá rồi nối clip, tránh lỗi codec/timebase giữa ba video Veo."""
    scale = "1080:1920" if aspect_ratio == "9:16" else "1920:1080"
    command = ["ffmpeg", "-y"]
    for clip in clips:
        command.extend(["-i", str(clip)])
    filter_parts = [
        f"[{index}:v]scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{index}]"
        for index in range(3)
    ]
    filter_parts.append("[v0][v1][v2]concat=n=3:v=1:a=0[outv]")
    command.extend(["-filter_complex", ";".join(filter_parts), "-map", "[outv]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)])
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if result.returncode:
        logger.error("ffmpeg failed: %s", result.stderr[-2000:])
        raise HTTPException(500, "Không thể nối ba clip bằng ffmpeg.")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate-video/", response_model=GenerateVideoResponse)
async def generate_video(request: GenerateVideoRequest) -> GenerateVideoResponse:
    """Tạo 3 clip Veo theo ảnh before/during/after và nối chúng thành một video."""
    job_id = uuid.uuid4().hex
    job_dir = BASE_DIR / job_id
    job_dir.mkdir()
    company = next(item for item in request.company_information if str(item.get("Company Name", "")).strip())
    before = existing_image_paths(request.before_images_path, "before_images_path")
    during = existing_image_paths(request.during_images_path, "during_images_path")
    after = existing_image_paths(request.after_images_path, "after_images_path")
    try:
        prompts = await create_prompts(request, company)
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=30.0), follow_redirects=True) as client:
            clips = await asyncio.gather(
                generate_veo_clip(client, request, prompts[0], before, job_dir / "01-hook.mp4"),
                generate_veo_clip(client, request, prompts[1], during, job_dir / "02-process.mp4"),
                generate_veo_clip(client, request, prompts[2], after, job_dir / "03-result.mp4"),
            )
        output = job_dir / "video-24s.mp4"
        await asyncio.to_thread(concatenate, clips, output, request.aspect_ratio)
    except HTTPException:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        logger.exception("Unexpected video job error")
        raise HTTPException(500, "Lỗi không mong đợi khi tạo video.") from exc
    return GenerateVideoResponse(
        video_path=str(output),
        video_url=f"/videos/{job_id}/{output.name}",
        duration_seconds=request.duration * 3,
        prompts=prompts,
    )


@app.get("/videos/{job_id}/{filename}")
async def get_video(job_id: str, filename: str) -> FileResponse:
    if not re.fullmatch(r"[a-f0-9]{32}", job_id) or filename != "video-24s.mp4":
        raise HTTPException(404, "Không tìm thấy video.")
    file_path = BASE_DIR / job_id / filename
    if not file_path.is_file():
        raise HTTPException(404, "Không tìm thấy video.")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)
