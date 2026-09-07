import os
import firebase_admin
from firebase_admin import credentials, firestore

# Путь к ключу firebase_key.json в корне проекта
KEY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase_key.json')

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()
