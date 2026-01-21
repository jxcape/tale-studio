#!/usr/bin/env python3
"""
시네마틱 씬 생성 - 자연스러운 영화 장면처럼.

핵심: 이미지가 움직이는 게 아니라, 영화의 한 장면.
"""
import asyncio
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.settings import Settings
from adapters.gateways.veo_video import VeoVideoGenerator
from usecases.interfaces import VideoRequest


# 레퍼런스 이미지
REFERENCE_IMAGE = "generated_videos/final_test/luterra_final_20260117_201315.png"

# 최소화된 자연스러운 모션 프롬프트
# - VFX 지시 제거
# - 씬의 맥락과 자연스러운 움직임만
SCENE_PROMPT = """A young warrior prince stands on a battlefield at dusk.

He slowly lifts his gaze from the ground, revealing determined eyes.
A subtle breath. The weight of decision on his face.
Wind gently moves his hair and cape.

The camera slowly pushes in on his face.
Shallow depth of field. Cinematic.

Natural subtle movements only.
24fps film look."""


async def main():
    print("=" * 70)
    print("Cinematic Scene Generation")
    print("=" * 70)

    ref_path = Path(REFERENCE_IMAGE)
    if not ref_path.exists():
        print(f"Error: Reference not found: {REFERENCE_IMAGE}")
        return

    settings = Settings()
    api_keys = settings.google_api_keys_list
    if not api_keys:
        print("Error: No API keys")
        return

    output_dir = Path("generated_videos/cinematic_scene")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    veo = VeoVideoGenerator(
        api_key=api_keys[0],
        model="veo-3.1-generate-preview",
        poll_interval=10.0,
    )

    print(f"\nReference: {ref_path}")
    print(f"\nPrompt ({len(SCENE_PROMPT)} chars):")
    print("-" * 40)
    print(SCENE_PROMPT)
    print("-" * 40)

    try:
        request = VideoRequest(
            prompt=SCENE_PROMPT,
            duration_seconds=8,
            aspect_ratio="16:9",
            reference_image_path=str(ref_path),
        )

        print("\n[GENERATING]...")
        job = await veo.generate(request)
        print(f"Job: {job.job_id[:50]}...")

        print("\n[WAITING]...")
        completed = await veo.wait_for_completion(job.job_id, timeout_seconds=900)

        if completed.status.value == "completed" and completed.video_url:
            video_path = output_dir / f"scene_{timestamp}.mp4"
            saved = await veo.download(completed.video_url, str(video_path))
            print(f"\n✓ Video: {saved}")
        else:
            print(f"\n✗ Failed: {completed.error_message}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
    finally:
        await veo.close()


if __name__ == "__main__":
    asyncio.run(main())
