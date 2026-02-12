#!/usr/bin/env python3
"""
SearXNG Analyzer Skill - Main Execution Script

Analyzes SearXNG search results by fetching content from detailed list URLs,
extracting details, and summarizing using qwen3-max in markdown format.
This script is meant to be executed directly by Claude.
Supports both standard HTTP requests and Playwright browser automation for anti-anti-spider purposes.
"""

import argparse
import asyncio
import json
import sys
import re
import os
from typing import Dict, Any, List
import httpx
import time


async def fetch_url_content_http(url: str, timeout: int = 10) -> str:
    """
    Fetch content from a URL using standard HTTP requests.

    Args:
        url: URL to fetch content from
        timeout: Request timeout in seconds

    Returns:
        Fetched content as string, or error message
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Google Chrome";v="91", "Chromium";v="91", ";Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=timeout)) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


async def fetch_url_content_playwright(url: str, timeout: int = 30) -> str:
    """
    Fetch content from a URL using Playwright browser automation.
    This method can handle JavaScript-rendered content and anti-bot measures.

    Args:
        url: URL to fetch content from
        timeout: Request timeout in seconds

    Returns:
        Fetched content as string, or error message
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            # Launch browser with stealth options
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-images",  # Optionally disable images for faster loading
                ]
            )

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "Sec-Ch-Ua": '"Google Chrome";v="91", "Chromium";v="91", ";Not-A.Brand";v="99"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Upgrade-Insecure-Requests": "1",
                },
                java_script_enabled=True,  # Enable JavaScript as many sites require it
                bypass_csp=True
            )

            page = await context.new_page()

            # Navigate to the page
            await page.goto(url, wait_until="networkidle", timeout=timeout*1000)

            # Wait for page to load and execute JavaScript
            await page.wait_for_timeout(2000)  # Wait additional time for dynamic content

            # Get page content after JavaScript execution
            content = await page.content()

            # Close browser
            await browser.close()

            return content

    except ImportError:
        return f"Error fetching {url}: Playwright is not installed. Install with 'pip install playwright' and run 'playwright install'"
    except Exception as e:
        return f"Error fetching {url} with Playwright: {str(e)}"


async def fetch_url_content(url: str, timeout: int = 10) -> str:
    """
    Fetch content from a URL with fallback from HTTP to Playwright methods.
    """
    # First try with standard HTTP
    content = await fetch_url_content_http(url, timeout)

    # Check if the result indicates an error that might be due to anti-bot measures
    error_indicators = ["401", "403", "406", "429", "anti-bot", "robot", "captcha", "datadome", "cloudfront", "Access Denied", "Forbidden"]
    if isinstance(content, str) and any(indicator in content.lower() or indicator in str(url).lower() for indicator in error_indicators):
        print(f"Standard HTTP request failed for {url}, trying with Playwright browser automation...")
        content = await fetch_url_content_playwright(url, timeout)
    elif content.startswith("Error"):
        # If HTTP fails completely, try Playwright anyway
        print(f"Standard HTTP request failed for {url}, falling back to Playwright browser automation...")
        content = await fetch_url_content_playwright(url, timeout)

    return content


def extract_urls_from_searxng_results(searxng_text: str) -> List[str]:
    """
    Extract URLs from SearXNG search results.
    SearXNG results typically contain URLs in both table and detailed list sections.

    Args:
        searxng_text: Raw SearXNG search results text

    Returns:
        List of extracted URLs
    """
    urls = set()

    # Look for URLs in the detailed list section (typically after titles)
    # Common patterns in SearXNG results:
    # - Lines that look like URLs
    # - URLs following titles or descriptions
    url_pattern = r'https?://[^\s"\'<>|]+(?:/[^\s"\'<>|]*)?'
    found_urls = re.findall(url_pattern, searxng_text)

    for url in found_urls:
        # Clean up the URL if it has trailing punctuation
        clean_url = re.sub(r'[.,;:!?]+$', '', url)
        urls.add(clean_url)

    # Also look for common SearXNG result patterns
    # Pattern: Title followed by URL
    title_url_pattern = r'(?:^|\n)[^\n]*?\n(https?://[^\s"\'<>|]+)'
    title_urls = re.findall(title_url_pattern, searxng_text, re.MULTILINE)
    for url in title_urls:
        clean_url = re.sub(r'[.,;:!?]+$', '', url)
        urls.add(clean_url)

    return list(urls)


