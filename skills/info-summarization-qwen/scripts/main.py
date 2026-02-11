#!/usr/bin/env python3
"""
Qwen3-Max Information Summarization Skill - Main Execution Script

Provides content summarization, key point extraction, and analysis using Qwen3-Max.
This script is meant to be executed directly by Claude.
"""

import argparse
import json
import sys
import os
from typing import Dict, Any


def call_qwen_summarization(text: str, action: str, context: Any, target_length: str = "medium", max_points: int = 5) -> Dict[str, Any]:
    """
    Call Qwen3-Max for summarization, key point extraction, or analysis using the context.llm API.

    Args:
        text: Input text to process
        action: Type of action - 'summarize', 'extract', or 'analyze'
        context: Context object containing the LLM API interface
        target_length: Target length for summarization ("short", "medium", "long")
        max_points: Maximum number of key points to extract

    Returns:
        Dictionary containing the result and metadata
    """
    import time
    start_time = time.time()

    if action == "summarize":
        prompt = f"""请对以下内容进行总结：

{text}

请提供一个{target_length}长度的总结。"""

        response = context.llm.generate(
            prompt=prompt,
            model="qwen3-max-2026-01-23",  # 使用完整模型 ID
            temperature=0.3,
            max_tokens=500
        )

        result = {
            "success": True,
            "original_content_length": len(text),
            "summary": response,
            "processing_duration": time.time() - start_time,
            "model_used": "qwen3-max"
        }

    elif action == "extract":
        prompt = f"""请从以下内容中提取最重要的{max_points}个要点：

{text}

请以列表形式呈现关键要点。"""

        response = context.llm.generate(
            prompt=prompt,
            model="qwen3-max-2026-01-23",  # 使用完整模型 ID
            temperature=0.3,
            max_tokens=500
        )

        result = {
            "success": True,
            "original_content_length": len(text),
            "key_points": response.split('\n'),  # 假设返回值是换行分隔的要点
            "points_extracted": max_points,
            "processing_duration": time.time() - start_time,
            "model_used": "qwen3-max"
        }

    elif action == "analyze":
        prompt = f"""请对以下内容进行全面分析：

{text}

分析应包括主要内容、关键概念、潜在影响等。"""

        response = context.llm.generate(
            prompt=prompt,
            model="qwen3-max-2026-01-23",  # 使用完整模型 ID
            temperature=0.3,
            max_tokens=1000
        )

        result = {
            "success": True,
            "original_content_length": len(text),
            "analysis": response,
            "processing_duration": time.time() - start_time,
            "model_used": "qwen3-max"
        }

    else:
        result = {
            "success": False,
            "error": f"Unknown action: {action}",
            "processing_duration": time.time() - start_time
        }

    return result


def handler(request, context):
    """
    MoltBot platform compatible handler for information summarization

    Args:
        request: Request dictionary containing the input
        context: Context object containing the LLM API interface

    Returns:
        Dictionary containing summarization results
    """
    text = request.get("input", "") or request.get("text", "")
    action = request.get("action", "summarize")  # Default to summarize
    target_length = request.get("length", "medium")
    max_points = request.get("max_points", 5)

    if not text:
        return {
            "success": False,
            "error": "Missing 'input' or 'text' in request"
        }

    if action not in ["summarize", "extract", "analyze"]:
        return {
            "success": False,
            "error": f"Invalid action: {action}. Supported actions: summarize, extract, analyze"
        }

    # Call the Qwen summarization function
    result = call_qwen_summarization(text, action, context, target_length, max_points)

    return result


def main():
    """Command-line entry point for compatibility with Claude Code skill system"""
    parser = argparse.ArgumentParser(description='Qwen3-Max Information Summarization Skill')
    parser.add_argument('--summarize', type=str, help='Text to summarize')
    parser.add_argument('--extract', type=str, help='Text to extract key points from')
    parser.add_argument('--analyze', type=str, help='Text to analyze')
    parser.add_argument('--length', type=str, default='medium', choices=['short', 'medium', 'long'],
                        help='Target length for summarization')
    parser.add_argument('--max-points', type=int, default=5, help='Maximum number of key points to extract')

    args = parser.parse_args()

    # Mock context object for command-line usage
    class MockContext:
        class MockLLM:
            def generate(self, prompt, model, temperature, max_tokens):
                # Simulate LLM response based on action
                if 'summarize' in prompt.lower():
                    return f"Simulated summary of: {prompt[:100]}..."
                elif 'extract' in prompt.lower() or 'key points' in prompt.lower():
                    return f"1. Key point from: {prompt[:50]}\n2. Another point"
                elif 'analyze' in prompt.lower():
                    return f"Analysis of content: {prompt[:100]}..."
                else:
                    return f"Processed: {prompt[:100]}..."

        def __init__(self):
            self.llm = self.MockLLM()

    mock_context = MockContext()

    if args.summarize:
        result = call_qwen_summarization(args.summarize, "summarize", mock_context, args.length, args.max_points)
    elif args.extract:
        result = call_qwen_summarization(args.extract, "extract", mock_context, args.length, args.max_points)
    elif args.analyze:
        result = call_qwen_summarization(args.analyze, "analyze", mock_context, args.length, args.max_points)
    else:
        parser.print_help()
        sys.exit(1)

    # Print result as JSON for Claude to consume
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()