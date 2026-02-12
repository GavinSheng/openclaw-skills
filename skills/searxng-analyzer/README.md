# SearXNG Analyzer Skill

This skill analyzes SearXNG search results by fetching content from detailed list URLs, extracting details, and summarizing using qwen3-max in markdown format. Features dual access mechanisms with automatic fallback to handle anti-bot protections.

## Installation

```bash
pip install -r requirements.txt
playwright install
```

## Configuration

Set environment variables if needed:
```bash
export QWEN_API_KEY=your_api_key_here
export QWEN_MODEL=qwen3-max
```

## Usage

This skill can be invoked to analyze SearXNG search results:

```bash
python scripts/main.py --analyze "SearXNG search results here..."
```

The skill will:
1. Parse the SearXNG search results
2. Extract URLs from the detailed list section
3. Fetch content from each URL using dual access mechanisms (HTTP and Playwright browser automation)
4. Extract relevant details from the fetched content
5. Use qwen3-max to summarize the collected information
6. Output results in markdown format

## Features

- Extracts and analyzes content from multiple URLs in SearXNG search results
- Automatically handles anti-bot measures using dual access methods:
  - Standard HTTP requests (primary method)
  - Playwright browser automation (fallback for protected sites)
- Built-in error handling and retry mechanisms
- Efficient concurrent fetching of multiple URLs
- Comprehensive error reporting

## Files

- `SKILL.md`: Contains skill definition and instructions for Claude
- `scripts/main.py`: Main execution script with core functionality
- `references/specification.md`: Specification and usage guidelines
- `assets/config.json`: Configuration options for processing