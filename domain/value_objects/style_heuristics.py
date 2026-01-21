"""
Style Heuristics v2 - Game Cinematic Style Definitions.

분석 소스: Lost Ark, Diablo IV, World of Warcraft
각 스타일의 시각적 특성을 상세하게 정의.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StyleType(Enum):
    """지원하는 스타일 타입."""
    GAME_CINEMATIC = "game_cinematic"
    DIABLO_DARK = "diablo_dark"
    LOST_ARK_FANTASY = "lost_ark_fantasy"
    WOW_EPIC = "wow_epic"


class SkinDetailLevel(Enum):
    """피부 디테일 레벨."""
    L1_PORES = "visible pores on nose, cheeks, and forehead"
    L2_WRINKLES = "fine wrinkles around eyes, forehead lines, expression creases"
    L3_SCARS = "battle scars, healed cuts, old wounds"
    L4_SURFACE = "dirt-covered, sweat droplets, blood splatter, ash"
    L5_SUBSURFACE = "visible veins, bruise discoloration, fatigue shadows"


class MetalType(Enum):
    """금속 타입."""
    POLISHED_STEEL = "polished steel with mirror-like reflections"
    MATTE_STEEL = "brushed steel with matte finish"
    DARK_GUNMETAL = "dark gunmetal with blue-gray undertones"
    GOLD_PLATED = "ornate gold plating with warm reflections"
    CORRODED = "corroded metal with rust patches and verdigris"
    BLACKENED_IRON = "blackened forge-darkened iron"


class LightingMood(Enum):
    """조명 분위기."""
    HEROIC = "heroic"
    DARK = "dark"
    DIVINE = "divine"
    SINISTER = "sinister"
    MYSTERIOUS = "mysterious"


@dataclass(frozen=True)
class SkinTextureSpec:
    """피부 텍스처 상세 명세 (v2)."""

    # 표면 디테일
    detail_level: str = "L1-L4"
    pores: str = "visible pores on nose, cheeks, forehead with realistic depth"
    wrinkles: str = "fine wrinkles around eyes, forehead lines, nasolabial folds"
    imperfections: str = "battle scars, healed cuts, bruising, dirt accumulation"
    surface_contamination: str = "dust-covered, sweat beads, dried blood, ash particles"

    # SSS (Subsurface Scattering)
    sss_areas: str = "ears, nose tip, fingertips showing warm red translucency when backlit"
    sss_color: str = "blood-red undertone, warm orange glow"
    sss_intensity: str = "strong on thin areas with direct backlight"

    # 조명 반응
    specular: str = "oily skin highlights on forehead, nose bridge, cheekbones"
    diffuse: str = "soft shadow gradients, no harsh edges on skin"
    rim: str = "bright rim light tracing jaw, ear contours, hair edges"

    def to_prompt(self, detail_level: str = "high") -> str:
        """프롬프트로 변환."""
        if detail_level == "extreme":
            return (
                f"Hyperrealistic skin with {self.pores}, {self.wrinkles}. "
                f"Surface showing {self.surface_contamination}. "
                f"Subsurface scattering: {self.sss_areas}, {self.sss_color}. "
                f"Lighting response: {self.specular}, {self.rim}."
            )
        elif detail_level == "high":
            return (
                f"Realistic skin with visible pores and fine texture. "
                f"{self.imperfections}. "
                f"Warm SSS glow on ears and thin skin areas. "
                f"{self.specular}, {self.rim}."
            )
        else:
            return f"Detailed skin texture with {self.rim}."


@dataclass(frozen=True)
class MetalTextureSpec:
    """금속 텍스처 상세 명세 (v2)."""

    # 기본 속성
    primary_type: str = "dark gunmetal steel with subtle blue-gray undertones"
    secondary_type: str = "gold/brass ornamental details with warm reflections"

    # 마모/손상
    wear_level: str = "battle-worn with micro-scratches and edge wear"
    damage: str = "dents from impacts, deep gouges, blade marks"
    environmental: str = "dust accumulation in crevices, dried blood in grooves"

    # 장식
    ornaments: str = "intricate engravings, embedded gems, fine chainmail at joints"

    # 반사 특성
    reflection: str = "strong specular highlights, environment reflections on curved surfaces"
    roughness: str = "varying roughness - polished on raised areas, matte in recesses"

    def to_prompt(self, wear: str = "battle-worn") -> str:
        """프롬프트로 변환."""
        if wear == "pristine":
            return (
                f"Pristine armor with {self.primary_type}. "
                f"Mirror-like reflections, {self.secondary_type}. "
                f"{self.ornaments}."
            )
        elif wear == "battle-worn":
            return (
                f"Battle-worn armor: {self.primary_type}. "
                f"{self.wear_level}, {self.damage}. "
                f"{self.environmental}. "
                f"{self.ornaments}. "
                f"{self.reflection}."
            )
        else:  # destroyed
            return (
                f"Heavily damaged armor with deep cracks and missing pieces. "
                f"Corroded metal, rust patches. "
                f"Broken ornaments, shattered gems."
            )


@dataclass(frozen=True)
class LightingSpec:
    """조명 상세 명세 (v2)."""

    # 키 라이트
    key_position: str = "45 degrees front-right, above eye level"
    key_color_warm: str = "warm gold (#FFD700)"
    key_color_cool: str = "cool steel blue (#A0C4FF)"
    key_intensity: str = "medium, dramatic contrast with deep shadows"

    # 림 라이트
    rim_position: str = "150 degrees back-left, strong separation"
    rim_color: str = "cyan (#00FFFF) or pure white"
    rim_intensity: str = "high, stronger than key for heroic silhouette"

    # 필 라이트
    fill_ratio: str = "1:8 to 1:16, minimal fill for drama"

    # 대기 조명
    volumetric_godrays: str = "god rays piercing through parting clouds, visible light shafts"
    volumetric_fog: str = "low-lying fog catching and scattering light beams"
    volumetric_dust: str = "dust motes floating in light shafts, catching backlight"

    # 조명 테크닉
    technique_rembrandt: str = "triangle highlight on opposite cheek, deep shadows"
    technique_split: str = "half face in shadow, extreme drama"
    technique_silhouette: str = "complete silhouette with bright backlight only"
    technique_rim_emphasis: str = "strong rim outlining figure against dark background"

    def to_prompt(self, mood: LightingMood = LightingMood.HEROIC) -> str:
        """분위기에 맞는 조명 프롬프트."""
        if mood == LightingMood.HEROIC:
            return (
                f"Dramatic heroic lighting: Key light {self.key_color_warm}, {self.key_position}. "
                f"Strong rim light {self.rim_color}, {self.rim_intensity}. "
                f"Atmosphere: {self.volumetric_godrays}, {self.volumetric_dust}. "
                f"Deep shadows with {self.fill_ratio} fill."
            )
        elif mood == LightingMood.DARK:
            return (
                f"Dark ominous lighting: Minimal key light {self.key_color_cool}, 90 degrees side. "
                f"Almost no fill, crushed blacks. "
                f"Faint rim light for separation. "
                f"Atmosphere: {self.volumetric_fog}, obscuring details."
            )
        elif mood == LightingMood.DIVINE:
            return (
                f"Divine celestial lighting: Overhead key light, pure white/gold. "
                f"Soft heavenly glow, halo effect. "
                f"{self.volumetric_godrays} descending from above. "
                f"Bloom on all light sources."
            )
        elif mood == LightingMood.SINISTER:
            return (
                f"Sinister underlighting: Key from below, red/orange tint. "
                f"Harsh shadows cast upward on face. "
                f"Red rim light, demonic glow. "
                f"Dark purple atmospheric haze."
            )
        else:  # MYSTERIOUS
            return (
                f"Mysterious backlighting: Strong backlight only. "
                f"{self.technique_silhouette}. "
                f"Teal/cyan atmospheric glow. "
                f"Face details obscured, only edges visible."
            )


@dataclass(frozen=True)
class ColorSpec:
    """색상 상세 명세 (v2)."""

    # Diablo 팔레트 (어둡고 호러틱)
    diablo_base: str = "#0A0A0A"
    diablo_shadow: str = "#1A1A1A"
    diablo_midtone: str = "#3A3A3A"
    diablo_accent_warm: str = "#CC4400"
    diablo_accent_cool: str = "#4488AA"

    # Lost Ark 팔레트 (하이 판타지)
    lostark_base: str = "#0A0A1F"
    lostark_shadow: str = "#1A1A2F"
    lostark_magic_blue: str = "#0066FF"
    lostark_magic_purple: str = "#9933FF"
    lostark_gold: str = "#FFD700"
    lostark_cyan: str = "#00FFFF"

    # WoW 팔레트 (화려한 판타지)
    wow_base: str = "#151525"
    wow_arcane: str = "#AA66FF"
    wow_holy: str = "#FFD700"
    wow_fel: str = "#66FF00"

    # 그레이딩
    shadow_tint: str = "blue/teal (#001122) pushed into shadows"
    midtone_desat: str = "-20% to -30% saturation, muted but not gray"
    highlight_bloom: str = "overexposed highlights with color-matched bloom"
    contrast: str = "high S-curve contrast, crushed blacks, preserved skin tones"

    def to_prompt(self, style: str = "lost_ark") -> str:
        """스타일에 맞는 색상 프롬프트."""
        if style == "diablo":
            return (
                f"Color palette: Near-black base ({self.diablo_base}), "
                f"warm fire accents ({self.diablo_accent_warm}), "
                f"cool death tones ({self.diablo_accent_cool}). "
                f"Extreme desaturation except blood and fire. "
                f"Crushed blacks, minimal midtones."
            )
        elif style == "wow":
            return (
                f"Color palette: Deep purple base ({self.wow_base}), "
                f"arcane purple ({self.wow_arcane}), holy gold ({self.wow_holy}). "
                f"Vibrant magical colors against dark background. "
                f"Rich saturation on magic effects."
            )
        else:  # lost_ark
            return (
                f"Color palette: Deep blue-black base ({self.lostark_base}), "
                f"magic blue ({self.lostark_magic_blue}), gold accents ({self.lostark_gold}). "
                f"Cyan rim lights ({self.lostark_cyan}). "
                f"Grading: {self.shadow_tint}, {self.midtone_desat}, {self.contrast}."
            )


@dataclass(frozen=True)
class CameraSpec:
    """카메라 상세 명세 (v2)."""

    # 앵글
    angle_low_hero: str = "15 degrees below eye level, looking up, emphasizing heroic stature"
    angle_high_scale: str = "30 degrees above, looking down, showing scale and vulnerability"
    angle_dutch: str = "10-25 degree tilt, tension and disorientation"
    angle_eye_level: str = "neutral intimate connection, dialogue and emotion"

    # 움직임
    move_creep: str = "imperceptibly slow push-in, 0.5% per second, building tension"
    move_boom_up: str = "vertical rise revealing vast environment below"
    move_orbit: str = "slow 120-180 degree arc around subject, showcasing hero"
    move_whip_pan: str = "rapid horizontal pan with motion blur streak"
    move_dolly_zoom: str = "zoom in while pulling back, vertigo effect"

    # 심도
    dof_extreme_closeup: str = "f/1.2-f/1.8, millimeter focus, single eye sharp"
    dof_closeup: str = "f/1.8-f/2.8, both eyes sharp, ears soft"
    dof_medium: str = "f/2.8-f/4, full upper body sharp, background soft bokeh"
    dof_wide: str = "f/5.6-f/8, environment context, slight background softness"

    # 구도 패턴
    comp_overwhelming_scale: str = "tiny figure dwarfed by massive threat, 80% frame is threat"
    comp_heroic_closeup: str = "face filling 60-80% frame, slight low angle, bokeh background"
    comp_confrontation: str = "opposing forces on each side, tension in center"
    comp_divine_descent: str = "light descending from above, character bathed in glow"

    def to_prompt(
        self,
        angle: str = "low_hero",
        movement: str = "creep",
        dof: str = "closeup"
    ) -> str:
        """카메라 프롬프트."""
        angle_desc = getattr(self, f"angle_{angle}", self.angle_low_hero)
        move_desc = getattr(self, f"move_{movement}", self.move_creep)
        dof_desc = getattr(self, f"dof_{dof}", self.dof_closeup)

        return (
            f"Camera angle: {angle_desc}. "
            f"Movement: {move_desc}. "
            f"Depth of field: {dof_desc}."
        )


@dataclass(frozen=True)
class VFXSpec:
    """VFX 상세 명세 (v2)."""

    # 파티클 - 상시
    particle_dust: str = "floating dust motes catching backlight, 10-20 per sqm"
    particle_ash: str = "glowing embers and gray ash rising in heat currents"
    particle_magic: str = "ethereal wisps orbiting character, self-illuminated"

    # 파티클 - 이벤트
    particle_debris: str = "stone and metal chunks with realistic physics trajectories"
    particle_sparks: str = "shower of bright orange/white sparks from metal impacts"
    particle_blood: str = "stylized dark blood droplets, emphasized in slow motion"

    # 마법 효과 구조
    magic_core: str = "overexposed white/cyan center, blown out"
    magic_inner_glow: str = "bright saturated color surrounding core"
    magic_outer_aura: str = "main color fading to transparent at edges"
    magic_particles: str = "tiny sparks orbiting the effect"

    # 포스트 프로세싱
    post_bloom: str = "medium-high bloom on light sources, color-matched"
    post_chromatic: str = "subtle 0.1-0.3% chromatic aberration at frame edges"
    post_vignette: str = "gentle 15-20% vignette darkening corners"
    post_grain: str = "subtle 2-4% film grain adding texture"
    post_motion_blur: str = "cinematic 180 degree shutter motion blur"

    def to_prompt(self, intensity: str = "high") -> str:
        """VFX 프롬프트."""
        if intensity == "extreme":
            return (
                f"Particles: {self.particle_dust}, {self.particle_ash}, {self.particle_magic}. "
                f"Magic effects: {self.magic_core}, {self.magic_inner_glow}, "
                f"{self.magic_outer_aura}, {self.magic_particles}. "
                f"Post: {self.post_bloom}, {self.post_chromatic}, "
                f"{self.post_vignette}, {self.post_motion_blur}."
            )
        elif intensity == "high":
            return (
                f"Particles: {self.particle_dust}, {self.particle_ash}. "
                f"Magic: glowing core with bloom bleeding outward, orbiting sparks. "
                f"Post: {self.post_bloom}, {self.post_vignette}, {self.post_grain}."
            )
        else:
            return f"Subtle particles: dust motes in light. Post: light bloom, vignette."


@dataclass(frozen=True)
class MotionSpec:
    """모션 상세 명세 (v2)."""

    # 속도
    speed_normal: str = "24fps realistic timing"
    speed_slowmo: str = "120fps overcranked, emotional impact moments"
    speed_ramp: str = "normal to slow at impact, then back to normal"

    # 무게감
    weight_heavy_armor: str = "slow acceleration, momentum carry-through, settling time"
    weight_weapon: str = "swing pulling entire body, recovery time"
    weight_cape: str = "trailing behind movement, secondary animation"

    # 애니메이션 원칙
    anticipation: str = "wind-up before major actions, weight shift, eyes lead body"
    follow_through: str = "hair/cape continue after body stops, gradual settling"
    secondary: str = "ornaments sway, fabric ripples, hair strands move independently"

    # 환경
    env_constant: str = "wind affecting flags/capes/hair, drifting smoke, floating debris"
    env_triggered: str = "ground cracks on impact, shockwave ripples, debris spray"

    def to_prompt(self, action_type: str = "heroic") -> str:
        """모션 프롬프트."""
        if action_type == "slow_dramatic":
            return (
                f"Motion: {self.speed_slowmo}. "
                f"Weight: {self.weight_heavy_armor}. "
                f"{self.follow_through}. "
                f"Environment: {self.env_constant}."
            )
        elif action_type == "action":
            return (
                f"Motion: {self.speed_ramp}. "
                f"{self.anticipation}. "
                f"Weight: {self.weight_weapon}. "
                f"Environment: {self.env_triggered}."
            )
        else:  # heroic
            return (
                f"Motion: deliberate slow movement, {self.weight_heavy_armor}. "
                f"{self.anticipation}, {self.follow_through}. "
                f"Secondary: {self.secondary}. "
                f"Environment: {self.env_constant}."
            )


@dataclass
class StyleHeuristics:
    """
    스타일 휴리스틱 v2 통합 클래스.

    게임 시네마틱의 모든 시각적 특성을 포함.
    """

    style_type: StyleType
    skin: SkinTextureSpec = field(default_factory=SkinTextureSpec)
    metal: MetalTextureSpec = field(default_factory=MetalTextureSpec)
    lighting: LightingSpec = field(default_factory=LightingSpec)
    color: ColorSpec = field(default_factory=ColorSpec)
    camera: CameraSpec = field(default_factory=CameraSpec)
    vfx: VFXSpec = field(default_factory=VFXSpec)
    motion: MotionSpec = field(default_factory=MotionSpec)

    # 메타데이터
    reference_works: list[str] = field(default_factory=list)
    quality_keywords: list[str] = field(default_factory=list)

    @classmethod
    def game_cinematic(cls) -> "StyleHeuristics":
        """게임 시네마틱 스타일 프리셋 (Lost Ark 기반)."""
        return cls(
            style_type=StyleType.GAME_CINEMATIC,
            reference_works=[
                "Lost Ark cinematics by Smilegate",
                "Diablo IV cinematics by Blizzard",
                "World of Warcraft cinematics",
            ],
            quality_keywords=[
                "Unreal Engine 5 photorealistic rendering",
                "Blur Studio cinematic quality",
                "AAA game cinematic",
                "24fps with cinematic motion blur",
                "photorealistic skin and metal textures",
            ],
        )

    @classmethod
    def diablo_dark(cls) -> "StyleHeuristics":
        """Diablo 스타일 (어둡고 호러틱)."""
        return cls(
            style_type=StyleType.DIABLO_DARK,
            reference_works=[
                "Diablo IV announcement cinematic",
                "Diablo IV Vessel of Hatred",
            ],
            quality_keywords=[
                "Blizzard cinematic quality",
                "photorealistic horror",
                "extreme darkness",
                "near-black color palette",
                "visceral detail",
            ],
        )

    def build_full_prompt(
        self,
        scene_description: str,
        mood: str = "heroic",
        skin_detail: str = "high",
        metal_wear: str = "battle-worn",
        camera_angle: str = "low_hero",
        camera_movement: str = "creep",
        dof: str = "closeup",
        action_type: str = "heroic",
        vfx_intensity: str = "high",
        color_style: str = "lost_ark",
    ) -> str:
        """완전한 프롬프트 생성."""

        lighting_mood = LightingMood[mood.upper()] if mood.upper() in LightingMood.__members__ else LightingMood.HEROIC

        sections = [
            f"[SCENE]\n{scene_description}",
            f"[SKIN TEXTURE]\n{self.skin.to_prompt(skin_detail)}",
            f"[METAL TEXTURE]\n{self.metal.to_prompt(metal_wear)}",
            f"[LIGHTING]\n{self.lighting.to_prompt(lighting_mood)}",
            f"[COLOR]\n{self.color.to_prompt(color_style)}",
            f"[CAMERA]\n{self.camera.to_prompt(camera_angle, camera_movement, dof)}",
            f"[VFX]\n{self.vfx.to_prompt(vfx_intensity)}",
            f"[MOTION]\n{self.motion.to_prompt(action_type)}",
            f"[STYLE]\nQuality: {', '.join(self.quality_keywords[:3])}. Reference: {', '.join(self.reference_works[:2])}.",
        ]

        return "\n\n".join(sections)

    def build_veo_prompt(
        self,
        scene_description: str,
        mood: str = "heroic",
        color_style: str = "lost_ark",
    ) -> str:
        """Veo API용 컴팩트 프롬프트."""

        lighting_mood = LightingMood[mood.upper()] if mood.upper() in LightingMood.__members__ else LightingMood.HEROIC

        return f"""Cinematic {mood} shot. {scene_description}

{self.lighting.to_prompt(lighting_mood)}

{self.color.to_prompt(color_style)}

{self.motion.to_prompt("slow_dramatic")}

{self.vfx.to_prompt("high")}

Style: {', '.join(self.quality_keywords[:3])}. Reference: {self.reference_works[0]}."""

    def get_negative_prompt(self) -> str:
        """네거티브 프롬프트."""
        return (
            "cartoon style, anime style, low quality, blurry, "
            "fast jerky movements, modern elements, UI text, "
            "oversaturated colors, flat lighting, plastic skin, "
            "visible camera rig, lens distortion, chromatic aberration, "
            "uncanny valley, stiff animation, floating objects"
        )
