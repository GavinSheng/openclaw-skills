# Web Info Search Skill

This skill provides web search capabilities and allows fetching content from web pages. Features dual access mechanisms with automatic fallback to handle anti-bot protections.

## Installation

```bash
pip install -r requirements.txt
playwright install
```

## Configuration

Set environment variables if needed:
```bash
export WEB_SEARCH_TIMEOUT=30
export WEB_FETCH_DELAY=1000
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

## Features

- **Web Search**: Multi-provider search with fallbacks (DuckDuckGo, Bing, Baidu)
- **Content Fetching**: Advanced content extraction with dual access mechanisms:
  - Standard HTTP requests (primary method)
  - Playwright browser automation (fallback for protected sites)
- **Anti-Bot Protection**: Automatic detection and bypass of common anti-bot measures
- **Content Processing**: Smart extraction of article content, removal of navigation and ads
- **Regional Optimization**: Support for different search engines based on region

## Files

- `SKILL.md`: Contains skill definition and instructions for Claude
- `scripts/main.py`: Main execution script with core functionality
- `references/api_spec.md`: API specifications and usage guidelines
- `assets/selector_rules.json`: Website-specific parsing rules