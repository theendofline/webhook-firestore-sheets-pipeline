import flask
from flask import jsonify
from google.cloud import firestore
from google.api_core.exceptions import GoogleAPICallError

# Initialize Firestore client
try:
    db = firestore.Client()
except Exception as e:
    print(f"Error initializing Firestore client: {e}")
    db = None

def store_data_in_firestore(proposal_data):
    """
    Store proposal data in Firestore.
    
    Args:
        proposal_data (dict): Dictionary containing proposal information
    
    Returns:
        bool: True if data was successfully stored, False otherwise
    """
    if not db:
        print("Firestore client not initialized.")
        return False

    try:
        # Check if required fields are present
        if 'scannerName' in proposal_data and 'uid' in proposal_data:
            uid = proposal_data['uid']
            proposalLink = f"https://www.upwork.com/ab/proposals/{uid}"
            document_id = uid
            
            # Prepare data for Firestore
            firestore_data = {
                'proposalLink': proposalLink,
                'createdAt': proposal_data['createdAt'],
                'scannerName': proposal_data['scannerName'],
            }
            
            # Store data in Firestore
            db.collection('proposals').document(document_id).set(firestore_data)
            return True
        else:
            print("Missing required fields in proposal data.")
            return False
    except GoogleAPICallError as e:
        print(f"Error storing data in Firestore: {e}")
        return False

def webhook_to_firestore(request):
    """
    Handle webhook requests and store data in Firestore.
    
    Args:
        request (flask.Request): Flask request object
    
    Returns:
        tuple: JSON response and HTTP status code
    """
    # Ensure the request method is POST
    if request.method != 'POST':
        return jsonify(error="This function only responds to POST requests."), 405

    # Parse JSON data from the request
    data = request.get_json(silent=True)
    if not data:
        return jsonify(error="Invalid JSON data"), 400

    # Extract relevant data from the request
    data_content = data.get('data', {})
    proposal_data = data_content.get('proposal', {})
    scanner_name = data_content.get('scannerName')

    # Validate required fields
    if not proposal_data:
        return jsonify(error="Missing 'proposal' data"), 400
    if not proposal_data.get('createdAt'):
        return jsonify(error="Missing 'createdAt' in proposal data"), 400
    if not proposal_data.get('uid'):
        return jsonify(error="Missing 'uid' in proposal data"), 400
    if not scanner_name:
        return jsonify(error="Missing 'scannerName' in data"), 400

    # Check if Firestore client is initialized
    if not db:
        return jsonify(error="Firestore client not initialized, cannot process request."), 500

    # Add 'scannerName' to 'proposal_data'
    proposal_data['scannerName'] = scanner_name

    # Attempt to store data in Firestore
    if store_data_in_firestore(proposal_data):
        return jsonify(success=True, message="Data stored in Firestore successfully.")
    else:
        return jsonify(error="Failed to store data in Firestore."), 500
