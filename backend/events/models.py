from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False, help_text="Mark True when the event is over to move it to past events and revert frontend styling.")
    custom_theme_code = models.TextField(blank=True, help_text="Paste raw CSS or JSON config code here to override the frontend theme for this event.")
    custom_theme_file = models.FileField(upload_to='event_themes/', blank=True, null=True, help_text="Upload a custom theme file (CSS or JSON) for this event.")

    def __str__(self):
        return self.title

class RegistrationForm(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='form')
    google_sheet_link = models.URLField(max_length=500, help_text="Paste the link to the Google Sheet where answers should be saved")
    sheet_name = models.CharField(max_length=100, default="Sheet1", help_text="Usually 'Sheet1' or 'Form Responses 1'")

    def __str__(self):
        return f"Form for {self.event.title}"

class FormField(models.Model):
    FIELD_TYPES = (
        ('text', 'Short Text'),
        ('textarea', 'Long Text'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkbox (Multiple Options)'),
        ('file', 'File Upload (Images/PDFs)'), 
    )
    
    form = models.ForeignKey(RegistrationForm, related_name='fields', on_delete=models.CASCADE)
    label = models.CharField(max_length=200, help_text="The question (e.g., 'Phone Number', 'Upload ID')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    options = models.TextField(blank=True, help_text="If Dropdown or Checkbox, enter options separated by commas (e.g. Option 1, Option 2)")
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.label

class Speaker(models.Model):
    name = models.CharField(max_length=150)
    bio = models.TextField()
    is_revealed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class TicketingConfig(models.Model):
    """Global configuration for the ticketing and email system, editable in Admin."""
    # --- Google Sheets ---
    main_sheet_link = models.URLField(max_length=500, blank=True)
    main_sheet_name = models.CharField(max_length=100, default="Sheet1")
    col_name = models.CharField(max_length=50, default="Name")
    col_email = models.CharField(max_length=50, default="Email ID")
    col_ticket_status = models.CharField(max_length=50, default="Ticket Status")
    col_email_status = models.CharField(max_length=50, default="Email Status")
    
    # --- Email ---
    sender_email = models.EmailField(blank=True)
    sender_app_password = models.CharField(max_length=255, blank=True)
    
    # --- Assets (Drive URLs) ---
    ticket_template_url = models.URLField(max_length=500, blank=True)
    email_message_url = models.URLField(max_length=500, blank=True)
    font_url = models.URLField(max_length=500, blank=True)
    
    # --- Coordinates & Sizes ---
    name_text_x_pos = models.IntegerField(default=1823)
    name_text_y_pos = models.IntegerField(default=299)
    qr_code_x_pos = models.IntegerField(default=1610)
    qr_code_y_pos = models.IntegerField(default=343)
    font_size = models.IntegerField(default=147)
    qr_code_target_size = models.IntegerField(default=260)
    
    # --- MongoDB ---
    mongo_uri = models.CharField(max_length=500, blank=True)
    mongo_db_name = models.CharField(max_length=100, blank=True)
    mongo_collection_name = models.CharField(max_length=100, blank=True)
    
    # --- Google Service Account ---
    google_service_account_json = models.TextField(blank=True)
    
    # --- NEW: Cloudinary Configuration ---
    cloudinary_cloud_name = models.CharField(max_length=100, blank=True, help_text="Your Cloudinary Cloud Name")
    cloudinary_api_key = models.CharField(max_length=100, blank=True, help_text="Your Cloudinary API Key")
    cloudinary_api_secret = models.CharField(max_length=150, blank=True, help_text="Your Cloudinary API Secret")
    
    # ... existing Cloudinary fields ...
    
    # --- NEW: Automation & Status Emails ---
    auto_generate_tickets = models.BooleanField(
        default=False, 
        help_text="If True, tickets are generated and emailed INSTANTLY when a user registers."
    )
    confirmation_mail_template_url = models.URLField(
        max_length=500, blank=True, 
        help_text="Link to the HTML email sent to say 'Your form is under review' (Used if Auto-Generate is OFF)"
    )
    
    class Meta:
        verbose_name = "Ticketing Configuration"
        verbose_name_plural = "Ticketing Configuration"

    def __str__(self):
        return "Global Ticketing Settings"