#!/usr/bin/env python3
"""
L1-L2-L3 파이프라인 실행 스크립트.

Story → [L1: SceneArchitect] → [L2: ShotComposer] → [L3: PromptBuilder] → Prompts
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

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(message)s')
from usecases.scene_architect import SceneArchitect, SceneArchitectInput
from usecases.shot_composer import LLMDirectComposer, TemplateBasedComposer, ShotComposerInput
from usecases.prompt_builder import PromptBuilder, PromptBuilderInput


# =============================================================================
# 입력 스토리 (루테란의 결의) - 트레일러 샷 리스트
# - 각 항목 = 1 샷 (L2 스킵, 바로 L3로)
# - 임팩트 위주, 긴장감 빌드업, 클라이맥스
# =============================================================================
STORY = """
[SHOT LIST - 각 항목이 하나의 독립된 샷. 빠른 컷 전환.]

SHOT 01 (2초) - EWS, 분위기
검은 화면. 천둥소리. 붉은 하늘이 서서히 드러난다.
아크라시아 대륙 전체가 불타고 있다. 연기와 화염.

SHOT 02 (2초) - EWS, 임팩트
하늘 가득 악마 군단. 수만 개의 검은 날개가 태양을 완전히 가린다.
화면이 어둠으로 뒤덮인다.

SHOT 03 (1초) - ECU, 임팩트
카제로스의 거대한 눈. 붉게 타오르는 동공. 화면을 가득 채운다.

SHOT 04 (2초) - EWS, 분위기
폐허가 된 도시. 무너진 성벽 사이로 연기가 피어오른다.
침묵. 바람 소리만.

SHOT 05 (1초) - WS, 전환
역광. 언덕 위 일곱 개의 실루엣. 망토가 바람에 휘날린다.
에스더의 등장.

SHOT 06 (1초) - CU, 캐릭터
아제나의 눈. 분노로 이글거린다. 눈물이 고여있다.

SHOT 07 (1초) - CU, 캐릭터
카단. 검을 천천히 뽑는다. 검날에서 섬광.

SHOT 08 (2초) - MS, 캐릭터
루테란. 석양빛이 금빛 갑옷을 붉게 물들인다.
천천히 고개를 든다. 결연한 눈빛.

SHOT 09 (1초) - ECU, 오브젝트
패자의 검. 검날 클로즈업. 금빛 룬 문자가 빛나기 시작한다.

SHOT 10 (2초) - MS → CU, 액션
루테란이 검을 하늘로 치켜든다.
검에서 황금빛 광채가 폭발한다!

SHOT 11 (2초) - WS, 액션
에스더 일곱 명이 일제히 무기를 든다.
각자의 아크 파워가 빛난다. 일곱 색의 빛이 하늘로 솟구친다.

SHOT 12 (2초) - EWS, 클라이맥스
에스더들이 악마 군단을 향해 돌격한다.
폭발. 마법. 검격. 화면 가득 카오스.

SHOT 13 (1초) - ECU, 엔딩
루테란의 눈. 결의에 찬 눈빛.
"여기가 끝이 아니다."

