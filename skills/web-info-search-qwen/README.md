# Tongyi Web Info Search Skill

This skill provides web search capabilities using Tongyi search features and allows fetching content from web pages.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables if needed:
```bash
export HTTPS_PROXY=http://your-proxy:port
export HTTP_PROXY=http://your-proxy:port
```

## Usage

This skill can be invoked in two ways:

1. Search the web:
```bash
python scripts/main.py --search "your query" --num-results 10
```

2. Fetch web content:
```bash
python scripts/main.py --fetch "https://example.com/page"
```

## Files

- `SKILL.md`: Contains skill definition and instructions for Claude
- `scripts/main.py`: Main execution script with core functionality
- `references/api_spec.md`: API specifications and usage guidelines
- `assets/selector_rules.json`: Website-specific parsing rules