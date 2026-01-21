"""
Pytest configuration and shared fixtures.
"""
import pytest


@pytest.fixture
def sample_story() -> str:
    """Sample story input for testing."""
    return """
    외로운 AI 연구원 Dr. Kim은 자신이 만든 AI와 대화하며
    점점 인간성에 대해 깊이 고민하게 된다.
    결국 AI를 통해 자신의 진정한 감정을 발견한다.
    """


@pytest.fixture
def sample_character_definition() -> dict:
    """Sample character definition for testing."""
    return {
        "id": "protagonist",
        "name": "Dr. Kim",
        "age": 45,
        "gender": "male",
        "physical_description": "Asian male, tired eyes, slight stubble",
        "outfit": "wrinkled white lab coat, loosened tie",
        "face_details": "round glasses, deep eye bags, contemplative expression",
    }
