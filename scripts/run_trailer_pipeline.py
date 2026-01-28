#!/usr/bin/env python3
"""
트레일러용 파이프라인: L1 → L3 (L2 스킵)

샷 리스트 형태의 스토리를 바로 프롬프트로 변환.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime

import sys
import logging
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.settings import Settings
from infrastructure.api_key_pool import APIKeyPool, RotationStrategy
from adapters.gateways.gemini_llm import GeminiLLMGateway
from adapters.repositories.file_repository import FileAssetRepository
from usecases.interfaces import LLMRequest

logging.basicConfig(level=logging.INFO, format='%(message)s')

# =============================================================================
# 트레일러 샷 리스트 (각 항목 = 1 샷 = 1 프롬프트)
# =============================================================================
SHOTS = [
    # === ACT 1: 절망 (빠른 컷) ===
    {
        "id": "shot_01",
        "duration": 5,
        "type": "EWS",
        "description": "붉은 하늘 아래 불타는 대륙. 화염 기둥이 솟구친다. 연기가 하늘을 뒤덮는다.",
        "camera": "Aerial shot, slow descent through smoke",
        "mood": "Apocalyptic"
    },
    {
        "id": "shot_02",
        "duration": 5,
        "type": "EWS",
        "description": "악마 군단이 하늘을 가득 채운다. 수만 개의 검은 날개. 끝이 보이지 않는 어둠의 물결.",
        "camera": "Low angle, looking up at overwhelming darkness",
        "mood": "Terrifying, hopeless"
    },
    {
        "id": "shot_03",
        "duration": 5,
        "type": "MS",
        "description": "폐허 속 쓰러진 병사들. 부러진 검과 깃발. 피와 먼지. 패배한 전장.",
        "camera": "Slow tracking through battlefield debris",
        "mood": "Defeat, despair"
    },

    # === ACT 2: 대비 - 교차 편집 (적 vs 아군) ===
    {
        "id": "shot_04",
        "duration": 5,
        "type": "ECU",
        "description": "악마의 발굽이 땅을 밟는다. 갈라지는 대지. 먼지가 솟구친다.",
        "camera": "Ground level, impact shot",
        "mood": "Ominous, heavy"
    },
    {
        "id": "shot_05",
        "duration": 5,
        "type": "ECU",
        "description": "인간의 부츠가 땅을 딛는다. 굳건하게. 흔들리지 않는다.",
        "camera": "Ground level, steady stance",
        "mood": "Defiance"
    },
    {
        "id": "shot_06",
        "duration": 5,
        "type": "CU",
        "description": "악마의 이빨. 침을 흘리며 으르렁거린다. 굶주린 포식자.",
        "camera": "Close-up, shallow DOF, saliva dripping",
        "mood": "Monstrous, hungry"
    },
    {
        "id": "shot_07",
        "duration": 5,
        "type": "CU",
        "description": "아제나의 입술이 말없이 다물어진다. 이를 악문다. 각오.",
        "camera": "Close-up on lips and jaw, tension",
        "mood": "Silent determination",
        "character": "아제나"
    },

    # === ACT 3: 플래시 컷 - 에스더들 (빠르게) ===
    {
        "id": "shot_08",
        "duration": 5,
        "type": "CU",
        "description": "카단의 손이 검 손잡이를 쥔다. 손등의 핏줄이 선다.",
        "camera": "Extreme close-up on hand gripping sword",
        "mood": "Tension",
        "character": "카단"
    },
    {
        "id": "shot_09",
        "duration": 5,
        "type": "MS",
        "description": "루테란의 뒷모습. 망토가 바람에 날린다. 앞에 펼쳐진 악마 군단. 혼자 서 있다.",
        "camera": "Behind shoulder, facing endless enemy",
        "mood": "Solitary, overwhelming odds",
        "character": "루테란"
    },

    # === ACT 4: 전투 플래시 ===
    {
        "id": "shot_10",
        "duration": 5,
        "type": "MS",
        "description": "검과 검이 부딪친다. 스파크가 튄다. 어둠 속 섬광.",
        "camera": "Dynamic angle, sparks flying",
        "mood": "Clash, intensity"
    },
    {
        "id": "shot_11",
        "duration": 5,
        "type": "EWS",
        "description": "전장 위로 마법 폭발. 붉은 빛과 푸른 빛이 충돌. 실루엣들이 싸운다.",
        "camera": "Wide shot, magical explosions backlighting figures",
        "mood": "Chaos, war"
    },

    # === ACT 5: 클라이맥스 - 루테란 돌격 (속도감) ===
    {
        "id": "shot_12",
        "duration": 8,
        "type": "TRACKING",
        "description": "루테란이 천천히 걷는다. 검을 땅에 끌며. 검날이 돌바닥에 긁히며 불꽃이 튄다. 걸음이 빨라진다. 뛰기 시작한다. 전력 질주. 카메라가 함께 달린다. 바람이 얼굴을 때린다. 망토가 휘날린다. 점점 빨라지는 발걸음. 앞만 보는 눈.",
        "camera": "Side tracking shot accelerating with character, starts slow ends sprinting, wind and debris",
        "mood": "Building momentum, unstoppable charge",
        "character": "루테란"
    },
]

# 캐릭터 정보
CHARACTERS = {
    "루테란": "45-year-old male warrior king, ornate golden armor with lion motifs on shoulders, blue cape flowing in wind, short black hair with grey streaks, weathered face with determined eyes, holding the legendary golden sword 'Sword of the Victor'",
    "아제나": "30-year-old female warrior queen, crimson and black angular armor with runic engravings, long black hair flowing, pale skin, fierce eyes burning with rage, tears in eyes, twin swords on back",
    "카단": "40-year-old male guardian, silver-white holy armor glowing faintly, short silver hair swept back, calm and wise eyes, tower shield on back, drawing a gleaming sword",
}

STYLE_SUFFIX = "Cinematic, epic fantasy, photorealistic, dramatic lighting, 8K quality, film grain, shallow depth of field. Negative: cartoon, anime, CGI look, deformed faces"


async def build_prompt(llm: GeminiLLMGateway, shot: dict) -> str:
    """샷 정보를 영상 생성 프롬프트로 변환."""

    # 캐릭터 정보 추가
    character_desc = ""
    if "character" in shot:
        for name, desc in CHARACTERS.items():
            if name in shot["character"]:
                character_desc = f"Character: {desc}. "
                break

    # 프롬프트 조합
    prompt = f"{shot['description']} {character_desc}Camera: {shot['camera']}. Mood: {shot['mood']}. {STYLE_SUFFIX}"

    return prompt


async def main():
    print("=" * 70)
    print("Trailer Pipeline: Shot List → Prompts (L2 Skip)")
    print("=" * 70)

    # 설정
    settings = Settings()

    # 출력 디렉토리
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"pipeline_output/trailer_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # API 키 풀
    key_infos = settings.google_api_key_infos
    key_pool = APIKeyPool(
        keys=key_infos,
        strategy=RotationStrategy.ROUND_ROBIN,
        daily_limit=1500,
        max_failures_per_key=3,
    )
    print(f"API Key Pool: {len(key_infos)}개 키")

    llm = GeminiLLMGateway(key_pool=key_pool, model="gemini-2.0-flash-lite")

    print(f"\n총 {len(SHOTS)}개 샷")
    print(f"출력: {output_dir}\n")

    # 프롬프트 생성
    prompts = []
    for shot in SHOTS:
        prompt = await build_prompt(llm, shot)
        prompts.append({
            "shot_id": shot["id"],
            "duration": shot["duration"],
            "shot_type": shot["type"],
            "final_prompt": prompt,
        })
        print(f"[{shot['id']}] {shot['type']} | {shot['duration']}초")
        print(f"  → {prompt[:80]}...")
        print()

    await llm.close()

    # 결과 저장
    result = {
        "timestamp": timestamp,
        "total_shots": len(SHOTS),
        "total_duration": sum(s["duration"] for s in SHOTS),
        "shots": SHOTS,
        "prompts": prompts,
    }

    result_file = output_dir / "pipeline_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # 프롬프트 텍스트 파일
    prompts_file = output_dir / "prompts.txt"
    with open(prompts_file, "w", encoding="utf-8") as f:
        for p in prompts:
            f.write(f"=== {p['shot_id']} ({p['duration']}s) ===\n")
            f.write(f"{p['final_prompt']}\n\n")

    print("=" * 70)
    print("완료")
    print("=" * 70)
    print(f"샷: {len(SHOTS)}개")
    print(f"총 길이: {sum(s['duration'] for s in SHOTS)}초")
    print(f"결과: {result_file}")
    print(f"프롬프트: {prompts_file}")


if __name__ == "__main__":
    asyncio.run(main())
