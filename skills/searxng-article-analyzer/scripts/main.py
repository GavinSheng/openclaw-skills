#!/usr/bin/env python3
"""
SearXNG Article Analyzer Skill - Main Execution Script

Provides detailed analysis of individual articles using qwen3-max.
This script is meant to be executed directly by Claude for in-depth article analysis.
Supports both standard HTTP requests and Playwright browser automation for anti-anti-spider purposes.
"""

import argparse
import asyncio
import json
import sys
import os
import re
from typing import Dict, Any
import httpx
from urllib.parse import urljoin, quote
import time


async def fetch_article_content_http(url: str) -> Dict[str, Any]:
    """
    Fetch and extract content from a specific article URL using standard HTTP requests.

    Args:
        url: Article URL to fetch content from

    Returns:
        Dictionary containing page content and metadata
    """
    start_time = time.time()

    try:
        # Create headers optimized for article content, mimicking a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Google Chrome";v="91", "Chromium";v="91", ";Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/',
        }

        # Handle proxy configuration
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

        client_params = {
            'timeout': 30.0,
            'headers': headers
        }

        if proxy:
            client_params['proxies'] = proxy

        async with httpx.AsyncClient(**client_params) as client:
            response = await client.get(url)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code} - Could not fetch the article",
                    "url": url
                }

            content = response.text
            fetch_duration = time.time() - start_time

            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "No title"

            # Extract main content (try common article selectors)
            # Look for main article content in common tags
            article_patterns = [
                r'<article[^>]*>(.*?)</article>',
                r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
                r'<main[^>]*>(.*?)</main>',
                r'<div[^>]*id="[^"]*article[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*id="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            ]

            main_content = ""
            for pattern in article_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    main_content = match.group(1)
                    break

            # If no common pattern found, extract text from body
            if not main_content:
                body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.IGNORECASE | re.DOTALL)
                if body_match:
                    main_content = body_match.group(1)
                else:
                    main_content = content

            # Remove script and style elements
            clean_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', main_content, flags=re.DOTALL)
            # Remove comments
            clean_content = re.sub(r'<!--.*?-->', ' ', clean_content, flags=re.DOTALL)
            # Remove extra whitespace
            clean_content = re.sub(r'\s+', ' ', clean_content)

            # Remove common non-content elements (navigation, ads, etc.)
            non_content_patterns = [
                r'<nav[^>]*>.*?</nav>',
                r'<footer[^>]*>.*?</footer>',
                r'<header[^>]*>.*?</header>',
                r'<aside[^>]*>.*?</aside>',
                r'<div[^>]*class="[^"]*(nav|menu|sidebar|advertisement|ads|banner)[^"]*"[^>]*>.*?</div>',
                r'<section[^>]*class="[^"]*(nav|menu|sidebar|advertisement|ads|banner)[^"]*"[^>]*>.*?</section>',
            ]

            for pattern in non_content_patterns:
                clean_content = re.sub(pattern, ' ', clean_content, flags=re.IGNORECASE | re.DOTALL)

            # Further clean up
            clean_content = re.sub(r'<[^>]+>', ' ', clean_content)  # Remove all remaining tags
            main_text = ' '.join(clean_content.split())

            # Extract meta description if available
            meta_desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            meta_description = meta_desc_match.group(1) if meta_desc_match else ""

            # Extract publication date if available
            date_patterns = [
                r'<time[^>]+datetime=["\']([^"\']*)["\']',
                r'<time[^>]+content=["\']([^"\']*)["\']',
                r'datetime=["\']([^"\']*)["\']',
                r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{4}/\d{2}/\d{2})',
            ]
            pub_date = ""
            for pattern in date_patterns:
                date_match = re.search(pattern, content, re.IGNORECASE)
                if date_match:
                    pub_date = date_match.group(1)
                    break

            return {
                "success": True,
                "url": url,
                "title": title,
                "content": main_text,
                "meta_description": meta_description,
                "publication_date": pub_date,
                "raw_content_preview": main_text[:1000],  # First 1000 chars as preview
                "status_code": response.status_code,
                "fetch_duration": fetch_duration,
                "full_content_length": len(main_text),
                "method": "http"
            }

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Connection failed - URL may be blocked in your region or inaccessible",
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error occurred while fetching: {str(e)}",
            "url": url
        }