SHOT 14 (1초) - 블랙
페이드 투 블랙. 타이틀.
"""

CHARACTER_HINTS = [
    {
        "name": "루테란 (Luterra)",
        "role": "주인공, 에스더의 리더, 루테란 왕국의 건국왕",
        "description": "기사의 나라 루테란 왕국의 왕이자 에스더들의 리더. "
                       "금색 정교한 갑옷에 파란 망토, 사자 문양의 어깨 장식. "
                       "패자의 검(금빛으로 빛나는 대검)을 들고 있다. "
                       "짧은 검은 머리에 회색 가닥, 풍파를 겪은 얼굴, 결연한 눈빛. "
                       "내면: 세계의 진실을 아는 유일한 자. 500년의 희생을 감수하는 선택의 무게.",
        "emotion_arc": "고뇌 → 결의 → 희망"
    },
    {
        "name": "아제나 (Azena)",
        "role": "로헨델의 여왕, 마법사 전사",
        "description": "30대 여성 전사. 진홍색과 검정색 갑옷, 날카로운 각진 디자인. "
                       "등에 쌍검, 긴 검은 머리가 흩날림. "
                       "창백한 피부에 전투 흉터, 붉게 빛나는 강렬한 눈. "
                       "내면: 몽환군단에게 로헨델을 유린당한 트라우마. 악마에 대한 극도의 증오. "
                       "루테란에게만 마음을 연 폐쇄적 성격.",
        "emotion_arc": "분노/눈물 → 갈등 → 묵묵한 동의"
    },
    {
        "name": "카단 (Kadan)",
        "role": "가디언 슬레이어, 최강의 에스더",
        "description": "고귀한 남성 팔라딘 전사. 은백색 갑옷에 성스러운 문양. "
                       "등에 타워 실드, 짧은 은발을 뒤로 넘김. "
                       "차분하고 현명한 눈에 부드러운 금빛 광채. "
                       "내면: 루테란의 선택을 가장 잘 이해하는 자. '필연'이라 믿음. "
                       "무뚝뚝하고 말수 적지만 깊은 신뢰.",
        "emotion_arc": "관조 → 이해의 끄덕임 → 지지"
    }
]

GENRE = "epic fantasy"
TARGET_DURATION = 0.5  # 30초 (테스트용)


async def main():
    print("=" * 70)
    print("Tale Pipeline: L1 → L2 → L3")
    print("=" * 70)

    # 설정 로드
    settings = Settings()
    api_keys = settings.google_api_keys_list
    if not api_keys:
        print("Error: No Google API keys configured")
        return

    # 출력 디렉토리
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"pipeline_output/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 어댑터 초기화 (APIKeyPool로 자동 failover)
    key_infos = settings.google_api_key_infos  # alias 포함
    key_pool = APIKeyPool(
        keys=key_infos,
        strategy=RotationStrategy.ROUND_ROBIN,
        daily_limit=1500,  # Gemini API 무료 티어
        max_failures_per_key=3,
    )
    print(f"API Key Pool: {len(key_infos)}개 키 로드됨")
    for info in key_infos:
        print(f"  - [{info.alias}] {info.key[:12]}...")

    llm = GeminiLLMGateway(key_pool=key_pool, model="gemini-2.0-flash-lite")
    repo = FileAssetRepository(base_dir=output_dir)

    try:
        # =====================================================================
        # Level 1: Scene Architect
        # =====================================================================
        print("\n" + "=" * 70)
        print("[L1] Scene Architect")
        print("=" * 70)

        scene_architect = SceneArchitect(llm_gateway=llm, asset_repository=repo)

        l1_input = SceneArchitectInput(
            story=STORY,
            genre=GENRE,
            target_duration_minutes=TARGET_DURATION,
            character_hints=CHARACTER_HINTS,
        )

        print(f"입력 스토리: {len(STORY)}자")
        print(f"목표 길이: {TARGET_DURATION * 60}초")
        print("\n[실행 중...]")

        l1_output = await scene_architect.execute(l1_input)

        print(f"\n✓ 씬 {len(l1_output.scenes)}개 추출")
        print(f"✓ 캐릭터 {len(l1_output.characters)}개 정의")
        print(f"✓ 총 길이: {l1_output.total_duration_seconds}초")

        print("\n--- Scenes ---")
        for scene in l1_output.scenes:
            print(f"  [{scene.id}] {scene.scene_type.value} | {scene.duration.seconds}초 | {scene.narrative_summary[:50]}...")

        print("\n--- Characters ---")
        for char in l1_output.characters:
            print(f"  [{char.id}] {char.name} | {char.physical_description[:50]}...")

        # =====================================================================
        # Level 2: Shot Composer (LLM Direct)
        # =====================================================================
        print("\n" + "=" * 70)
        print("[L2] Shot Composer (LLM Direct)")
        print("=" * 70)

        shot_composer = LLMDirectComposer(llm_gateway=llm, asset_repository=repo)

        l2_input = ShotComposerInput(scenes=l1_output.scenes)

        print("\n[실행 중...]")

        l2_output = await shot_composer.execute(l2_input)

        total_shots = sum(len(shots) for shots in l2_output.shot_sequences.values())
        print(f"\n✓ 총 {total_shots}개 샷 생성")

        print("\n--- Shot Sequences ---")
        all_shots = []
        for scene_id, shots in l2_output.shot_sequences.items():
            print(f"\n  Scene: {scene_id}")
            for shot in shots:
                print(f"    [{shot.id}] {shot.shot_type.value} | {shot.duration.seconds}초 | {shot.purpose}")
                all_shots.append(shot)

        # =====================================================================
        # Level 3: Prompt Builder
        # =====================================================================
        print("\n" + "=" * 70)
        print("[L3] Prompt Builder")
        print("=" * 70)

        prompt_builder = PromptBuilder(asset_repository=repo)

        # 씬 컨텍스트 매핑
        scene_contexts = {
            scene.id: scene.narrative_summary
            for scene in l1_output.scenes
        }

        l3_input = PromptBuilderInput(
            shots=all_shots,
            characters=l1_output.characters,
            scene_contexts=scene_contexts,
            style_keywords=["Cinematic", "24fps film look", "Shallow depth of field"],
            negative_prompts=["CGI", "cartoon", "anime", "deformed"],
        )

        print("\n[실행 중...]")

        l3_output = await prompt_builder.execute(l3_input)

        print(f"\n✓ 총 {len(l3_output.prompts)}개 프롬프트 생성")

        print("\n--- Final Prompts ---")
        for prompt in l3_output.prompts:
            final_text = prompt.build()
            print(f"\n[{prompt.shot_id}]")
            print(f"  Type: {prompt.shot_type.value}")
            print(f"  Purpose: {prompt.purpose}")
            print(f"  Prompt ({len(final_text)}자):")
            print(f"    {final_text[:200]}...")

        # =====================================================================
        # 결과 저장
        # =====================================================================
        print("\n" + "=" * 70)
        print("결과 저장")
        print("=" * 70)

        # 전체 결과 JSON 저장
        result_summary = {
            "timestamp": timestamp,
            "story_length": len(STORY),
            "target_duration_seconds": TARGET_DURATION * 60,
            "actual_duration_seconds": l1_output.total_duration_seconds,
            "scenes": [
                {
                    "id": s.id,
                    "type": s.scene_type.value,
                    "duration": s.duration.seconds,
                    "narrative": s.narrative_summary,
                }
                for s in l1_output.scenes
            ],
            "characters": [
                {
                    "id": c.id,
                    "name": c.name,
                    "fixed_prompt": c.fixed_prompt,
                }
                for c in l1_output.characters
            ],
            "shots": [
                {
                    "id": shot.id,
                    "scene_id": shot.scene_id,
                    "type": shot.shot_type.value,
                    "duration": shot.duration.seconds,
                    "purpose": shot.purpose,
                }
                for shot in all_shots
            ],
            "prompts": [
                prompt.to_dict()
                for prompt in l3_output.prompts
            ],
        }

        summary_path = output_dir / "pipeline_result.json"
        summary_path.write_text(json.dumps(result_summary, indent=2, ensure_ascii=False))
        print(f"\n✓ 결과 저장: {summary_path}")

        # 프롬프트만 별도 저장 (복사해서 쓰기 편하게)
        prompts_path = output_dir / "prompts.txt"
        with prompts_path.open("w") as f:
            for prompt in l3_output.prompts:
                f.write(f"=== {prompt.shot_id} ===\n")
                f.write(prompt.build())
                f.write("\n\n")
        print(f"✓ 프롬프트 저장: {prompts_path}")

        print("\n" + "=" * 70)
        print("파이프라인 완료")
        print(f"출력 디렉토리: {output_dir}")
        print("=" * 70)

    finally:
        await llm.close()


if __name__ == "__main__":
    asyncio.run(main())
