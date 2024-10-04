import flask
from flask import jsonify
from google.cloud import firestore
from google.api_core.exceptions import GoogleAPICallError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firestore client
try:
    db = firestore.Client()
    logger.info("Firestore client initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing Firestore client: {e}")
    db = None

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten nested dictionaries, creating keys with separator.
    
    Args:
        d (dict): The dictionary to flatten
        parent_key (str): The string to prepend to dictionary's keys
        sep (str): The string used to separate flattened keys
    
    Returns:
        dict: A flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def store_data_in_firestore(data):
    """
    Store all data in Firestore, handling any structure.
    
    Args:
        data (dict): Dictionary containing all the data from the webhook
    
    Returns:
        bool: True if data was successfully stored, False otherwise
    """
    if not db:
        logger.error("Firestore client not initialized.")
        return False

    try:
        # Flatten the entire data structure
        flat_data = flatten_dict(data)
        logger.info("Data flattened successfully.")
        
        # Extract UID (assuming it's always present in data_proposal_uid)
        uid = flat_data.get('data_proposal_uid')
        if not uid:
            logger.error("Missing required 'uid' in proposal data.")
            return False

        # Store flattened data in Firestore
        db.collection('proposals').document(uid).set(flat_data)
        logger.info(f"Data stored successfully in Firestore with UID: {uid}")
        return True
    except GoogleAPICallError as e:
        logger.error(f"Error storing data in Firestore: {e}")
        return False

def webhook_to_firestore(request):
    """
    Handle webhook requests and store all data in Firestore.
    
    Args:
        request (flask.Request): Flask request object
    
    Returns:
        tuple: JSON response and HTTP status code
    """
    logger.info("Received webhook request.")

    if request.method != 'POST':
        logger.warning("Received non-POST request.")
        return jsonify(error="This function only responds to POST requests."), 405

    data = request.get_json(silent=True)
    if not data:
        logger.error("Received invalid JSON data.")
        return jsonify(error="Invalid JSON data."), 400

    if not db:
        logger.error("Firestore client not initialized, cannot process request.")
        return jsonify(error="Firestore client not initialized, cannot process request."), 500

    logger.info("Processing webhook data...")
    if store_data_in_firestore(data):
        logger.info("Data successfully stored in Firestore.")
        return jsonify(success=True, message="Data stored in Firestore successfully."), 200
    else:
        logger.error("Failed to store data in Firestore.")
        return jsonify(error="Failed to store data in Firestore."), 500

# Uncomment these lines if you're running the app locally with Flask
# app = flask.Flask(__name__)
# 
# @app.route('/', methods=['POST'])
# def index():
#     return webhook_to_firestore(flask.request)
# 
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8080, debug=True)
