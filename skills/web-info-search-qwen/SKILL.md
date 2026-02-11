---
name: web-info-search-tongyi
description: Search the web for information using Tongyi search capabilities. Use when user asks for current information, wants to research a topic, or needs content from a URL.
---

# Tongyi Web Information Search Skill

This skill provides web search capabilities using Tongyi search features and allows fetching content from web pages. It includes two core functions: web_search (keyword search) and web_fetch (webpage content extraction).

## Instructions
- When asked to search for information online, execute `scripts/main.py --search "your query"` to perform keyword searches using Tongyi search capabilities
- When asked to get information from a specific URL, execute `scripts/main.py --fetch "URL"` to extract webpage content
- Always verify the URLs are accessible before attempting to fetch content
- Summarize search results or fetched content in a concise and informative manner
- Use appropriate search terms to find the most relevant information

## Core Functions
- **web_search**: Performs keyword-based searches across the web to find relevant information using Tongyi search capabilities
- **web_fetch**: Extracts content from specified webpages, including title, text, links, and images

## Examples
- "Search for the latest developments in AI technology" → Execute `scripts/main.py --search "latest AI technology"`
- "Get the content from https://example.com/article" → Execute `scripts/main.py --fetch "https://example.com/article"`
- "Find information about Python web scraping" → Execute `scripts/main.py --search "Python web scraping"`

## Additional resources

- For complete API details, see [references/api_spec.md](references/api_spec.md)
- For website crawling rules, see [assets/selector_rules.json](assets/selector_rules.json)

## Guidelines
- Only access publicly available websites
- Respect website robots.txt policies when fetching content
- Handle errors gracefully when websites are unavailable
- Do not fetch extremely large files or pages with excessive media content
- Always provide context about the source when sharing fetched content
- Focus on extracting the most relevant information from search results
- The skill implements fallback mechanisms using multiple search providers when primary search services have limitations