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


def send_email_via_smtp(to_email: str, subject: str, body: str, from_email: str = None, password: str = None) -> Dict[str, Any]:
    """
    Send email using SMTP with provided credentials or environment variables.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email address (optional, uses env var if not provided)
        password: Email password/app key (optional, uses env var if not provided)

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

        # Add body to email
        msg.attach(MIMEText(body, 'html', 'utf-8'))

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
    result = send_email_via_smtp(to_email, subject, content, from_email, password)

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
        "password": args.password
    }

    # Call the email sending function
    result = send_email(email_config, mock_context)

    # Print result as JSON for Claude to consume
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()