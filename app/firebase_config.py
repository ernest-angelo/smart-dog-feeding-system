import streamlit as st
import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore

# =========================
# FIREBASE INIT
# =========================

if not firebase_admin._apps:

    firebase_credentials = dict(
        st.secrets["firebase"]
    )

    cred = credentials.Certificate(
        firebase_credentials
    )

    firebase_admin.initialize_app(
        cred
    )

# =========================
# FIRESTORE DATABASE
# =========================

db = firestore.client()