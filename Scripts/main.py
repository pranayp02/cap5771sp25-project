import streamlit as st
import pandas as pd
import pickle
from utils.recommend_utils import (
    create_users_table, signup_user, login_user, user_ratings_profile,
    save_user_rating, get_user_ratings
)

# Load model artifacts
book_indices_cb = pickle.load(open("models/book_indices_cb.pkl", "rb"))
book_level_df_cb = pickle.load(open("models/book_level_df_cb.pkl", "rb"))
model_cb = pickle.load(open("models/model_cb.pkl", "rb"))
vectorizer_cb = pickle.load(open("models/vectorizer_cb.pkl", "rb"))
pub_model = pickle.load(open("models/publisher_model.pkl", "rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))
book_data = book_level_df_cb  # this is used in both content-based and collaborative

# Initial setup
create_users_table()

st.set_page_config(page_title="📚 Book Recommendation System", layout="wide")

if 'username' not in st.session_state:
    st.session_state.username = None


def show_home():
    st.title("📚 Welcome to SmartShelf")
    st.write("Discover books tailored to your preferences. Please login or sign up to get started.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            st.session_state.page = "login"
    with col2:
        if st.button("Sign Up"):
            st.session_state.page = "signup"


def search_books():
    st.title("🔍 Search Books")
    title_input = st.text_input("Enter book title keyword")
    if title_input:
        matches = book_data[book_data['Book-Title'].str.contains(title_input, case=False, na=False)]
        if matches.empty:
            st.warning("No book found!")
        else:
            for _, row in matches.iterrows():
                st.image(row['Image-URL-L'], width=120)
                st.markdown(f"### {row['Book-Title']}")
                st.caption(f"Author: {row['Book-Author']} | Publisher: {row['Publisher']} | Year: {row['Year-Of-Publication']}")
                st.write("---")
                st.write("📌 Want to interact with this book?")
                col1, col2 = st.columns([1, 2])
                with col1:
                    if st.button(f"📖 I Read This", key=f"read_{row['Book-Title']}"):
                        idx = book_indices_cb.get(row['Book-Title'])
                        if idx is not None:
                            distances, indices = model_cb.kneighbors(vectorizer_cb.transform([str(row['Book-Rating'])]), n_neighbors=6)
                            book_ids = [i for i in indices[0] if book_data.iloc[i]['Book-Title'] != row['Book-Title']][:5]
                            st.subheader("📚 You might also like:")
                            rec_cols = st.columns(3)
                            for i, rec_id in enumerate(book_ids):
                                rec = book_data.iloc[rec_id]
                                with rec_cols[i % 3]:
                                    st.image(rec['Image-URL-L'], width=120)
                                    st.markdown(f"**{rec['Book-Title']}**")
                                    st.caption(f"by {rec['Book-Author']}, {rec['Publisher']}")
                with col2:
                    rating = st.slider(f"Rate this book: {row['Book-Title']}", 0, 10, key=f"rate_{row['Book-Title']}")
                    if st.button("Submit Rating", key=f"submit_{row['Book-Title']}"):
                        save_user_rating(st.session_state.username, row['Book-Title'], rating)
                        st.success("Thanks for rating!")


def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    if st.session_state.username:
        st.sidebar.success(f"Logged in as: {st.session_state.username}")
        if st.sidebar.button("Home"):
            st.session_state.page = 'search'
        if st.sidebar.button("Your Ratings"):
            st.session_state.page = 'ratings'
        if st.sidebar.button("Logout"):
            st.session_state.username = None
            st.session_state.page = 'home'
            st.rerun()

    if st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'login':
        if login_user():
            st.session_state.page = 'search'
            st.rerun()
    elif st.session_state.page == 'signup':
        signup_user()
    elif st.session_state.page == 'search':
        search_books()
    elif st.session_state.page == 'ratings':
        user_ratings_profile(st.session_state.username, book_data)


if __name__ == '__main__':
    main()
