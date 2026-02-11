#!/usr/bin/env python3
"""
Web Information Search Skill - Main Execution Script

Provides web_search (keyword search) and web_fetch (webpage content extraction) functions.
This script is meant to be executed directly by Claude.
"""

import argparse
import asyncio
import json
import sys
import os
from typing import Dict, Any
import httpx
import re
from urllib.parse import urljoin, quote
import time


async def search_duckduckgo(query: str, num_results: int = 10) -> Dict[str, Any]:
    """
    Search using DuckDuckGo Instant Answer API
    """
    try:
        encoded_query = quote(query.encode('utf-8'))

        # Use direct API call with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        # Handle proxy configuration
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

        # Create client configuration
        client_params = {
            'timeout': 20.0,
            'headers': headers
        }

        if proxy:
            client_params['proxies'] = proxy

        async with httpx.AsyncClient(**client_params) as client:
            # Using DuckDuckGo's API
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }

            response = await client.get('https://api.duckduckgo.com/', params=params)

            if response.status_code == 200:
                data = response.json()

                results = []
                # Extract from RelatedTopics which contains search results
                for topic in data.get('RelatedTopics', [])[:num_results]:
                    if 'FirstURL' in topic and 'Text' in topic:
                        results.append({
                            "title": topic.get('Name', topic['Text'][:60]),
                            "url": topic['FirstURL'],
                            "snippet": topic['Text']
                        })

                if results:
                    return {
                        "success": True,
                        "results": results,
                        "search_provider": "DuckDuckGo"
                    }

    except Exception as e:
        print(f"DuckDuckGo search failed: {str(e)}", file=sys.stderr)

    return None  # Return None if DuckDuckGo search doesn't work


async def search_bing(query: str, num_results: int = 10) -> Dict[str, Any]:
    """
    Search using Bing (without API key - scraping approach)
    """
    try:
        encoded_query = quote(query.encode('utf-8'))

        # Bing Search endpoint
        search_url = f"https://www.bing.com/search?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.bing.com/'
        }

        # Handle proxy configuration
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

        # Create client configuration
        client_params = {
            'timeout': 20.0,
            'headers': headers
        }

        if proxy:
            client_params['proxies'] = proxy

        async with httpx.AsyncClient(**client_params) as client:
            response = await client.get(search_url)

            if response.status_code == 200:
                content = response.text

                # More specific pattern for Bing search results
                # Bing typically has results in <li> elements with class "b_algo"
                pattern = r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>.*?<h2><a\s+href="([^"]*)"[^>]*>(.*?)</a></h2>.*?</li>'

                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)

                results = []
                for link, title_html in matches[:num_results]:
                    # Clean title by removing HTML tags and unescaping entities
                    title = re.sub(r'<[^>]+>', '', title_html)
                    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'").strip()

                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": f"Search result for '{query}' from Bing"
                    })

                if results:
                    return {
                        "success": True,
                        "results": results,
                        "search_provider": "Bing"
                    }

    except Exception as e:
        print(f"Bing search failed: {str(e)}", file=sys.stderr)

    return None  # Return None if Bing search doesn't work


async def search_baidu(query: str, num_results: int = 10) -> Dict[str, Any]:
    """
    Search using Baidu (for Chinese region)
    """
    try:
        encoded_query = quote(query.encode('utf-8'))

        # Baidu search endpoint
        search_url = f"https://www.baidu.com/s?wd={encoded_query}&rn={min(num_results, 10)}&ie=utf-8"

        # Headers optimized for Baidu
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.baidu.com/'
        }

        # Handle proxy configuration
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

        # Create client configuration
        client_params = {
            'timeout': 20.0,
            'headers': headers
        }

        if proxy:
            client_params['proxies'] = proxy

        async with httpx.AsyncClient(**client_params) as client:
            response = await client.get(search_url)

            if response.status_code == 200:
                content = response.text

                # Pattern for Baidu search results - looking for title within h3 tags with specific classes
                title_pattern = r'<h3[^>]*class="[^"]*t[^"]*"[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>'

                matches = re.findall(title_pattern, content, re.IGNORECASE | re.DOTALL)

                results = []
                for link, title_html in matches[:num_results]:
                    # Clean title by removing HTML tags and unescaping entities
                    title = re.sub(r'<[^>]+>', '', title_html).strip()
                    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")

                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": f"Search result for '{query}' from Baidu"
                    })

                if results:
                    return {
                        "success": True,
                        "results": results,
                        "search_provider": "Baidu"
                    }

    except Exception as e:
        print(f"Baidu search failed: {str(e)}", file=sys.stderr)

    return None  # Return None if Baidu search doesn't work


