import os
import pytz
from datetime import datetime
from google.cloud import firestore
from googleapiclient.discovery import build
from google.oauth2 import service_account
import functions_framework

# Google Sheets and Firestore setup
SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), './service_account_credentials_file.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '[your spreadsheet id]'
# See ID in the link: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
RANGE_NAME = '[your range name]'
# Configuration for accessing Google Sheets.
try:
    DB = firestore.Client()
except Exception as e:
    print(f"Error initializing Firestore client: {e}")
    DB = None


# Initialize Firestore client.

def authenticate_google_sheets():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return None
    # Check if the service account file exists. If not, log an error and return None.

    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        # Load credentials from the service account file.

        return build('sheets', 'v4', credentials=credentials)
        # Build and return the Google Sheets API client.
    except Exception as e:
        print(f"Error during Google Sheets authentication: {e}")
        return None
    # Handle any exceptions that occur during authentication.


def get_firestore_data():
    if not DB:
        print("Firestore client not initialized.")
        return []
    # Check if the Firestore client is initialized. If not, return an empty list.

    try:
        proposals = DB.collection('proposals').stream()
        # Fetch data from the 'proposals' collection in Firestore.

        return [
            {
                'createdAt': datetime.strptime(doc.to_dict()['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
                .replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Kiev'))
                .strftime("%d %b, %Y %H:%M:%S"),
                'scannerName': doc.to_dict().get('scannerName', ''),
                'proposalLink': doc.to_dict().get('proposalLink', '')
            }
            for doc in proposals
        ]
        # Parse and transform the data from Firestore, adjusting the time to the 'Europe/Kiev' timezone.
    except Exception as e:
        print(f"Error fetching data from Firestore: {e}")
        return []
    # Handle exceptions that might occur while fetching data from Firestore.


def get_existing_links(service):
    if not service:
        print("Google Sheets service not initialized.")
        return []
    # Check if the Google Sheets service is initialized. If not, return an empty list.

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=f'{RANGE_NAME}!D:D').execute()
        # Fetch existing links (column D) from the specified range in the Google Sheet.

        return [row[0] for row in result.get('values', []) if row]
        # Return a list of existing links.
    except Exception as e:
        print(f"Error fetching existing links from Google Sheet: {e}")
        return []
    # Handle exceptions that might occur while fetching data from Google Sheets.


def append_to_google_sheet(service, data):
    if not service:
        print("Google Sheets service not initialized.")
        return
    if not data:
        print("No data to append.")
        return
    # Check if the Google Sheets service is initialized and if there is data to append. If not, return early.

    try:
        body = {'values': data}
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption='RAW', insertDataOption='INSERT_ROWS', body=body).execute()
        # Append data to the Google Sheet.
    except Exception as e:
        print(f"Error appending data to Google Sheet: {e}")
    # Handle exceptions that might occur while appending data to Google Sheets.


@functions_framework.http
def firestore_to_sheets(request):
    # Entry point of the Cloud Function

    service = authenticate_google_sheets()
    # Authenticate and initialize the Google Sheets service.

    if not service:
        return 'Google Sheets service authentication failed', 500
    # If authentication fails, return an error message and a 500 status code.

    firestore_data = get_firestore_data()
    if not firestore_data:
        return 'No data fetched from Firestore', 500
    # Fetch data from Firestore. If no data is fetched, return an error message and a 500 status code.

    existing_links = get_existing_links(service)
    if existing_links is None:
        return 'Failed to fetch existing links from Google Sheets', 500
    # Fetch existing links from Google Sheets. If this fails, return an error message and a 500 status code.

    new_values = [
        [record['createdAt'], record['scannerName'], "", record['proposalLink']]
        for record in firestore_data if record['proposalLink'] not in existing_links
    ]
    # Prepare new values for insertion by filtering out records that already exist in the Google Sheet.

    if not new_values:
        return 'No new entries to add to Google Sheets', 200
    # If there are no new entries to add, return a success message and a 200 status code.

    append_to_google_sheet(service, new_values)
    # Append new values to the Google Sheet.

    return 'New entries added to Google Sheets successfully', 200
    # Return a success message and a 200 status code after appending new data.