def call_qwen_summarization(content_list: List[Dict[str, str]], original_results: str, context: Any) -> str:
    """
    Call qwen3-max for summarization of the collected content using the context.llm API.

    Args:
        content_list: List of dictionaries containing URL and fetched content
        original_results: Original SearXNG search results for context
        context: Context object containing the LLM API interface

    Returns:
        Markdown-formatted summary of the content in Chinese
    """
    import time
    start_time = time.time()

    # Prepare content for summarization
    formatted_content = ""
    for i, item in enumerate(content_list, 1):
        url = item.get("url", "Unknown URL")
        content = item.get("content", "")

        if content.startswith("Error"):
            formatted_content += f"Source {i} ({url}): Failed to fetch content: {content}\n\n"
        else:
            # Extract a brief snippet from the content to avoid exceeding token limits
            snippet = content[:2000] + "..." if len(content) > 2000 else content
            formatted_content += f"Source {i} ({url}):\n{snippet}\n\n"

    # Create a prompt for the LLM that explicitly requests Chinese output
    prompt = f"""请分析以下来自SearXNG搜索结果的内容，并生成一个结构化的Markdown格式摘要。请注意，无论原始内容是何种语言，请务必使用中文进行回答：

原始SearXNG搜索结果：
{original_results}

---

收集到的内容：
{formatted_content}

---

请按以下格式返回分析结果：
# SearXNG 搜索结果分析

## 来源摘要
[对来源数量、类型、质量的整体概述]

## 关键发现
[提取的关键信息点，按重要性排序]

## 内容概览
[对各来源内容的简要总结]

## 相关性评估
[评估内容与原始搜索请求的相关性]

## 总体分析
[综合分析结论]
"""

    try:
        # Call the LLM for summarization using the MoltBot standard interface
        response = context.llm.generate(
            prompt=prompt,
            model="qwen3-max-2026-01-23",  # 使用完整模型 ID
            temperature=0.3,
            max_tokens=2000
        )

        if response is None:
            return "# 错误\n\n大语言模型调用失败：模型返回了空响应。请检查模型服务是否正常运行。"

        return response

    except Exception as e:
        error_msg = f"# 错误\n\n大语言模型调用失败：{str(e)}\n\n请检查：\n- 模型服务是否正常运行\n- 模型ID是否正确\n- API密钥是否有效\n- 网络连接是否正常"
        return error_msg


async def analyze_searxng_results(searxng_results: str, context: Any) -> Dict[str, Any]:
    """
    Analyze SearXNG search results by fetching content from URLs and summarizing.

    Args:
        searxng_results: Raw SearXNG search results text
        context: Context object containing the LLM API interface

    Returns:
        Dictionary containing analysis results
    """
    import time
    start_time = time.time()

    # Extract URLs from the SearXNG results
    urls = extract_urls_from_searxng_results(searxng_results)

    # Fetch content from each URL
    content_tasks = []
    for url in urls:
        content_tasks.append(fetch_url_content(url))

    fetched_contents = await asyncio.gather(*content_tasks)

    # Prepare content list for summarization
    content_list = []
    for url, content in zip(urls, fetched_contents):
        content_list.append({
            "url": url,
            "content": content
        })

    # Call the actual qwen summarization
    markdown_summary = call_qwen_summarization(content_list, searxng_results, context)

    duration = time.time() - start_time

    return {
        "success": True,
        "original_results_length": len(searxng_results),
        "urls_found": len(urls),
        "content_fetched": len([c for c in content_list if not c['content'].startswith("Error")]),
        "errors": len([c for c in content_list if c['content'].startswith("Error")]),
        "summary": markdown_summary,
        "processing_duration": duration,
        "model_used": "qwen3-max"
    }


def handler(request, context):
    """
    MoltBot platform compatible handler for analyzing SearXNG search results

    Args:
        request: Request dictionary containing the input
        context: Context object containing the LLM API interface

    Returns:
        Dictionary containing analysis results
    """
    searxng_results = request.get("document", "") or request.get("input", "")

    if not searxng_results:
        return {
            "success": False,
            "error": "Missing 'document' or 'input' in request"
        }

    # Since the main analysis function is async, we need to run it appropriately
    import asyncio

    async def run_analysis():
        return await analyze_searxng_results(searxng_results, context)

    # Run the async analysis
    result = asyncio.run(run_analysis())

    return result


def main():
    """
    Command-line entry point for compatibility with Claude Code skill system
    """
    import argparse

    parser = argparse.ArgumentParser(description='SearXNG Analyzer Skill')
    parser.add_argument('--analyze', type=str, help='SearXNG search results to analyze')

    args = parser.parse_args()

    if not args.analyze:
        parser.print_help()
        sys.exit(1)

    # Mock context object for command-line usage
    class MockContext:
        class MockLLM:
            def generate(self, prompt, model, temperature, max_tokens):
                # Simulate LLM response
                return f"Simulated summary of: {prompt[:200]}..."

        def __init__(self):
            self.llm = self.MockLLM()

    mock_context = MockContext()

    # Since the main analysis function is async, we need to run it in an event loop
    import asyncio
    result = asyncio.run(analyze_searxng_results(args.analyze, mock_context))

    # Print result as JSON for Claude to consume
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()