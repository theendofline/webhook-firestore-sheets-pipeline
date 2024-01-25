import functions_framework
import flask
import time
import pytz
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.cloud import firestore

# Initialize Firestore client for database operations.
db = firestore.Client()


def authenticate_google_sheets():
    """
    Authenticates with Google Sheets API using service account credentials.
    Returns a service object that can be used to interact with the Google Sheets API.
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = './service_account_credentials_file.json'  # Path to service account credentials file.
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=credentials)


def store_data_in_firestore(proposal_data):
    """
    Stores proposal data in Firestore under the 'proposals' collection.

    Parameters:
    proposal_data (dict): Contains the proposal information to be stored.
    """
    # Check if the required 'scannerName' field is present in the proposal data.
    if 'scannerName' in proposal_data:
        uid = proposal_data['uid']

        # The POST data we receive is a string with a number, and we need a link
        # to the proposal, so here we convert this to the required format
        proposalLink = f"https://www.third_party_service.com/ab/proposals/{uid}"

        # Firestore document ID is set to the proposal's UID for easy referencing.
        document_id = uid

        # Prepare the data for Firestore, including a link to the proposal and creation timestamp.
        firestore_data = {
            'proposalLink': proposalLink,
            'createdAt': proposal_data['createdAt'],
            'scannerName': proposal_data['scannerName'],
            # Additional fields can be included as needed.
        }

        # Store the data in Firestore under the 'proposals' collection.
        db.collection('proposals').document(document_id).set(firestore_data)


def reconcile_with_google_sheet(service, SPREADSHEET_ID, RANGE_NAME):
    """
    Reconciles Firestore data with a Google Sheet, appending new entries.

    Parameters:
    service: The authenticated Google Sheets service object.
    SPREADSHEET_ID (str): The ID of the Google Sheet to update.
    RANGE_NAME (str): The range within the sheet to fetch existing links.
    """
    # Fetch existing entries from the specified range in the Google Sheet.
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    existing_links = {row[3] for row in result.get('values', []) if len(row) > 3}

    # Retrieve new proposal data from Firestore, ordering by creation time.
    proposals = db.collection('proposals').order_by('createdAt').stream()

    new_values = []  # List to hold data for new proposals not yet in the Google Sheet.
    for proposal in proposals:
        data = proposal.to_dict()
        if data['proposalLink'] not in existing_links:
            # Convert UTC 'createdAt' timestamp to 'Europe/Kiev' timezone.
            createdAt_kyiv = datetime.strptime(data['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Kiev'))
            createdAt_formatted = createdAt_kyiv.strftime("%d %b, %Y %H:%M:%S")
            new_values.append([createdAt_formatted, data.get('scannerName'), "", data['proposalLink']])

    # Sort new_values by date and time before appending to Google Sheet
    new_values.sort(key=lambda x: datetime.strptime(x[0], "%d %b, %Y %H:%M:%S"))

    # Append new unique data to the Google Sheet if there are any new entries.
    if new_values:
        service.spreadsheets().values().append(
            # ! Be sure to link the insert to the first column. If you do not do this, each new row in the table
            # will be inserted with an offset/shift of 3 columns to the right.
            spreadsheetId=SPREADSHEET_ID, range='{RANGE_NAME}!A:A',
            valueInputOption='RAW', insertDataOption='INSERT_ROWS', body={'values': new_values}
        ).execute()


def webhook_to_sheets(request):
    """
    Endpoint for a webhook that processes POST requests containing proposal data,
    stores it in Firestore, and reconciles it with a Google Sheet.

    Parameters:
    request: The Flask request object containing the incoming webhook data.
    """
    if request.method == 'POST':
        data = request.get_json(silent=True)  # Extract JSON data from the request.
        proposal_data = data.get('data', {}).get('proposal', {})

        # Validate the presence of required data fields.
        if not proposal_data.get('createdAt') or not proposal_data.get('scannerName') or not proposal_data.get('uid'):
            return flask.jsonify(error="Missing required proposal data"), 400

        # Store the proposal data in Firestore.
        store_data_in_firestore(proposal_data)

        # Introduce a pause of 10 seconds
        time.sleep(10)

        # Authenticate and prepare to reconcile the data with Google Sheets.
        service = authenticate_google_sheets()
        SPREADSHEET_ID = 'your_spreadsheet_id_here'
        RANGE_NAME = 'your_range_name_here'
        reconcile_with_google_sheet(service, SPREADSHEET_ID, RANGE_NAME)

        # Respond to the webhook sender that the data was processed successfully.
        return flask.jsonify(success=True, message="Data processed successfully.")
    else:
        # Respond with an error if the request method is not POST.
        return 'This function only responds to POST requests.', 405
