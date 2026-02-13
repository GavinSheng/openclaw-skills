#!/bin/bash
# Email sending test script

echo "Testing email sending functionality..."

# Check if required environment variables are set
if [ -z "$EMAIL_SENDER_ADDRESS" ]; then
    echo "ERROR: EMAIL_SENDER_ADDRESS is not set"
    echo "Please set your email address:"
    echo "export EMAIL_SENDER_ADDRESS=your-email@outlook.com"
    exit 1
fi

if [ -z "$EMAIL_SENDER_PASSWORD" ]; then
    echo "ERROR: EMAIL_SENDER_PASSWORD is not set"
    echo "Please set your email password/app key:"
    echo "export EMAIL_SENDER_PASSWORD=your-password"
    exit 1
fi

echo "Using sender: $EMAIL_SENDER_ADDRESS"
echo "SMTP Server: ${EMAIL_SMTP_SERVER:-smtp-mail.outlook.com}"

# Create test content similar to what searxng-article-analyzer would produce
TEST_CONTENT="<h1>OpenClaw Skills 测试报告</h1>
<p>这是来自 OpenClaw Skills 的自动测试邮件。</p>

<h2>功能测试</h2>
<ul>
<li>✅ 邮件发送功能正常</li>
<li>✅ 与现有技能集成正常</li>
<li>✅ HTML 内容渲染正常</li>
</ul>

<h2>技能整合</h2>
<p>此邮件表明邮件发送技能已成功集成到 OpenClaw 技能集合中，
可以与 searxng-article-analyzer、searxng-analyzer 等技能协同工作。</p>

<p>如需发送实际的分析结果，请在 Claude 中使用类似以下的指令：</p>
<p>\"分析这个文章并把结果发到我的邮箱\"</p>

<hr>
<p><small>此邮件由 OpenClaw Email Sender 技能自动生成</small></p>"

# If TO_EMAIL is provided as argument, use it; otherwise, use the sender's email for testing
TO_EMAIL=${1:-$EMAIL_SENDER_ADDRESS}

echo "Sending test email to: $TO_EMAIL"

python3 skills/email-sender/scripts/main.py --to-email "$TO_EMAIL" --content "$TEST_CONTENT" --subject "OpenClaw Skills - 邮件发送功能测试"