async def fetch_article_content_playwright(url: str) -> Dict[str, Any]:
    """
    Fetch and extract content from a specific article URL using Playwright browser automation.
    This method can handle JavaScript-rendered content and anti-bot measures.

    Args:
        url: Article URL to fetch content from

    Returns:
        Dictionary containing page content and metadata
    """
    try:
        from playwright.async_api import async_playwright

        start_time = time.time()

        async with async_playwright() as p:
            # Launch browser with stealth options
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Optionally disable images for faster loading
                    '--disable-javascript',  # Only if JS is not needed
                ]
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Sec-Ch-Ua': '"Google Chrome";v="91", "Chromium";v="91", ";Not-A.Brand";v="99"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Upgrade-Insecure-Requests': '1',
                },
                java_script_enabled=True,  # Enable JavaScript as many sites require it
                bypass_csp=True
            )

            page = await context.new_page()

            # Navigate to the page
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for page to load and execute JavaScript
            await page.wait_for_timeout(3000)  # Wait additional time for dynamic content

            # Get page content after JavaScript execution
            content = await page.content()
            title = await page.title()

            # Close browser
            await browser.close()

            fetch_duration = time.time() - start_time

            # Process the content similar to HTTP method
            # Extract main content (try common article selectors)
            article_patterns = [
                r'<article[^>]*>(.*?)</article>',
                r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
                r'<main[^>]*>(.*?)</main>',
                r'<div[^>]*id="[^"]*article[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*id="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            ]

            main_content = ""
            for pattern in article_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    main_content = match.group(1)
                    break

            # If no common pattern found, extract text from body
            if not main_content:
                body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.IGNORECASE | re.DOTALL)
                if body_match:
                    main_content = body_match.group(1)
                else:
                    main_content = content

            # Remove script and style elements
            clean_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', main_content, flags=re.DOTALL)
            # Remove comments
            clean_content = re.sub(r'<!--.*?-->', ' ', clean_content, flags=re.DOTALL)
            # Remove extra whitespace
            clean_content = re.sub(r'\s+', ' ', clean_content)

            # Remove common non-content elements (navigation, ads, etc.)
            non_content_patterns = [
                r'<nav[^>]*>.*?</nav>',
                r'<footer[^>]*>.*?</footer>',
                r'<header[^>]*>.*?</header>',
                r'<aside[^>]*>.*?</aside>',
                r'<div[^>]*class="[^"]*(nav|menu|sidebar|advertisement|ads|banner)[^"]*"[^>]*>.*?</div>',
                r'<section[^>]*class="[^"]*(nav|menu|sidebar|advertisement|ads|banner)[^"]*"[^>]*>.*?</section>',
            ]

            for pattern in non_content_patterns:
                clean_content = re.sub(pattern, ' ', clean_content, flags=re.IGNORECASE | re.DOTALL)

            # Further clean up
            clean_content = re.sub(r'<[^>]+>', ' ', clean_content)  # Remove all remaining tags
            main_text = ' '.join(clean_content.split())

            # Extract meta description if available
            meta_desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            meta_description = meta_desc_match.group(1) if meta_desc_match else ""

            # Extract publication date if available
            date_patterns = [
                r'<time[^>]+datetime=["\']([^"\']*)["\']',
                r'<time[^>]+content=["\']([^"\']*)["\']',
                r'datetime=["\']([^"\']*)["\']',
                r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{4}/\d{2}/\d{2})',
            ]
            pub_date = ""
            for pattern in date_patterns:
                date_match = re.search(pattern, content, re.IGNORECASE)
                if date_match:
                    pub_date = date_match.group(1)
                    break

            return {
                "success": True,
                "url": url,
                "title": title,
                "content": main_text,
                "meta_description": meta_description,
                "publication_date": pub_date,
                "raw_content_preview": main_text[:1000],  # First 1000 chars as preview
                "status_code": 200,  # Assuming successful fetch with Playwright
                "fetch_duration": fetch_duration,
                "full_content_length": len(main_text),
                "method": "playwright"
            }

    except ImportError:
        return {
            "success": False,
            "error": "Playwright is not installed. Install with 'pip install playwright' and run 'playwright install'",
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error occurred while fetching with Playwright: {str(e)}",
            "url": url
        }


async def fetch_article_content(url: str) -> Dict[str, Any]:
    """
    Fetch article content with fallback from HTTP to Playwright methods.
    """
    # First try with standard HTTP
    result = await fetch_article_content_http(url)

    # If HTTP fails with 401/403/406 or similar protection errors, try Playwright
    if not result["success"] and any(code in result["error"] for code in ["401", "403", "406", "429", "anti-bot", "robot", "captcha", "datadome", "cloudfront"]):
        print(f"Standard HTTP request failed, trying with Playwright browser automation for {url}...")
        result = await fetch_article_content_playwright(url)

    # If HTTP fails completely, try Playwright anyway
    elif not result["success"]:
        print(f"Standard HTTP request failed, falling back to Playwright browser automation for {url}...")
        result = await fetch_article_content_playwright(url)

    return result


