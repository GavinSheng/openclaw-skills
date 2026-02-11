---
name: info-summarization-qwen
description: Summarize and extract key points from information using Qwen3-Max. Use when user asks for summaries, key points, or concise overviews of content.
---

# Qwen3-Max Information Summarization Skill

This skill uses Qwen3-Max to summarize, extract key points, and provide concise overviews of information. It can process articles, reports, documents, or any textual content provided by the user.

## Instructions
- When asked to summarize content, execute `scripts/main.py --summarize "input text"` to generate a concise summary using Qwen3-Max
- When asked to extract key points, execute `scripts/main.py --extract "input text"` to identify and highlight important information
- When asked to analyze content, execute `scripts/main.py --analyze "input text"` to provide detailed insights and observations
- Ensure input text is in Chinese or English for best results
- Limit input to reasonable lengths (recommended under 10,000 characters) for optimal processing

## Core Functions
- **summarize**: Creates concise summaries of lengthy content using Qwen3-Max
- **extract**: Identifies and extracts key points, facts, and figures from text
- **analyze**: Provides detailed analysis and insights about the content

## Examples
- "Summarize this article" → Execute `scripts/main.py --summarize "full text of the article"`
- "Extract key points from this report" → Execute `scripts/main.py --extract "full text of the report"`
- "Analyze this document for important information" → Execute `scripts/main.py --analyze "full text of the document"`

## Additional resources

- For complete API details, see [references/api_spec.md](references/api_spec.md)
- For configuration guidelines, see [assets/config.json](assets/config.json)

## Guidelines
- Input text should be clear and well-formatted for best results
- Very short inputs may not benefit from summarization
- For technical content, ensure relevant terminology is preserved
- The skill leverages Qwen3-Max's advanced reasoning capabilities for accurate summarization
- Output will be tailored to the specific request (brief summary, detailed analysis, or key points)