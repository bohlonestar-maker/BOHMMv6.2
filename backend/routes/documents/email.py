"""
Document Signing - Email Notifications

Handles sending email notifications for document signing:
- Signing request emails to recipients
- Approval request emails to approvers
"""
import os
import sys


async def send_signing_email(
    recipient_email: str,
    recipient_name: str,
    template_name: str,
    message: str,
    signing_token: str,
    sender_name: str,
    is_approver: bool = False
):
    """Send email notification with signing link"""
    try:
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 465))
        smtp_username = os.environ.get('SUPPORT_SMTP_USERNAME', os.environ.get('SMTP_USERNAME'))
        smtp_password = os.environ.get('SUPPORT_SMTP_PASSWORD', os.environ.get('SMTP_PASSWORD'))
        smtp_from = os.environ.get('SUPPORT_SMTP_USERNAME', os.environ.get('SMTP_FROM_EMAIL'))
        
        if not all([smtp_host, smtp_username, smtp_password, smtp_from]):
            sys.stderr.write("[DOCS] SMTP not configured, skipping email\n")
            return
        
        # Build signing URL
        frontend_url = os.environ.get('FRONTEND_URL', os.environ.get('REACT_APP_BACKEND_URL', ''))
        if '/api' in frontend_url:
            frontend_url = frontend_url.replace('/api', '')
        signing_url = f"{frontend_url}/sign/{signing_token}"
        
        msg = MIMEMultipart('alternative')
        
        if is_approver:
            msg['Subject'] = f"Approval Required: {template_name}"
            action_text = "approval"
            button_text = "Review & Approve"
            header_text = "Document Requires Your Approval"
        else:
            msg['Subject'] = f"Document Ready for Signature: {template_name}"
            action_text = "signature"
            button_text = "Review & Sign Document"
            header_text = "Document Ready for Signature"
        
        msg['From'] = smtp_from
        msg['To'] = recipient_email
        
        # Plain text version
        text_content = f"""
Hello {recipient_name},

{sender_name if not is_approver else "A document"} {"has sent you" if not is_approver else "requires your"} {"a document" if not is_approver else "approval"} "{template_name}" that requires your {action_text}.

{f"Message: {message}" if message else ""}

Click the link below to review and {"sign" if not is_approver else "approve/deny"} the document:
{signing_url}

This link will expire in 30 days.

Thank you,
BOH Document System
        """
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {"#dc2626" if is_approver else "#1e293b"}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; }}
        .button {{ display: inline-block; background: {"#dc2626" if is_approver else "#7c3aed"}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #64748b; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{header_text}</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{recipient_name}</strong>,</p>
            <p>{"<strong>" + sender_name + "</strong> has sent you a document" if not is_approver else "A document"} that requires your {action_text}:</p>
            <p style="font-size: 18px; color: {"#dc2626" if is_approver else "#7c3aed"};"><strong>{template_name}</strong></p>
            {f"<p><em>{message}</em></p>" if message else ""}
            <p style="text-align: center;">
                <a href="{signing_url}" class="button">{button_text}</a>
            </p>
            <p style="font-size: 12px; color: #64748b;">This link will expire in 30 days.</p>
        </div>
        <div class="footer">
            <p>BOH Document Signing System</p>
        </div>
    </div>
</body>
</html>
        """
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=True
        )
        
        sys.stderr.write(f"[DOCS] {'Approval' if is_approver else 'Signing'} email sent to {recipient_email}\n")
        
    except Exception as e:
        sys.stderr.write(f"[DOCS] Failed to send signing email: {e}\n")
