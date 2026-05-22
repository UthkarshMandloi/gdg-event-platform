import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

class GSheetsHelper:
    def __init__(self, config, custom_sheet_link=None, custom_sheet_name=None):
        self.config = config
        try:
            cred_dict = json.loads(config.google_service_account_json)
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
            self.service = build('sheets', 'v4', credentials=creds)
            
            # Use the form's specific sheet link if provided, otherwise use the global one
            link_to_use = custom_sheet_link if custom_sheet_link else config.main_sheet_link
            self.spreadsheet_id = link_to_use.split('/d/')[1].split('/')[0]
            self.sheet_name = custom_sheet_name if custom_sheet_name else config.main_sheet_name
            
        except Exception as e:
            raise Exception(f"Google Sheets Connection Failed: {e}")

    # CRITICAL FIX: Re-added the missing get_headers function!
    def get_headers(self):
        """Fetches the first row (headers) of the sheet."""
        range_name = f"{self.sheet_name}!1:1"
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        return result.get('values', [[]])[0]

    def sync_sheet_headers(self, custom_field_labels):
        target_headers = [
            self.config.col_name,
            self.config.col_email,
            "Attendee ID",
            self.config.col_ticket_status,
            self.config.col_email_status
        ]
        target_headers.extend(custom_field_labels)

        range_name = f"{self.sheet_name}!1:1"
        
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        current_headers = result.get('values', [[]])[0] if result.get('values') else []

        if current_headers != target_headers:
            body = {'values': [target_headers]}
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            print("[GSheets] Header row updated successfully to match form fields.")
            return True, target_headers
            
        return False, target_headers

    def append_attendee(self, attendee_data):
        headers = self.get_headers()
        row_data = []
        
        for header in headers:
            row_data.append(attendee_data.get(header, ""))
            
        body = {'values': [row_data]}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self.sheet_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        print(f"[GSheets] Appended new attendee: {attendee_data.get(self.config.col_email)}")

    def update_attendee_status(self, email, ticket_status, email_status):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=self.sheet_name).execute()
        values = result.get('values', [])
        
        if not values: return False
        
        headers = values[0]
        try:
            email_col_idx = headers.index(self.config.col_email)
            ticket_col_idx = headers.index(self.config.col_ticket_status)
            email_status_col_idx = headers.index(self.config.col_email_status)
        except ValueError:
            return False

        for i, row in enumerate(values):
            if i > 0 and len(row) > email_col_idx and row[email_col_idx] == email:
                cell_range_t = f"{self.sheet_name}!{chr(ord('A') + ticket_col_idx)}{i + 1}"
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id, range=cell_range_t,
                    valueInputOption='RAW', body={'values': [[ticket_status]]}
                ).execute()
                
                cell_range_e = f"{self.sheet_name}!{chr(ord('A') + email_status_col_idx)}{i + 1}"
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id, range=cell_range_e,
                    valueInputOption='RAW', body={'values': [[email_status]]}
                ).execute()
                return True
                
        return False