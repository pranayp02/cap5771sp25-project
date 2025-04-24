import streamlit as st
import sqlite3
import pandas as pd
import re
import base64
from sklearn.neighbors import NearestNeighbors

DB_NAME = 'users.db'

# ---------- Background Image Setup ----------
def set_background(image_path: str):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded_image}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------- Database Setup ----------
def create_users_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        age INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_ratings (
                        username TEXT,
                        book_title TEXT,
                        rating INTEGER,
                        PRIMARY KEY (username, book_title))''')
    conn.commit()
    conn.close()

# ---------- Password Validation ----------
def validate_password(password):
    return (len(password) >= 8 and
            re.search(r"[A-Z]", password) and
            re.search(r"[a-z]", password) and
            re.search(r"[0-9]", password) and
            re.search(r"[^a-zA-Z0-9]", password))

# ---------- Signup Page ----------
def signup_user():
    set_background("assets/signup_bg.jpg")
    st.subheader("Create a New Account")
    new_user = st.text_input("Username")
    age = st.number_input("Age", min_value=5, max_value=100, step=1)
    st.markdown("Password must be at least 8 characters long and include uppercase, lowercase, numbers, and symbols.")
    new_pass = st.text_input("Create Password", type='password')
    confirm_pass = st.text_input("Confirm Password", type='password')

    if st.button("Sign Up"):
        if new_pass != confirm_pass:
            st.error("Passwords do not match.")
        elif not validate_password(new_pass):
            st.error("Password does not meet the strength requirements.")
        elif not new_user or not new_pass:
            st.error("Please fill in all fields.")
        else:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (username, password, age) VALUES (?, ?, ?)", (new_user, new_pass, age))
            conn.commit()
            conn.close()
            st.success("Account created successfully! Please login.")

# ---------- Login Page ----------
def login_user():
    set_background("assets/login_bg.jpg")
    st.subheader("Login to Your Account")
    user = st.text_input("Username")
    passwd = st.text_input("Password", type='password')
    if st.button("Login"):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user, passwd))
        data = cursor.fetchone()
        conn.close()
        if data:
            st.success(f"Welcome, {user}!")
            st.session_state.username = user
            return True
        else:
            st.error("Incorrect Username or Password")
    return False

# ---------- Main Home Page ----------
def main_home():
    set_background("assets/home_bg.jpg")
    st.markdown("""<h1 style='text-align: center; color: white;'>Welcome to SmartShelf</h1>""", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            st.session_state.page = "login"
    with col2:
        if st.button("Sign Up"):
            st.session_state.page = "signup"

# ---------- Routing ----------
def main():
    st.set_page_config(page_title="Book Recommender", layout="wide")
    create_users_table()

    if 'page' not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "home":
        main_home()
    elif st.session_state.page == "login":
        if login_user():
            st.session_state.page = "main"
    elif st.session_state.page == "signup":
        signup_user()
    elif st.session_state.page == "main":
        from recommend_utils import unified_interface
        unified_interface(st.session_state.username)

if __name__ == "__main__":
    main()
