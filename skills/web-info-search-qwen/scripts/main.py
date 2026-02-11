#!/usr/bin/env python3
"""
Tongyi Web Information Search Skill - Main Execution Script

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


async def search_tongyi(query: str, num_results: int = 10) -> Dict[str, Any]:
    """
    Search using Tongyi search capabilities
    """
    try:
        encoded_query = quote(query.encode('utf-8'))

        # Headers optimized for Chinese search engines
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
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

        # Try search engines that Tongyi might integrate with or recommend
        # First, try Sogou (popular in China)
        search_url = f"https://www.sogou.com/web?query={encoded_query}"

        async with httpx.AsyncClient(**client_params) as client:
            response = await client.get(search_url)

            if response.status_code == 200:
                content = response.text

                # Pattern for Sogou search results
                title_pattern = r'<h3>\s*<a\s+href="([^"]*)"[^>]*>(.*?)</a>\s*</h3>'

                matches = re.findall(title_pattern, content, re.IGNORECASE | re.DOTALL)

                results = []
                for link, title_html in matches[:num_results]:
                    # Clean title by removing HTML tags and unescaping entities
                    title = re.sub(r'<[^>]+>', '', title_html).strip()
                    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")

                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": f"Search result for '{query}' from Sogou"
                    })

                if results:
                    return {
                        "success": True,
                        "results": results,
                        "search_provider": "Sogou"
                    }

        # If Sogou doesn't work, try 360 Search
        search_url = f"https://www.so.com/s?q={encoded_query}"

        async with httpx.AsyncClient(**client_params) as client:
            response = await client.get(search_url)

            if response.status_code == 200:
                content = response.text

                # Pattern for 360 Search results
                title_pattern = r'<h3>\s*<a\s+target="_blank"\s+href="([^"]*)"[^>]*>(.*?)</a>\s*</h3>'

                matches = re.findall(title_pattern, content, re.IGNORECASE | re.DOTALL)

                results = []
                for link, title_html in matches[:num_results]:
                    # Clean title by removing HTML tags and unescaping entities
                    title = re.sub(r'<[^>]+>', '', title_html).strip()
                    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")

                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": f"Search result for '{query}' from 360 Search"
                    })

                if results:
                    return {
                        "success": True,
                        "results": results,
                        "search_provider": "360 Search"
                    }

    except Exception as e:
        print(f"Tongyi integrated search failed: {str(e)}", file=sys.stderr)

    return None  # Return None if Tongyi search doesn't work


async def search_bing(query: str, num_results: int = 10) -> Dict[str, Any]:
    """
    Search using Bing (as alternative provider)
    """
    try:
        encoded_query = quote(query.encode('utf-8'))

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


async def web_search(query: str, num_results: int = 10) -> Dict[str, Any]:
    """
    Perform a web search for the given query, trying Tongyi integrated providers first.

    Args:
        query: Search query string
        num_results: Number of results to return (default 10)

    Returns:
        Dictionary containing search results
    """
    start_time = time.time()

    # Try Tongyi integrated search first (Sogou, 360 Search, etc.)
    tongyi_result = await search_tongyi(query, num_results)
    if tongyi_result and tongyi_result["results"]:
        search_duration = time.time() - start_time
        return {
            "success": True,
            "results": tongyi_result["results"],
            "query": query,
            "num_results_returned": len(tongyi_result["results"]),
            "search_duration": search_duration,
            "search_provider": tongyi_result["search_provider"]
        }

    # If Tongyi providers fail, try Bing as alternative
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

    # If all search providers fail, provide helpful fallback results
    fallback_results = []
    for i in range(min(num_results, 3)):
        fallback_results.append({
            "title": f"Suggested resource for '{query}'",
            "url": f"https://www.sogou.com/web?query={quote(query)}",
            "snippet": f"Try searching for '{query}' using Sogou or another search engine that may be more accessible in your region."
        })

    search_duration = time.time() - start_time
    return {
        "success": True,
        "results": fallback_results,
        "query": query,
        "num_results_returned": len(fallback_results),
        "search_duration": search_duration,
        "search_provider": "fallback",
        "warning": "All search services failed. Please check your internet connection and regional restrictions. Consider using local search engines."
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


def handler(request, context):
    """
    MoltBot platform compatible handler for web search and fetch operations

    Args:
        request: Request dictionary containing the input
        context: Context object containing the LLM API interface

    Returns:
        Dictionary containing search or fetch results
    """
    import asyncio

    search_query = request.get("search", "")
    fetch_url = request.get("fetch", "")
    num_results = request.get("num_results", 10)

    if search_query:
        # Run web search
        result = asyncio.run(web_search(search_query, num_results))
    elif fetch_url:
        # Run web fetch
        result = asyncio.run(web_fetch(fetch_url))
    else:
        return {
            "success": False,
            "error": "Missing 'search' or 'fetch' in request"
        }

    return result


def main():
    parser = argparse.ArgumentParser(description='Tongyi Web Information Search Skill')
    parser.add_argument('--search', type=str, help='Search query string')
    parser.add_argument('--fetch', type=str, help='URL to fetch content from')
    parser.add_argument('--num-results', type=int, default=10, help='Number of search results (for search)')

    args = parser.parse_args()

    if args.search:
        import asyncio
        result = asyncio.run(web_search(args.search, args.num_results))
    elif args.fetch:
        import asyncio
        result = asyncio.run(web_fetch(args.fetch))
    else:
        parser.print_help()
        sys.exit(1)

    # Print result as JSON for Claude to consume
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()