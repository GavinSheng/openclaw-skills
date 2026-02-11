# SearXNG Analyzer Skill - Specification

## Overview
The SearXNG Analyzer skill is designed to process SearXNG search results, extract URLs from the detailed list section, fetch content from those URLs, and then provide a summary using qwen3-max in markdown format.

## Input Format
The skill accepts raw SearXNG search results which typically include:
- A table section with columns: Result number, URL, and Engines (e.g., bing news, yahoo news, wikinews, startpage)
- A detailed list section with: Title, URL, and Summary for each result
- Multi-engine aggregated results for comprehensive coverage

## Processing Steps

### 1. URL Extraction
- Parse the SearXNG results to identify URLs in both table and detailed list sections
- Use regex patterns to extract all valid URLs from the text
- Clean URLs by removing trailing punctuation

### 2. Content Fetching
- Asynchronously fetch content from each extracted URL
- Implement timeout protection (default 10 seconds per URL)
- Handle errors gracefully when URLs cannot be accessed

### 3. Content Processing
- Collect all successfully fetched content
- Preserve error information for failed fetch attempts
- Structure the content for analysis

### 4. Summarization
- Use qwen3-max to analyze and summarize the collected content
- Generate a markdown-formatted output with clear organization
- Include information about sources and processing status

## Expected Output
The skill returns a JSON object with:
- `success`: Boolean indicating successful processing
- `original_results_length`: Character count of input
- `urls_found`: Number of URLs extracted from results
- `content_fetched`: Number of successful content fetches
- `errors`: Number of failed content fetches
- `summary`: Markdown-formatted summary of the analysis
- `processing_duration`: Time taken to process the request
- `model_used`: Model used for summarization

## Error Handling
- Network timeouts are handled with a default 10-second timeout
- Invalid URLs are skipped during extraction
- Failed content fetches are noted but don't halt processing
- Malformed SearXNG results are processed to the extent possible

## Performance Considerations
- Asynchronous URL fetching improves performance when processing multiple URLs
- Content is limited to prevent excessive processing time
- Processing time scales with the number of URLs to fetch