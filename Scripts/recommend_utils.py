import sqlite3
import pandas as pd
import streamlit as st
from sklearn.neighbors import NearestNeighbors
import pickle
import base64
import pickle

DB_NAME = 'users.db'

# ---------- USER DB FUNCTIONS ----------
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

# ---------- RECOMMENDATION LOGIC ----------
@st.cache_data



def load_models():
    models = {}
    with open("models/vectorizer.pkl", "rb") as f:
        models["vectorizer"] = pickle.load(f)
    with open("models/vectorizer_cb.pkl", "rb") as f:
        models["vectorizer_cb"] = pickle.load(f)
    with open("models/model_cb.pkl", "rb") as f:
        models["model_cb"] = pickle.load(f)
    with open("models/publisher_model.pkl", "rb") as f:  # ✅ THIS is missing in your error case
        models["publisher_model"] = pickle.load(f)
    with open("models/knn_collaborative_model.pkl", "rb") as f:
        models["knn_collaborative_model"] = pickle.load(f)
    with open("models/book_level_df_cb.pkl", "rb") as f:
        models["book_level_df_cb"] = pickle.load(f)
    with open("models/user_item_matrix.pkl", "rb") as f:
        models["user_item_matrix"] = pickle.load(f)
    with open("models/user_item_columns.pkl", "rb") as f:
        models["user_item_columns"] = pickle.load(f)
    with open("models/book_indices_cb.pkl", "rb") as f:
        models["book_indices_cb"] = pickle.load(f)

    return models


def save_user_rating(username, book_title, rating):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO user_ratings (username, book_title, rating) VALUES (?, ?, ?)", (username, book_title, rating))
    conn.commit()
    conn.close()

def get_user_ratings(username):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM user_ratings WHERE username = ?", conn, params=(username,))
    conn.close()
    return df

def delete_user_rating(username, book_title):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_ratings WHERE username = ? AND book_title = ?", (username, book_title))
    conn.commit()
    conn.close()

def publisher_recommendation(book_title, models):
    pub_model = models['publisher_model']
    vectorizer = models['vectorizer']
    book_df = models['book_level_df_cb']

    vec = vectorizer.transform([book_title])
    pred_publisher = pub_model.predict(vec)[0]

    recs = book_df[book_df['Publisher'] == pred_publisher]
    recs = recs.drop_duplicates(subset="Book-Title").head(6)
    return recs


def content_recommendation(book_title, models, top_n=5):
    book_indices = models['book_indices_cb']
    book_df = models['book_level_df_cb']
    model = models['model_cb']
    tfidf_matrix = model._fit_X

    if book_title not in book_indices:
        return []
    idx = book_indices[book_title]
    distances, indices = model.kneighbors(tfidf_matrix[idx], n_neighbors=top_n+5)
    recommendations = []
    for i in indices[0]:
        candidate = book_df.iloc[i]
        if candidate['Book-Title'] != book_title and candidate['Book-Title'] not in [r['Book-Title'] for r in recommendations]:
            recommendations.append(candidate)
        if len(recommendations) == top_n:
            break
    return pd.DataFrame(recommendations)[['Book-Title', 'Book-Author', 'Publisher', 'Image-URL-L']]

def collaborative_recommendation(username, models, top_n=5):
    user_item_matrix = models['user_item_matrix']
    knn_model = models['knn_collaborative_model']
    user_ratings = get_user_ratings(username)

    if user_ratings.empty:
        return pd.DataFrame()

    real_user_ratings = dict(zip(user_ratings['book_title'], user_ratings['rating']))
    real_user_df = pd.DataFrame([real_user_ratings])
    real_user_df = real_user_df.reindex(columns=user_item_matrix.columns, fill_value=0)
    distances, indices = knn_model.kneighbors(real_user_df, n_neighbors=5)
    similar_users = user_item_matrix.iloc[indices[0]].index.tolist()
    similar_ratings = user_item_matrix.loc[similar_users]
    avg_ratings = similar_ratings.mean().sort_values(ascending=False)
    already_rated = set(real_user_ratings.keys())
    final_recommendations = avg_ratings[~avg_ratings.index.isin(already_rated)].head(top_n)

    df = models['book_level_df_cb']
    return df[df['Book-Title'].isin(final_recommendations.index)][['Book-Title', 'Book-Author', 'Publisher', 'Image-URL-L']]

def display_books(df):
    for idx in range(0, len(df), 3):
        row = st.columns(3)
        for i, col in enumerate(row):
            if idx + i < len(df):
                book = df.iloc[idx + i]
                with col:
                    st.image(book['Image-URL-L'], width=150)
                    st.markdown(f"**{book['Book-Title']}**")
                    st.caption(f"{book['Book-Author']} — {book['Publisher']}")