async def web_search(query: str, num_results: int = 10) -> Dict[str, Any]:
    """
    Perform a web search for the given query, trying multiple search providers.

    Args:
        query: Search query string
        num_results: Number of results to return (default 10)

    Returns:
        Dictionary containing search results
    """
    start_time = time.time()

    # Try DuckDuckGo first (international service)
    duckduckgo_result = await search_duckduckgo(query, num_results)
    if duckduckgo_result and duckduckgo_result["results"]:
        search_duration = time.time() - start_time
        return {
            "success": True,
            "results": duckduckgo_result["results"],
            "query": query,
            "num_results_returned": len(duckduckgo_result["results"]),
            "search_duration": search_duration,
            "search_provider": "DuckDuckGo"
        }

    # If DuckDuckGo fails, try Bing (alternative)
    bing_result = await search_bing(query, num_results)
    if bing_result and bing_result["results"]:
        search_duration = time.time() - start_time
        return {
            "success": True,
            "results": bing_result["results"],
            "query": query,
            "num_results_returned": len(bing_result["results"]),
            "search_duration": search_duration,
            "search_provider": "Bing",
            "info": "Results from Bing (accessible internationally)"
        }

    # If Bing fails, try Baidu (Chinese region)
    baidu_result = await search_baidu(query, num_results)
    if baidu_result and baidu_result["results"]:
        search_duration = time.time() - start_time
        return {
            "success": True,
            "results": baidu_result["results"],
            "query": query,
            "num_results_returned": len(baidu_result["results"]),
            "search_duration": search_duration,
            "search_provider": "Baidu",
            "info": "Results from Baidu (more accessible in China)"
        }

    # If all search providers fail, provide helpful fallback results
    fallback_results = []
    for i in range(min(num_results, 3)):
        fallback_results.append({
            "title": f"Manual search suggestion for '{query}'",
            "url": f"https://www.google.com/search?q={quote(query)}",
            "snippet": f"You can manually search for '{query}' using your preferred search engine."
        })

    search_duration = time.time() - start_time
    return {
        "success": False,
        "results": fallback_results,
        "query": query,
        "num_results_returned": len(fallback_results),
        "search_duration": search_duration,
        "search_provider": "none",
        "warning": "All search services failed. Check your internet connection and regional restrictions. Consider using VPN or local search engines."
    }


async def web_fetch(url: str) -> Dict[str, Any]:
    """
    Fetch and extract content from a web page.

    Args:
        url: URL to fetch content from

    Returns:
        Dictionary containing page content and metadata
    """
    start_time = time.time()

    try:
        # Handle proxy configuration
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

        # Create client configuration with proxy if available
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache'
        }

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
                    "error": f"HTTP {response.status_code} - May be blocked in your region",
                    "url": url
                }

            content = response.text
            fetch_duration = time.time() - start_time

            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "No title"

            # Extract main content (basic approach)
            # Remove script and style elements
            clean_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', content, flags=re.DOTALL)
            # Remove HTML tags while preserving text
            text_only = re.sub(r'<[^>]+>', ' ', clean_content)
            # Normalize whitespace
            main_text = ' '.join(text_only.split())

            # Extract links
            link_pattern = r'<a[^>]+href\s*=\s*["\']([^"\']+)["\'][^>]*>'
            raw_links = re.findall(link_pattern, content, re.IGNORECASE)
            # Resolve relative URLs
            absolute_links = []
            for link in raw_links:
                absolute_link = urljoin(url, link)
                absolute_links.append(absolute_link)

            # Extract images
            img_pattern = r'<img[^>]+src\s*=\s*["\']([^"\']+)["\'][^>]*>'
            raw_imgs = re.findall(img_pattern, content, re.IGNORECASE)
            # Resolve relative URLs
            absolute_images = []
            for img in raw_imgs:
                absolute_img = urljoin(url, img)
                absolute_images.append(absolute_img)

            return {
                "success": True,
                "url": url,
                "title": title,
                "content": main_text[:4000],  # Truncate to 4000 chars
                "full_content_length": len(main_text),
                "links_count": len(absolute_links),
                "images_count": len(absolute_images),
                "status_code": response.status_code,
                "fetch_duration": fetch_duration,
                "headers": dict(response.headers)
            }

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Connection failed - URL may be blocked in your region (e.g., due to GFW in China) or proxy misconfigured",
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error occurred while fetching: {str(e)} - May be due to regional restrictions or proxy issues",
            "url": url
        }


async def main():
    parser = argparse.ArgumentParser(description='Web Information Search Skill')
    parser.add_argument('--search', type=str, help='Search query string')
    parser.add_argument('--fetch', type=str, help='URL to fetch content from')
    parser.add_argument('--num-results', type=int, default=10, help='Number of search results (for search)')

    args = parser.parse_args()

    if args.search:
        result = await web_search(args.search, args.num_results)
    elif args.fetch:
        result = await web_fetch(args.fetch)
    else:
        parser.print_help()
        sys.exit(1)

    # Print result as JSON for Claude to consume
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())