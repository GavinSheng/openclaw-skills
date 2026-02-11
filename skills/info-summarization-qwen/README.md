# Qwen Info Summarization Skill

This skill uses Qwen3-Max to summarize, extract key points, and provide analysis of textual content.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables if needed:
```bash
export QWEN_API_KEY=your_api_key_here
export QWEN_MODEL=qwen3-max
```

## Usage

This skill can be invoked in multiple ways:

1. Summarize content:
```bash
python scripts/main.py --summarize "your text here" --length medium
```

2. Extract key points:
```bash
python scripts/main.py --extract "your text here" --max-points 5
```

3. Analyze content:
```bash
python scripts/main.py --analyze "your text here"
```

## Files

- `SKILL.md`: Contains skill definition and instructions for Claude
- `scripts/main.py`: Main execution script with core functionality
- `references/api_spec.md`: API specifications and usage guidelines
- `assets/config.json`: Configuration options for processing