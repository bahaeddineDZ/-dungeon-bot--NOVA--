import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

cred_json = os.getenv("FIREBASE_CREDENTIAL")
if not cred_json:
    raise Exception("❌ لم يتم العثور على متغير البيئة FIREBASE_CREDENTIAL")

cred_dict = json.loads(cred_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)

db = firestore.client()
