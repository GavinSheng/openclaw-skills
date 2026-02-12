---
name: article-analyzer
description: Analyze individual articles in depth to generate suitable content for public account publishing. Extracts content from URLs and provides both summary (under 300 words) and detailed analysis parts, with proper formatting for social media publication. Use when users want to analyze and repurpose articles for public account posts.
---

# Article Analyzer Skill

This skill provides detailed analysis of individual articles to generate suitable content for public account (WeChat Official Account, etc.) publishing. It extracts content from URLs and provides both summary and detailed analysis parts.

## Instructions

- When asked to analyze an article for public account publication, execute `scripts/main.py --url "article_url"` to fetch and analyze the content
- The skill will provide both a summary (under 300 words) and detailed analysis
- The summary highlights core viewpoints and values for quick understanding
- The detailed analysis is organized in a publication-friendly format, avoiding direct copying
- Always verify the URLs are accessible before attempting to fetch content
- Format results appropriately for public account publishing

## Core Functions

- **article_analysis**: Fetches and analyzes individual articles, providing both summary and detailed analysis parts suitable for public account publication

## Examples

- "Analyze this article for our public account post" → Execute `scripts/main.py --url "https://example.com/article"`
- "Generate summary and detailed content from this article" → Execute `scripts/main.py --url "https://example.com/article"`
- "Prepare this article for WeChat public account" → Execute `scripts/main.py --url "https://example.com/article"`

## Additional resources

- For complete API details, see [references/api_spec.md](references/api_spec.md)
- For content formatting guidelines, see [assets/formatting_guide.json](assets/formatting_guide.json)

## Guidelines

- Only access publicly available articles
- Respect website robots.txt policies when fetching content
- Handle errors gracefully when websites are unavailable
- Ensure the summary stays under 300 words
- Format detailed analysis appropriately for public account publishing
- Avoid direct copying of original content; rephrase and summarize instead
- Focus on extracting the value and key points from articles
- The skill uses qwen3-max model for analysis and summary generation
- The final output is structured specifically for public account publication