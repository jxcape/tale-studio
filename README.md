# Tale Studio

AI Video Generation Pipeline using T2V (Text-to-Video) and I2V (Image-to-Video) APIs.

## Overview

Tale Studio transforms story text into video sequences through a 3-level architecture:

```
Story (text) → Scene Architect → Shot Composer → Prompt Builder → Video API → MP4
```

**Target**: 2-minute video = ~15 shots = 3-5 scenes

## Architecture

### 3-Level Pipeline

| Level | Component | Role |
|-------|-----------|------|
| L1 | Scene Architect | Story → Scenes, Characters, Locations |
| L2 | Shot Composer | Scene → Shot sequences, T2V/I2V decision |
| L3 | Prompt Builder | Shot → Final prompt with cinematography |

### Clean Architecture

```
tale/
├── domain/           # Entities & Value Objects (no dependencies)
├── usecases/         # Application logic & interfaces
├── adapters/         # External API implementations
├── infrastructure/   # Settings, CLI, utilities
└── tests/            # Unit & integration tests
```

## API Integration

| Purpose | API | Notes |
|---------|-----|-------|
| Video Generation | Google Veo | T2V and I2V (~8s per shot) |
| Image Generation | Google Imagen | Character references |
| LLM | Gemini / OpenAI | Scene analysis, prompt generation |

## Installation

```bash
# Clone
git clone git@github.com:jxcape/tale-studio.git
cd tale-studio

# Setup (using uv)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your API keys
```

## Usage

```bash
# Run pipeline
python scripts/run_pipeline.py --story "Your story text here"

# Run tests
pytest
```

## Configuration

Copy `.env.example` to `.env` and configure:

- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_API_KEYS` - Google Cloud API keys (comma-separated for rotation)
- `GOOGLE_PROJECT_ID` - GCP project ID
- `GOOGLE_LOCATION` - GCP region (e.g., us-central1)

## Key Concepts

### Terminology

| Term | Definition |
|------|------------|
| **Story** | Complete narrative (1 video project) |
| **Scene** | Continuous sequence at same time/place |
| **Shot** | Minimum generation unit = 1 API call = ~8s video |

### Consistency Strategy

- Multi-angle character references (front/side/3-quarter)
- Fixed prompts per character injected into all shots
- I2V for character shots, T2V for atmosphere/background

## Development

```bash
# Run tests with coverage
pytest --cov

# Lint
ruff check .

# Format
ruff format .
```

## Specs

- [Architecture](specs/architecture.md) - System design
- [MVP](specs/mvp.md) - MVP scope and decisions
- [Style Heuristics](specs/style_heuristics.md) - Visual style guidelines

## License

MIT
