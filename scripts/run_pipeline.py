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
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.settings import Settings
from adapters.gateways.gemini_llm import GeminiLLMGateway
from adapters.repositories.file_repository import FileAssetRepository
from usecases.scene_architect import SceneArchitect, SceneArchitectInput
from usecases.shot_composer import LLMDirectComposer, TemplateBasedComposer, ShotComposerInput
from usecases.prompt_builder import PromptBuilder, PromptBuilderInput


# =============================================================================
# 입력 스토리 (루테란의 결의)
# - 원작 로어 기반: 사슬전쟁 막바지, 카제로스 봉인 직전 에스더 회의
# - specs/lore/story_context.md 참조
# =============================================================================
STORY = """
사슬전쟁 막바지. 악마들의 침공으로 아크라시아는 폐허가 되었다.
심연의 군주 카제로스와 그의 6대 군단. 수만의 악마들.
인류는 절망의 끝에 서 있었다.

그때, 일곱 명의 영웅이 나타났다. 훗날 '에스더(찬란한 별)'라 불리게 될 이들.
그 중심에 루테란이 있었다.

폐허가 된 원형 석조 광장. 부서진 기둥들 사이로 횃불이 타오른다.
에스더들이 모여 있다. 마지막 작전을 논의하기 위해.

아제나가 먼저 입을 연다. 로헨델의 여왕, 진홍빛 갑옷의 전사.
그녀의 목소리에는 억누르지 못한 분노가 서려 있다.

"봉인? 봉인이라고?"

그녀의 눈에 눈물이 고인다. 분노의 눈물.
몽환군단에게 로헨델을 유린당한 기억. 기사단장들이 악마에게 장악당한 참상.
그 모든 것이 그녀의 목소리를 떨리게 한다.

"저 괴물들이 우리 백성을 얼마나 죽였는지 잊은 거야?"
아제나의 주먹이 떨린다.
"소멸시켜야 해. 완전히. 다시는 일어나지 못하도록."

루테란은 묵묵히 듣는다.
그의 어깨 위에 놓인 무게가 보이는 듯하다.
엘가시아에서 알게 된 진실. 아무에게도 말할 수 없는 비밀.
카제로스를 소멸시키면 더 큰 파멸이 온다는 것.

하지만 그것을 말할 수 없다. 미래가 바뀔 것이기에.

카단이 조용히 지켜본다. 은백색 갑옷의 가디언 슬레이어.
말없이 루테란을 바라보는 그의 눈에는 이해가 담겨 있다.
그는 알고 있었다. 루테란의 선택이 필연임을.

침묵이 흐른다.

루테란이 천천히 고개를 든다.
석양빛이 그의 금빛 갑옷을 붉게 물들인다.
패자의 검 - 에스더 갈라투르가 만들어준 전설의 무기.
그 검을 천천히 자신 앞에 세운다.

"우리들의 역할은 카제로스의 봉인으로 끝난다."

아제나가 숨을 멈춘다. 다른 에스더들도 루테란을 바라본다.

"500년 뒤, 새로운 빛이 올 것이다."
루테란의 눈에 결의가 깃든다.
"그때까지 우리가 버텨야 한다. 이것이 내 선택이다."

카단이 고개를 끄덕인다. 말없는 동의.
아제나는 이를 악문다. 하지만 그녀도 알고 있었다.
저 남자를 따르지 않을 수 없다는 것을.

루테란이 검을 하늘로 들어올린다.
검에서 금빛 광채가 퍼져나간다. 아크의 힘.

"여기가 끝이 아니다."

에스더들이 하나둘 그의 뒤에 선다.
카단이. 아제나가. 그리고 나머지 에스더들이.
부서진 깃발들이 바람에 나부끼고,
새로운 결의가 폐허 위에 피어난다.
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

    # 어댑터 초기화
    api_keys = settings.google_api_keys_list
    llm = GeminiLLMGateway(api_key=api_keys[-1], model="gemini-2.0-flash-lite")
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
