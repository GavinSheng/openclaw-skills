# Email Sender Configuration Guide

## Environment Variables

The Email Sender skill uses the following environment variables for configuration:

### Required Settings
- `EMAIL_SENDER_ADDRESS` - Your email address
- `EMAIL_SENDER_PASSWORD` - Your email app password or access token

### Optional Settings
- `EMAIL_SMTP_SERVER` - SMTP server (defaults to `smtp.gmail.com`)
- `EMAIL_SMTP_PORT` - SMTP port (defaults to `587`)

## Service-Specific Configuration

### Gmail
```bash
export EMAIL_SMTP_SERVER=smtp.gmail.com
export EMAIL_SMTP_PORT=587
export EMAIL_SENDER_ADDRESS=your-email@gmail.com
export EMAIL_SENDER_PASSWORD=your-16-digit-app-password
```

**Important**: For Gmail, you must use an App Password instead of your regular password:
1. Enable 2-factor authentication
2. Generate an App Password at [Google Account Security](https://myaccount.google.com/security)
3. Use the 16-character App Password in `EMAIL_SENDER_PASSWORD`

### Outlook/Hotmail
```bash
export EMAIL_SMTP_SERVER=smtp-mail.outlook.com
export EMAIL_SMTP_PORT=587
export EMAIL_SENDER_ADDRESS=your-email@outlook.com
export EMAIL_SENDER_PASSWORD=your-password
```

### Yahoo Mail
```bash
export EMAIL_SMTP_SERVER=smtp.mail.yahoo.com
export EMAIL_SMTP_PORT=587
export EMAIL_SENDER_ADDRESS=your-email@yahoo.com
export EMAIL_SENDER_PASSWORD=your-app-password
```

## Security Best Practices

1. **Never hardcode credentials** in scripts or configuration files
2. **Use environment variables** or secure credential management systems
3. **Rotate passwords/app tokens** regularly
4. **Limit permissions** of the email account used for sending
5. **Review email logs** regularly for unauthorized access

## Testing Your Configuration

To test your email configuration, use the command line:

```bash
python scripts/main.py --to-email "test@example.com" --content "Test email content"
```

## Troubleshooting

### Common Issues

- **Authentication Failed**: Verify your email address and password/app token are correct
- **SMTP Connection Error**: Check your SMTP server and port settings
- **Permission Error**: Ensure your email account allows SMTP access
- **Content Blocked**: Some email providers block automated content

### Verifying Setup

1. Check environment variables are set:
   ```bash
   echo $EMAIL_SENDER_ADDRESS
   echo $EMAIL_SMTP_SERVER
   ```

2. Test with a simple email first

3. Monitor your email service's security activity