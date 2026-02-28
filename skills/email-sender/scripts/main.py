#!/usr/bin/env python3
"""
Email Sender Skill - Main Execution Script

Sends email with content from other skill results (like searxng-article-analyzer, searxng-analyzer, etc.).
Uses LLM to analyze content and generate appropriate subject line.
This script is meant to be executed directly by Claude.
"""

import argparse
import json
import sys
import os
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import re


def markdown_to_html(markdown_text: str) -> str:
    """
    Convert Markdown content to HTML for proper email rendering.

    Args:
        markdown_text: Input markdown text

    Returns:
        Converted HTML text
    """
    # First, try to use the markdown library if available (recommended)
    try:
        import markdown
        # Use extended markdown features for better compatibility
        html_text = markdown.markdown(markdown_text, extensions=[
            'extra',        # Includes tables, fenced code blocks, footnotes, etc.
            'codehilite',   # Syntax highlighting
            'fenced_code',  # Fenced code blocks
            'toc',          # Table of contents
            'attr_list',    # Attribute lists
            'def_list',     # Definition lists
            'abbr',         # Abbreviations
            'md_in_html'    # Markdown in HTML blocks
        ])
    except ImportError:
        # Basic fallback conversion if markdown library is not available
        import re

        # First, handle code blocks (these should be processed first to avoid interference)
        # Process fenced code blocks: ```lang ... ```
        def code_block_replacer(match):
            lang = match.group(1) if match.group(1) else ''
            code = match.group(2)
            # Escape HTML entities in code blocks
            code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return f'<pre><code class="language-{lang}">{code}</code></pre>'

        # Handle fenced code blocks (```lang\n...\n```)
        markdown_text = re.sub(r'```(\w+)?\n(.*?)```', code_block_replacer, markdown_text, flags=re.DOTALL)

        # Split the text into lines for processing
        lines = markdown_text.split('\n')
        html_lines = []

        in_list = False
        list_type = ''  # 'ul' for unordered, 'ol' for ordered

        for line in lines:
            # Check if this is a code block line (already processed)
            if '<pre><code' in line:
                html_lines.append(line)
                continue

            # Process headers (# Header -> <h1>Header</h1>)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                content = header_match.group(2)
                line = f'<h{level}>{content}</h{level}>'
                html_lines.append(line)
                continue

            # Process lists
            ul_match = re.match(r'^(\s*)[-*]\s+(.+)$', line)
            ol_match = re.match(r'^(\s*)([0-9]+)\.\s+(.+)$', line)

            if ul_match or ol_match:
                # Determine list type and content
                if ul_match:
                    indent = ul_match.group(1)
                    content = ul_match.group(2)
                    current_list_type = 'ul'
                else:
                    indent = ol_match.group(1)
                    content = ol_match.group(3)
                    current_list_type = 'ol'

                # Calculate indent level (2 spaces = 1 level)
                indent_level = len(indent) // 2

                # If not in a list or list type changed, close previous list
                if in_list and list_type != current_list_type:
                    html_lines.append('</li></ul>' if list_type == 'ul' else '</li></ol>')
                    in_list = False

                # Handle list nesting
                if not in_list:
                    # Start new list
                    list_tag = '<ul>' if current_list_type == 'ul' else '<ol>'
                    html_lines.append(list_tag)
                    in_list = True
                    list_type = current_list_type

                # Add the list item
                html_lines.append(f'<li>{content}')
            else:
                # Not a list item - if we were in a list, close it
                if in_list:
                    html_lines.append('</li></ul>' if list_type == 'ul' else '</li></ol>')
                    in_list = False

                # Process basic inline markdown elements in non-list lines
                # Bold: **text** or __text__
                processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
                processed_line = re.sub(r'__(.*?)__', r'<strong>\1</strong>', processed_line)

                # Italic: *text* or _text_
                processed_line = re.sub(r'\*(.*?)\*', r'<em>\1</em>', processed_line)
                processed_line = re.sub(r'_(.*?)_', r'<em>\1</em>', processed_line)

                # Links: [text](url)
                processed_line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', processed_line)

                # Inline code: `code`
                processed_line = re.sub(r'`([^`]+)`', r'<code>\1</code>', processed_line)

                # Paragraph tags for non-empty lines that aren't already HTML tags
                if processed_line.strip() and not processed_line.startswith('<'):
                    processed_line = f'<p>{processed_line}</p>'

                html_lines.append(processed_line)

        # Close any open list at the end
        if in_list:
            html_lines.append('</li></ul>' if list_type == 'ul' else '</li></ol>')

        html_text = '\n'.join(html_lines)

    # Wrap in basic HTML template for email clients
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif, sans-serif; line-height: 1.6; color: #333; margin: 20px; }}
        h1, h2, h3, h4, h5, h6 {{ margin-top: 1em; margin-bottom: 0.5em; color: #2c3e50; }}
        p {{ margin: 0.8em 0; }}
        ul, ol {{ margin: 0.8em 0; padding-left: 1.5em; }}
        li {{ margin: 0.3em 0; }}
        code {{ background-color: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
        pre {{ background-color: #f8f9fa; padding: 10px; overflow-x: auto; border-radius: 4px; margin: 0.8em 0; }}
        pre code {{ background: none; padding: 0; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
{html_text}
</body>
</html>"""

    return full_html


def analyze_content_and_generate_subject(content: str, context: Any) -> str:
    """
    Use LLM to analyze content and generate an appropriate email subject.

    Args:
        content: Content to analyze
        context: Context object containing the LLM API interface

    Returns:
        Generated subject line
    """
    import time
    start_time = time.time()

    # Prepare content for analysis (truncate if too long)
    content_preview = content[:2000] + "..." if len(content) > 2000 else content

    prompt = f"""请分析以下内容并生成一个合适的邮件主题。邮件内容如下：

{content_preview}

请只返回邮件主题，不要包含其他内容。主题应该简洁明了，反映邮件内容的核心。"""

    try:
        # Call the LLM for subject generation using the MoltBot standard interface
        response = context.llm.generate(
            prompt=prompt,
            model="qwen3-max-2026-01-23",  # 使用完整模型 ID
            temperature=0.3,
            max_tokens=100
        )

        if response is None:
            return "Generated Email Subject"

        # Clean up the response
        subject = response.strip().replace("\n", "").replace("\r", "")
        return subject

    except Exception as e:
        print(f"LLM subject generation failed: {str(e)}", file=sys.stderr)
        return "Generated Email Subject"


def detect_content_type(content: str) -> str:
    """
    Detect the content type of the email body.

    Args:
        content: The email content to analyze

    Returns:
        String indicating content type: 'markdown', 'html', or 'plain'
    """
    # Check if content already contains HTML tags
    html_tags = ['<html', '<body', '<p>', '<h', '<div', '<span', '<a href', '<ul', '<ol', '<li', '<strong', '<em', '<b>', '<i>', '<br', '<hr', '<table', '<tr', '<td']
    for tag in html_tags:
        if tag in content.lower():
            return 'html'

    # Check for markdown patterns
    markdown_patterns = [
        r'\*\*.*?\*\*',  # Bold **text**
        r'__.*?__',      # Bold __text__
        r'\*.*?\*',      # Italic *text*
        r'_.*?_',        # Italic _text_
        r'# .*',         # Headers # title
        r'## .*',        # Headers ## title
        r'### .*',       # Headers ### title
        r'- .*',         # Unordered list - item
        r'\d+\. .*',     # Ordered list 1. item
        r'```',          # Code blocks
        r'`.*?`',        # Inline code
        r'\[.*?\]\(.*?\)',  # Links [text](url)
    ]

    for pattern in markdown_patterns:
        if re.search(pattern, content):
            return 'markdown'

    # If no clear indicators found, assume plain text
    return 'plain'


def send_email_via_smtp(to_email: str, subject: str, body: str, from_email: str = None, password: str = None, content_format: str = 'auto') -> Dict[str, Any]:
    """
    Send email using SMTP with provided credentials or environment variables.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email address (optional, uses env var if not provided)
        password: Email password/app key (optional, uses env var if not provided)
        content_format: Format of the content - 'auto', 'markdown', 'html', or 'plain' (default 'auto')

    Returns:
        Dictionary containing operation result
    """
    import time
    start_time = time.time()

    # Get credentials from parameters or environment variables
    smtp_server = os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('EMAIL_SMTP_PORT', '587'))

    sender_email = from_email or os.environ.get('EMAIL_SENDER_ADDRESS')
    sender_password = password or os.environ.get('EMAIL_SENDER_PASSWORD')

    if not sender_email or not sender_password:
        return {
            "success": False,
            "error": "Missing email credentials. Please set EMAIL_SENDER_ADDRESS and EMAIL_SENDER_PASSWORD environment variables, or provide credentials as parameters."
        }

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')

        # Process content based on format
        if content_format == 'auto':
            detected_format = detect_content_type(body)
        else:
            detected_format = content_format

        # Process content according to format
        if detected_format == 'markdown':
            html_body = markdown_to_html(body)
            # For markdown content, only send HTML version since email clients
            # will render it properly (the markdown source is not needed)
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))  # HTML version only
        elif detected_format == 'html':
            # Content is already HTML, add as HTML part
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:  # plain or unknown
            # For plain text, create HTML version for better rendering
            html_body = body.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
            msg.attach(MIMEText(body, 'plain', 'utf-8'))  # Plain version
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))  # HTML version

        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable security
        server.login(sender_email, sender_password)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()

        return {
            "success": True,
            "message": f"Email sent successfully to {to_email}",
            "to_email": to_email,
            "subject": subject,
            "content_format": detected_format,
            "processing_duration": time.time() - start_time
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send email: {str(e)}"
        }


def send_email(email_config: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main function to send email with content analysis and subject generation.

    Args:
        email_config: Dictionary containing email configuration
        context: Context object containing the LLM API interface

    Returns:
        Dictionary containing operation result
    """
    import time
    start_time = time.time()

    to_email = email_config.get("to_email", "")
    subject = email_config.get("subject", "")
    content = email_config.get("content", "")
    from_email = email_config.get("from_email")
    password = email_config.get("password")

    if not to_email:
        return {
            "success": False,
            "error": "Missing 'to_email' in email_config"
        }

    if not content:
        return {
            "success": False,
            "error": "Missing 'content' in email_config"
        }

    # If no subject provided, generate one using LLM
    if not subject:
        subject = analyze_content_and_generate_subject(content, context)
        print(f"Generated subject: {subject}")

    # Send the email
    # Check if email_config specifies content format, otherwise use 'auto'
    content_format = email_config.get("content_format", "auto")
    result = send_email_via_smtp(to_email, subject, content, from_email, password, content_format)

    if result["success"]:
        result["processing_duration"] = time.time() - start_time
        result["to_email"] = to_email
        result["subject"] = subject

    return result


def handler(request, context):
    """
    MoltBot platform compatible handler for sending emails

    Args:
        request: Request dictionary containing the input
        context: Context object containing the LLM API interface

    Returns:
        Dictionary containing email sending results
    """
    email_config = request.get("email_config", request)  # Allow either format

    if not email_config:
        return {
            "success": False,
            "error": "Missing 'email_config' in request"
        }

    try:
        # Call the email sending function
        result = send_email(email_config, context)
        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Operation failed: {str(e)}"
        }


def main():
    """Command-line entry point for compatibility with Claude Code skill system"""
    parser = argparse.ArgumentParser(description='Email Sender Skill')
    parser.add_argument('--to-email', type=str, required=True, help='Recipient email address')
    parser.add_argument('--subject', type=str, help='Email subject (optional, will be generated if not provided)')
    parser.add_argument('--content', type=str, required=True, help='Email content')
    parser.add_argument('--from-email', type=str, help='Sender email address (optional, uses env var if not provided)')
    parser.add_argument('--password', type=str, help='Email password/app key (optional, uses env var if not provided)')
    parser.add_argument('--content-format', type=str, default='auto', choices=['auto', 'markdown', 'html', 'plain'],
                       help="Format of the content: 'auto' (detect automatically), 'markdown', 'html', or 'plain' (default: auto)")

    args = parser.parse_args()

    # Mock context object for command-line usage
    class MockContext:
        class MockLLM:
            def generate(self, prompt, model, temperature, max_tokens):
                # Simulate LLM response for subject generation
                if 'analyze' in prompt.lower() and 'subject' in prompt.lower():
                    return f"Subject for: {prompt[:50]}..."
                return f"Analysis result for: {prompt[:100]}..."

        def __init__(self):
            self.llm = self.MockLLM()

    mock_context = MockContext()

    # Prepare email configuration
    email_config = {
        "to_email": args.to_email,
        "subject": args.subject,
        "content": args.content,
        "from_email": args.from_email,
        "password": args.password,
        "content_format": args.content_format
    }

    # Call the email sending function
    result = send_email(email_config, mock_context)

    # Print result as JSON for Claude to consume
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()