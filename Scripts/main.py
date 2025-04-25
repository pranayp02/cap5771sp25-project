import streamlit as st
from recommend_utils import *
import os
import base64


st.set_page_config(page_title="Book Recommendation System", layout="wide")
create_users_table()

# Background Styling
def set_bg_image(image_path):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    encoded = base64.b64encode(img_bytes).decode()
    bg_style = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(bg_style, unsafe_allow_html=True)

# Session State 
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if 'models' not in st.session_state:
    st.session_state.models = load_models()

# Pages
def home_page():
    set_bg_image("images/home_img.avif")
    st.markdown("""
        <div style='text-align: center;'>
            <h1 style='font-size: 50px;'>Welcome to SmartShelf: Your Personal Book Recommender</h1>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: left;'>
            <h4><b>Discover your next favorite book effortlessly!</b></h4>
            <p>Log in or Sign up to explore personalized recommendations.<br>
            Our system adapts to your reading habits. Search books, rate them, and get smart suggestions.</p>
        </div>
        """, unsafe_allow_html=True)
    
        st.markdown("""
        <div style='text-align: left;'>
            <p><b>Create a new account:</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Signup"):
            st.session_state.page = 'signup'

        st.markdown("""
        <div style='text-align: left; margin-top: 20px;'>
            <p><b>Already have an account?</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Login"):
            st.session_state.page = 'login'

def login_page():
    set_bg_image("images/login_img.png")
    # st.subheader("Login")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.subheader("Login")
        user = st.text_input("Username")
        passwd = st.text_input("Password", type="password")
        if st.button("Login"):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, passwd))
            result = cursor.fetchone()
            conn.close()
            if result:
                st.success("Logged in successfully")
                st.session_state.logged_in = True
                st.session_state.username = user
                st.rerun()
            else:
                st.error("Invalid credentials")

def signup_page():
    set_bg_image("images/signup_img.jpg")
    # st.subheader("Sign Up")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        st.subheader("Sign Up")
        new_user = st.text_input("Choose Username")
        # age = st.text_input("Age")
        new_pass = st.text_input("Create Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")

        st.markdown("""
        **Password must contain:**
        - At least 8 characters
        - One special character (e.g. !,@,#)
        """)

        if st.button("Create Account"):
            if new_pass != confirm_pass:
                st.warning("Passwords do not match.")
            elif len(new_pass) < 8 or not any(char in '!@#$%^&*()_+' for char in new_pass):
                st.warning("Password does not meet complexity requirements.")
            else:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (new_user, new_pass))
                conn.commit()
                conn.close()
                st.success("Account created successfully!")
                st.session_state.page = 'login'
                st.rerun()

def recommendation_page():
    set_bg_image("images/main_img.jpg")

    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "home"
            st.rerun()

    st.title("SmartShelf: Personalized Book Recommender")
    st.markdown("Welcome, **{}**!".format(st.session_state.username))
    models = st.session_state.models

    tab1, tab2 = st.tabs(["Search Books", "Your Ratings"])

    with tab1:
        query = st.text_input("Search a Book Title")
        if query:
            book_df = models['book_level_df_cb']
            matched = book_df[book_df['Book-Title'].str.contains(query, case=False, na=False)]
            if not matched.empty:
                book = matched.iloc[0]
                st.subheader("Book Found:")
                st.image(book['Image-URL-L'], width=150)
                st.write(f"**Title:** {book['Book-Title']}")
                st.write(f"**Author:** {book['Book-Author']}")
                st.write(f"**Publisher:** {book['Publisher']}")
                st.write(f"**Year:** {book['Year-Of-Publication']}")

                rating_input = st.slider("Rate this book (0-10):", 0, 10, 5)
                if st.button("Submit Rating"):
                    save_user_rating(st.session_state.username, book['Book-Title'], rating_input)
                    st.success("Rating saved successfully")

                st.markdown("---")
                st.subheader("Books from the same publisher:")
                publisher_df = publisher_recommendation(book['Book-Title'], models)
                display_books(publisher_df)

                st.markdown("---")
                if st.button("Find similar books"):
                    # st.subheader("Similar books based on rating patterns:")
                    content_df = content_recommendation(book['Book-Title'], models)
                    display_books(content_df)
            else:
                st.warning("No book found for that title.")

    with tab2:
        ratings_df = get_user_ratings(st.session_state.username)
        book_df = models['book_level_df_cb']

        # Merge to include image URLs and metadata
        enriched_df = pd.merge(ratings_df, book_df, how='left', left_on='book_title', right_on='Book-Title')

        st.subheader("Your Ratings")
        for _, row in enriched_df.iterrows():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(row['Image-URL-L'], width=80)
            with col2:
                st.write(f"**{row['book_title']}**")
                new_rating = st.slider("Rating", 0, 10, row['rating'], key=row['book_title'])
                col_upd, col_del = st.columns(2)
                with col_upd:
                    if st.button("Update", key="update_" + row['book_title']):
                        save_user_rating(st.session_state.username, row['book_title'], new_rating)
                        st.success("Updated!")
                with col_del:
                    if st.button("Delete", key="delete_" + row['book_title']):
                        delete_user_rating(st.session_state.username, row['book_title'])
                        st.warning("Deleted")
                        st.rerun()

        st.markdown("---")
        st.subheader("Books Liked by Users Similar to You")
        df = collaborative_recommendation(st.session_state.username, models)
        display_books(df)


def main():
    if not st.session_state.logged_in:
        page = st.session_state.get("page", "home")
        if page == 'home':
            home_page()
        elif page == 'login':
            login_page()
        elif page == 'signup':
            signup_page()
    else:
        recommendation_page()

if __name__ == "__main__":
    main()