def call_qwen_analysis(article_data: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Call qwen3-max for detailed analysis of the article content.

    Args:
        article_data: Dictionary containing article information
        context: Context object containing the LLM API interface

    Returns:
        Dictionary containing summary and detailed analysis
    """
    start_time = time.time()

    title = article_data.get("title", "Untitled")
    content = article_data.get("content", "")
    url = article_data.get("url", "Unknown")
    meta_desc = article_data.get("meta_description", "")
    method = article_data.get("method", "unknown")

    # Prepare content for analysis (truncate if too long)
    content_preview = content[:4000]  # Limit to 4000 chars to prevent token overflow

    prompt = f"""请对以下文章进行深入分析，并生成适合公众号发布的概要和详情：

文章标题：{title}
文章URL：{url}
抓取方法：{method}
元描述：{meta_desc}

文章内容：
{content_preview}

请按以下格式返回分析结果：

## 概要
[不超过300字的文章总结，突出核心观点和价值，适合快速了解文章主旨]

## 详情
[对文章内容进行必要的整理和总结，避免原文照抄，组织成适合公众号发布的格式，可以包括：
- 背景介绍
- 核心内容/主要观点
- 关键数据或案例
- 深度分析
- 总结或展望]

注意：请确保详情部分经过整理和优化，不要简单复制原文。要突出文章的价值点，使读者有兴趣深入了解。"""

    try:
        # Call the LLM for analysis using the MoltBot standard interface
        response = context.llm.generate(
            prompt=prompt,
            model="qwen3-max-2026-01-23",  # 使用完整模型 ID
            temperature=0.5,
            max_tokens=2000
        )

        if response is None:
            return {
                "success": False,
                "error": "大语言模型调用失败：模型返回了空响应。请检查模型服务是否正常运行。",
                "processing_duration": time.time() - start_time
            }

        # Extract summary and detail parts from the response
        lines = response.split('\n')
        summary_section = []
        detail_section = []
        current_section = None

        for line in lines:
            if '## 概要' in line:
                current_section = 'summary'
            elif '## 详情' in line:
                current_section = 'detail'
            elif current_section == 'summary':
                summary_section.append(line)
            elif current_section == 'detail':
                detail_section.append(line)

        summary = '\n'.join(summary_section).strip()
        detail = '\n'.join(detail_section).strip()

        result = {
            "success": True,
            "url": url,
            "title": title,
            "summary": summary,
            "detail": detail,
            "full_analysis": response,
            "processing_duration": time.time() - start_time,
            "model_used": "qwen3-max",
            "method": method
        }

        return result

    except Exception as e:
        error_msg = f"大语言模型调用失败：{str(e)}\n\n请检查：\n- 模型服务是否正常运行\n- 模型ID是否正确\n- API密钥是否有效\n- 网络连接是否正常"
        return {
            "success": False,
            "error": error_msg,
            "processing_duration": time.time() - start_time
        }


def handler(request, context):
    """
    MoltBot platform compatible handler for article analysis

    Args:
        request: Request dictionary containing the input
        context: Context object containing the LLM API interface

    Returns:
        Dictionary containing article analysis results
    """
    article_url = request.get("url", "") or request.get("article_url", "")

    if not article_url:
        return {
            "success": False,
            "error": "Missing 'url' or 'article_url' in request"
        }

    try:
        # First, fetch the article content (with fallback to Playwright if needed)
        article_data = asyncio.run(fetch_article_content(article_url))

        if not article_data["success"]:
            return article_data

        # Then analyze the content using the LLM
        analysis_result = call_qwen_analysis(article_data, context)

        return analysis_result

    except Exception as e:
        return {
            "success": False,
            "error": f"Operation failed: {str(e)}"
        }


def main():
    """Command-line entry point for compatibility with Claude Code skill system"""
    parser = argparse.ArgumentParser(description='SearXNG Article Analyzer Skill')
    parser.add_argument('--url', type=str, required=True, help='URL of the article to analyze')

    args = parser.parse_args()

    # Mock context for command-line usage
    class MockContext:
        class MockLLM:
            def generate(self, prompt, model, temperature, max_tokens):
                # Simulate LLM response for command-line testing
                return f"模拟分析结果:\n\n## 概要\n这是对 {args.url} 的模拟概要，不超过300字，突出核心观点和价值，适合快速了解文章主旨。\n\n## 详情\n这是对 {args.url} 的详细分析，包含背景介绍、核心内容、关键数据、深度分析和总结展望，组织成适合公众号发布的格式。"

        def __init__(self):
            self.llm = self.MockLLM()

    mock_context = MockContext()

    # Create a request-like object
    request = {"url": args.url}

    # Call the handler
    result = handler(request, mock_context)

    # Print result as JSON for Claude to consume
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()