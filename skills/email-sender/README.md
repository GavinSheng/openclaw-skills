# Email Sender Skill

This skill sends emails with content from other skill results (like searxng-article-analyzer, searxng-analyzer, etc.). Uses LLM to analyze content and generate appropriate subject lines.

## Installation

No additional dependencies required - uses built-in Python libraries.

## Configuration

Set environment variables for email sending:
```bash
export EMAIL_SMTP_SERVER=smtp.gmail.com      # SMTP server (defaults to Gmail)
export EMAIL_SMTP_PORT=587                  # SMTP port (defaults to 587)
export EMAIL_SENDER_ADDRESS=your-email@gmail.com    # Your email address
export EMAIL_SENDER_PASSWORD=your-app-password    # Your email app password
```

For Gmail, you'll need to:
1. Enable 2-factor authentication
2. Generate an App Password (not your regular password)
3. Use the App Password in EMAIL_SENDER_PASSWORD

## Usage

This skill can be invoked with email configuration:

```bash
python scripts/main.py --to-email "recipient@example.com" --content "Email content here" --subject "Optional subject"
```

Or programmatically through the handler:

```python
email_config = {
    "to_email": "recipient@example.com",
    "content": "Email content here",
    "subject": "Optional subject",  # If omitted, LLM will generate a subject
    "from_email": "sender@example.com",  # Optional, uses env var if not provided
    "password": "app-password"  # Optional, uses env var if not provided
}

result = handler({"email_config": email_config}, context)
```

## Features

- **Content Analysis**: Uses LLM to analyze email content and generate appropriate subject lines if not provided
- **Secure Credentials**: Supports environment variables for email credentials
- **HTML Support**: Sends rich HTML email content
- **Error Handling**: Comprehensive error handling and reporting
- **Flexible Integration**: Designed to work with other skills like searxng-article-analyzer

## Integration with Other Skills

This skill is designed to work seamlessly with other OpenClaw skills:
- Accepts results from searxng-article-analyzer as content
- Processes searxng-analyzer results for email distribution
- Works with any skill that produces content for email distribution

## Files

- `SKILL.md`: Contains skill definition and instructions for Claude
- `scripts/main.py`: Main execution script with core functionality
- `references/configuration.md`: Configuration and setup guidelines
- `assets/templates/`: Email templates (if any)