要完成从 mojian180@yeah.net 发送测试邮件，请按以下步骤操作：

发件人配置（必须是您拥有并可配置的邮箱）：
```bash
export EMAIL_SMTP_SERVER=smtp.yeah.net
export EMAIL_SMTP_PORT=587
export EMAIL_SENDER_ADDRESS=mojian180@yeah.net
export EMAIL_SENDER_PASSWORD=您在yeah.net邮箱的密码
```

发送测试邮件（收件人可以是任何邮箱）：
```bash
python3 skills/email-sender/scripts/main.py --to-email "收件人邮箱@example.com" --content "$(cat test_email_content.html)" --subject "OpenClaw Skills 测试邮件"
```

这将从 mojian180@yeah.net 向 "收件人邮箱@example.com" 发送一封测试邮件。

注意：
- 发件人邮箱（mojian180@yeah.net）是配置并用于发送邮件的邮箱
- 收件人邮箱是接收邮件的邮箱（可以是任何邮箱地址）
- 只有发件人邮箱需要在系统中配置 SMTP 认证信息