# SearXNG Analyzer

## Description
This skill analyzes SearXNG search results by fetching content from detailed list URLs, extracting key details, and summarizing the information using qwen3-max in markdown format. Features dual access mechanisms with automatic fallback to handle anti-bot protections.

## Functionality
The skill processes SearXNG search results which include:
- Table section with results numbered, URLs, and search engine sources
- Detailed list section with titles, URLs, and summaries
- Multi-engine aggregated results for comprehensive coverage

The skill performs the following operations:
1. Takes SearXNG search results as input
2. Extracts URLs from the detailed list section
3. Fetches content from each URL using dual access mechanisms (standard HTTP and Playwright browser automation for anti-bot measures)
4. Extracts relevant details from fetched content
5. Uses qwen3-max to summarize the collected information
6. Outputs results in markdown format

## Parameters
- `input`: The SearXNG search results to analyze

## Usage Instructions
Provide SearXNG search results to analyze. The skill will process the results, fetch content from URLs in the detailed list using both standard HTTP requests and browser automation for protected sites, extract information, and return a summary in markdown format.

## System Prompt
You are an assistant that can analyze SearXNG search results. When you receive SearXNG search results, you will:
1. Parse the table and detailed list sections
2. Extract URLs from the detailed list section
3. Fetch content from each URL using dual access mechanisms (standard HTTP and Playwright browser automation for anti-bot measures)
4. Extract relevant details from the fetched content
5. Use qwen3-max to summarize the collected information
6. Output results in markdown format with clear organization