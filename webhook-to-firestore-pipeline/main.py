from flask import jsonify
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import firestore

# Importing necessary libraries. Flask for creating a web server, jsonify to format responses as JSON,
# and Firestore to interact with Google Firestore database.

# Initialize Firestore client
try:
    db = firestore.Client()
except Exception as e:
    print(f"Error initializing Firestore client: {e}")
    db = None


# Try to initialize the Firestore client. If it fails, catch the exception, print the error, and set 'db' to None.

def store_data_in_firestore(proposal_data):
    if not db:
        print("Firestore client not initialized.")
        return False
    # If the Firestore client is not initialized, log a message and return False.

    try:
        if 'scannerName' in proposal_data and 'uid' in proposal_data:
            uid = proposal_data['uid']
            proposalLink = f"https://3rd_party_service_link/{uid}"
            document_id = uid
            firestore_data = {
                'proposalLink': proposalLink,
                'createdAt': proposal_data['createdAt'],
                'scannerName': proposal_data['scannerName'],
            }
            # Validate if necessary data is present. Then, create a Firestore data document with proposal link,
            # creation time, and scanner name.

            db.collection('proposals').document(document_id).set(firestore_data)
            # Store the document in the Firestore 'proposals' collection with 'uid' as the document ID.

            return True
        else:
            print("Missing required fields in proposal data.")
            return False
    except GoogleAPICallError as e:
        print(f"Error storing data in Firestore: {e}")
        return False
    # Catch exceptions specific to Firestore API calls. If an error occurs, log it and return False.


def webhook_to_firestore(request):
    if request.method != 'POST':
        return jsonify(error="This function only responds to POST requests."), 405
    # This function only accepts POST requests. If the request is not POST, return an error message with a 405 HTTP
    # status code.

    data = request.get_json(silent=True)
    proposal_data = data.get('data', {}).get('proposal', {})
    # Extract JSON data from the request. If the data is not properly formatted, it defaults to an empty dictionary.

    if not proposal_data or not proposal_data.get('createdAt') or not proposal_data.get(
            'scannerName') or not proposal_data.get('uid'):
        return jsonify(error="Missing required proposal data"), 400
    # Check for required fields in the proposal data. If any are missing, return an error message with a 400 HTTP
    # status code.

    if not db:
        return jsonify(error="Firestore client not initialized, cannot process request."), 500
    # If the Firestore client is not initialized, return an error message with a 500 HTTP status code.

    if store_data_in_firestore(proposal_data):
        return jsonify(success=True, message="Data stored in Firestore successfully.")
    else:
        return jsonify(error="Failed to store data in Firestore."), 500
    # Attempt to store the data in Firestore using the 'store_data_in_firestore' function. Respond
    # with a success or error message based on the outcome.
