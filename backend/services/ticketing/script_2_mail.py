import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from django.conf import settings

def download_file(url, local_filename):
    """Downloads the HTML email template."""
    if not url:
        return None
    try:
        if "drive.google.com" in url:
            file_id = url.split('/d/')[1].split('/')[0]
            download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        else:
            download_url = url

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename
    except Exception as e:
        print(f"❌ Error downloading email template: {e}")
        return None

def send_ticket_email(email, relative_ticket_path, config):
    """
    Sends an email with the generated ticket attached.
    """
    if not relative_ticket_path:
        print(f"❌ Cannot send email to {email}: Ticket path is empty.")
        return False
        
    print(f"Sending ticket email to {email}...")
    
    # 1. Resolve full paths
    media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
    full_ticket_path = os.path.join(media_root, relative_ticket_path)
    temp_dir = os.path.join(media_root, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 2. Download the email HTML template
    local_email_path = download_file(config.email_message_url, os.path.join(temp_dir, "email_message.html"))
    if not local_email_path:
        print("❌ Could not download email template. Aborting email.")
        return False

    try:
        with open(local_email_path, 'r', encoding='utf-8') as f:
            message_template = f.read()

        # Try to extract the name from the email (or query the user model in the future)
        recipient_name = email.split('@')[0].capitalize()
        team_name = "Participant" # Fallback if no team is specified
        
        # Replace placeholders in the HTML
        email_body = message_template.replace('{name}', recipient_name).replace('{team_name}', team_name)
        
        # 3. Construct the Email Message
        msg = MIMEMultipart()
        msg['From'] = config.sender_email
        msg['To'] = email
        msg['Subject'] = "Your Event E-Ticket is Here!" 
        
        msg.attach(MIMEText(email_body, 'html'))

        # 4. Attach the Ticket Image
        with open(full_ticket_path, 'rb') as fp:
            img = MIMEImage(fp.read(), _subtype="png")
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(full_ticket_path))
            msg.attach(img)

        # 5. Send via SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(config.sender_email, config.sender_app_password)
            smtp.send_message(msg)
            
        print(f"✅ Email with ticket successfully sent to {email}.")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email to {email}: {e}")
        return False
    
def send_confirmation_email(email, first_name, config):
    """Sends a basic 'Form Under Review' email if auto-generate is off."""
    if not config.confirmation_mail_template_url:
        print("⚠️ No confirmation mail template URL provided in config. Skipping.")
        return False
        
    print(f"Sending confirmation email to {email}...")
    media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
    temp_dir = os.path.join(media_root, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    local_email_path = download_file(config.confirmation_mail_template_url, os.path.join(temp_dir, "confirm_msg.html"))
    if not local_email_path:
        return False

    try:
        with open(local_email_path, 'r', encoding='utf-8') as f:
            message_template = f.read()

        email_body = message_template.replace('{name}', first_name or "Participant")
        
        msg = MIMEMultipart()
        msg['From'] = config.sender_email
        msg['To'] = email
        msg['Subject'] = "Registration Received - Under Review" 
        msg.attach(MIMEText(email_body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(config.sender_email, config.sender_app_password)
            smtp.send_message(msg)
            
        print(f"✅ Confirmation email sent to {email}.")
        return True
    except Exception as e:
        print(f"❌ Error sending confirmation email: {e}")
        return False