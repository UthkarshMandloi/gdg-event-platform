import os
import uuid
import requests
import qrcode
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings

def download_file(url, local_filename):
    """Downloads a file from a URL (handles Google Drive links)."""
    if not url:
        print(f"❌ URL is empty for {local_filename}")
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
        print(f"✅ Successfully downloaded '{local_filename}'")
        return local_filename
    except Exception as e:
        print(f"❌ Error downloading file from {url}: {e}")
        return None

def generate_qr_code(data: str, file_path: str, size: int, corner_radius: int) -> bool:
    """Generates and saves a QR code image with rounded corners."""
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        # Resize using updated Pillow resample method
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.LANCZOS # Fallback for older Pillow versions
            
        img = img.resize((size, size), resample_filter)

        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size, size), radius=corner_radius, fill=255)

        img.putalpha(mask)
        img.save(file_path)
        print(f"✅ QR code generated: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error generating QR code: {e}")
        return False

def generate_ticket(email, first_name, last_name, config):
    """
    Main function called by Django Admin to generate a personalized ticket.
    Returns the relative path for the Django FileField.
    """
    full_name = f"{first_name} {last_name}".strip() or "Attendee"
    print(f"Generating ticket for {full_name} ({email})...")
    
    # 1. Setup Directories based on Django's MEDIA_ROOT
    media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
    temp_dir = os.path.join(media_root, 'temp')
    tickets_dir = os.path.join(media_root, 'tickets')
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(tickets_dir, exist_ok=True)
    
    # 2. Download Assets using the Admin Config URLs
    local_template_path = download_file(config.ticket_template_url, os.path.join(temp_dir, "template.png"))
    local_font_path = download_file(config.font_url, os.path.join(temp_dir, "font.ttf"))
    
    if not local_template_path or not local_font_path:
        print("❌ Critical error: Font or template download failed. Cannot create ticket.")
        return None
        
    # 3. Generate QR Code
    qr_filename = f"qr_{email.split('@')[0]}.png"
    qr_path = os.path.join(temp_dir, qr_filename)
    unique_attendee_id = str(uuid.uuid4()) # Create a unique ID for the QR code
    
    if not generate_qr_code(unique_attendee_id, qr_path, config.qr_code_target_size, 30):
        return None

    # 4. Create the final Ticket Image
    ticket_filename = f"ticket_{email.split('@')[0]}.png"
    relative_path = f"tickets/{ticket_filename}"
    full_ticket_path = os.path.join(media_root, relative_path)

    try:
        base_img = Image.open(local_template_path).convert("RGBA")
        draw = ImageDraw.Draw(base_img)

        # Draw the Name
        try:
            font = ImageFont.truetype(local_font_path, int(config.font_size))
        except (IOError, TypeError):
            print("⚠️ Warning: Font could not be loaded. Using default.")
            font = ImageFont.load_default()
            
        text_y = int(config.name_text_y_pos)
        text_x = int(config.name_text_x_pos)
        
        # Using the standard RGB black (17, 17, 17) from your original config
        draw.text((text_x, text_y), full_name, font=font, fill=(17, 17, 17), anchor="mt")

        # Paste the QR Code
        qr_img = Image.open(qr_path).convert("RGBA")
        qr_y = int(config.qr_code_y_pos)
        qr_x = int(config.qr_code_x_pos)
        base_img.paste(qr_img, (qr_x, qr_y), qr_img)

        base_img.save(full_ticket_path)
        print(f"✅ Personalized ticket created: {full_ticket_path}")
        
        # Cleanup temporary files
        if os.path.exists(qr_path): os.remove(qr_path)
        
        return relative_path

    except Exception as e:
        print(f"❌ Error creating ticket image: {e}")
        return None