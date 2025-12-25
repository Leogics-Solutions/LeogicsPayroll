import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Check if credentials are in environment variable (production)
firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')

if firebase_creds:
    # Production: load from environment variable
    cred_dict = json.loads(firebase_creds)
    cred = credentials.Certificate(cred_dict)
else:
    # Local development: load from file
    cred = credentials.Certificate('firebase-credentials.json')

firebase_admin.initialize_app(cred)
db = firestore.client()