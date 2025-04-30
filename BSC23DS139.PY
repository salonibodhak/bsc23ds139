import streamlit as st
import sqlite3, os, time, hashlib
from cryptography.fernet import Fernet

# --- Setup Encryption ---
KEY_FILE = "fernet.key"
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f: f.write(Fernet.generate_key())
with open(KEY_FILE, "rb") as f: KEY = f.read()
cipher = Fernet(KEY)

# --- Setup Database ---
def init_db():
    with sqlite3.connect("ledger.db") as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                encrypted TEXT,
                hash TEXT,
                prev_hash TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_time ON ledger(timestamp)')

def compute_hash(data, prev_hash):
    return hashlib.sha256((data + (prev_hash or '')).encode()).hexdigest()

def add_entry(data):
    enc = cipher.encrypt(data.encode()).decode()
    with sqlite3.connect("ledger.db") as conn:
        cur = conn.execute("SELECT hash FROM ledger ORDER BY id DESC LIMIT 1")
        prev = cur.fetchone()
        prev_hash = prev[0] if prev else None
        h = compute_hash(enc, prev_hash)
        conn.execute("INSERT INTO ledger (timestamp, encrypted, hash, prev_hash) VALUES (?, ?, ?, ?)",
                     (time.strftime("%Y-%m-%d %H:%M:%S"), enc, h, prev_hash))

def get_entries():
    with sqlite3.connect("ledger.db") as conn:
        return [(ts, cipher.decrypt(ed.encode()).decode()) for ts, ed in
                conn.execute("SELECT timestamp, encrypted FROM ledger ORDER BY id DESC LIMIT 10")]

# --- Streamlit App ---
st.set_page_config("Secure Ledger")
st.title("🔐 Secure Performance Ledger")
init_db()

entry = st.text_area("Enter performance data:")
if st.button("Add Entry") and entry.strip():
    add_entry(entry.strip())
    st.success("Entry added securely!")

st.subheader("Recent Entries")
for ts, data in get_entries():
    st.write(f"**{ts}**
