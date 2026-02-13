---
name: email-sender
description: Sends emails with content from other skill results (like searxng-article-analyzer, searxng-analyzer, etc.). Uses LLM to analyze content and generate appropriate subject lines. Ideal for distributing analysis results via email.
---

# Email Sender Skill

This skill sends emails with content from other skill results (like searxng-article-analyzer, searxng-analyzer, etc.). Uses LLM to analyze content and generate appropriate subject lines.

## Instructions

- When users want to send content via email, execute `scripts/main.py` with email configuration
- The skill will use LLM to analyze the content and generate a suitable subject line if not provided
- Requires SMTP credentials to be configured as environment variables
- Works well with content from searxng-article-analyzer and searxng-analyzer skills
- Can handle both plain text and HTML content

## Core Functions

- **send_email**: Sends an email to the specified recipient with the provided content
- **analyze_and_send**: Analyzes content using LLM and sends email with generated subject

## Examples

- "Send this article analysis to my email" → Configure email settings and call send_email with content
- "Email me the search results" → Use content from searxng-analyzer and send via email
- "Share the analysis with my team" → Generate email with team members as recipients

## Additional Resources

- For complete configuration details, see [references/configuration.md](references/configuration.md)
- For email templates, see [assets/templates/](assets/templates/)

## Guidelines

- Always verify email addresses are properly formatted before sending
- Use environment variables for SMTP credentials to keep them secure
- The skill will generate appropriate subject lines if not provided
- Content from other skills can be formatted as HTML for rich email presentation
- The skill uses qwen3-max model for content analysis and subject generation
- For Gmail, use app passwords instead of regular passwords
- Recommended to use email services that support SMTP (Gmail, Outlook, etc.)