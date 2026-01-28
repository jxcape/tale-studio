#!/usr/bin/env python3
"""
프롬프트로 Veo 영상 생성.

Usage:
    python scripts/generate_videos.py [--limit N] [--start N]
"""
import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.settings import Settings
from infrastructure.api_key_pool import APIKeyPool, RotationStrategy
from adapters.gateways.veo_video import VeoVideoGenerator
from usecases.interfaces import VideoRequest, VideoStatus


# 최신 파이프라인 결과 찾기
def find_latest_pipeline_output() -> Path:
    output_dir = Path("pipeline_output")
    dirs = sorted(output_dir.iterdir(), reverse=True)
    for d in dirs:
        if d.is_dir() and (d / "pipeline_result.json").exists():
            return d
    raise FileNotFoundError("No pipeline output found")


async def generate_video(
    veo: VeoVideoGenerator,
    prompt: str,
    shot_id: str,
    output_dir: Path,
    duration: int = 5,
) -> dict:
    """단일 영상 생성."""
    print(f"\n[{shot_id}] 영상 생성 시작...")
    print(f"  프롬프트: {prompt[:100]}...")

    try:
        # 영상 생성 요청
        request = VideoRequest(
            prompt=prompt,
            duration_seconds=duration,
            aspect_ratio="16:9",
        )

        job = await veo.generate(request)
        print(f"  Job ID: {job.job_id}")

        # 완료 대기
        job = await veo.wait_for_completion(job.job_id, timeout_seconds=600)

        if job.status == VideoStatus.COMPLETED:
            # 영상 다운로드
            video_path = output_dir / f"{shot_id}.mp4"
            await veo.download(job.video_url, str(video_path))
            print(f"  ✓ 완료: {video_path}")
            return {"shot_id": shot_id, "status": "success", "path": str(video_path)}
        else:
            print(f"  ✗ 실패: {job.error_message}")
            return {"shot_id": shot_id, "status": "failed", "error": job.error_message}

    except Exception as e:
        print(f"  ✗ 에러: {e}")
        return {"shot_id": shot_id, "status": "error", "error": str(e)}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="생성할 영상 수")
    parser.add_argument("--start", type=int, default=0, help="시작 인덱스")
    parser.add_argument("--model", default="veo-2.0-generate-001", help="Veo 모델")
    parser.add_argument("--output-dir", type=str, help="출력 디렉토리 (없으면 파이프라인 타임스탬프 사용)")
    parser.add_argument("--delay", type=int, default=30, help="요청 간 대기 시간(초)")
    args = parser.parse_args()

    # 설정 로드
    settings = Settings()

    # 최신 파이프라인 결과 로드
    pipeline_dir = find_latest_pipeline_output()
    print(f"파이프라인 결과: {pipeline_dir}")

    with open(pipeline_dir / "pipeline_result.json") as f:
        result = json.load(f)

    prompts = result.get("prompts", [])
    print(f"총 {len(prompts)}개 프롬프트")

    # 생성할 프롬프트 선택
    selected = prompts[args.start:args.start + args.limit]
    print(f"생성 대상: {len(selected)}개 (인덱스 {args.start}~{args.start + len(selected) - 1})")

    # 출력 디렉토리 (파이프라인 타임스탬프 기준)
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        pipeline_timestamp = result.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
        output_dir = Path(f"generated_videos/trailer_{pipeline_timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"출력 디렉토리: {output_dir}")

    # API 키 풀 설정
    key_infos = settings.google_api_key_infos
    key_pool = APIKeyPool(
        keys=key_infos,
        strategy=RotationStrategy.ROUND_ROBIN,
        daily_limit=10,  # Veo 일일 한도
        max_failures_per_key=3,
    )
    print(f"API Key Pool: {len(key_infos)}개 키")

    # Veo 생성기 (첫 번째 키로 시작, 실패시 수동 교체)
    first_key = key_infos[0].key
    veo = VeoVideoGenerator(api_key=first_key, model=args.model)

    print(f"\n{'='*60}")
    print(f"Veo 영상 생성 시작 (모델: {args.model})")
    print(f"{'='*60}")

    results = []
    current_key_idx = 0

    for i, prompt_data in enumerate(selected):
        shot_id = prompt_data["shot_id"]
        prompt = prompt_data["final_prompt"]
        duration = prompt_data.get("duration", 5)

        # 5초 최소
        duration = max(5, min(8, int(duration)))

        result = await generate_video(veo, prompt, shot_id, output_dir, duration)
        results.append(result)

        # 성공 후 다음 요청 전 딜레이 (rate limit 방지)
        if result["status"] == "success" and i < len(selected) - 1:
            print(f"  [대기] {args.delay}초...")
            await asyncio.sleep(args.delay)

        # 실패시 다음 키로 교체 시도
        if result["status"] in ("failed", "error") and "429" in str(result.get("error", "")):
            current_key_idx += 1
            if current_key_idx < len(key_infos):
                print(f"\n[키 교체] {key_infos[current_key_idx].alias}로 전환...")
                await veo.close()
                veo = VeoVideoGenerator(
                    api_key=key_infos[current_key_idx].key,
                    model=args.model
                )
            else:
                print("\n[한도 초과] 모든 키 소진. 중단.")
                break

    await veo.close()

    # 결과 저장
    result_file = output_dir / "generation_result.json"
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 요약
    print(f"\n{'='*60}")
    print("생성 완료")
    print(f"{'='*60}")
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    print(f"성공: {success}개, 실패: {failed}개")
    print(f"결과: {result_file}")


if __name__ == "__main__":
    asyncio.run(main())
