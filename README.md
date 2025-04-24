Project Title: SMARTSHELF: BOOK RECOMMENDATION SYSTEM USING CONTENT-BASED AND COLLABORATIVE FILTERING TECHINQUES 

This project aims to build a personalized book recommendation system that suggests books to users based on their reading preferences and historical ratings. It combines content-based filtering and collaborative filtering approaches to enhance the accuracy of recommendations. The system takes into account both the metadata of books (such as title, author, and publisher) and user behavior (like previously rated books).

The core functionality is implemented as a web application using Streamlit. Users can sign up, log in, search for book titles, rate books, and receive tailored recommendations. The recommendation engine includes three main strategies: predicting the publisher using a TF-IDF vectorizer and a classification model, recommending similar books using K-Nearest Neighbors on metadata, and collaborative filtering based on user ratings using a user-item matrix.

During Milestone 1, datasets from Kaggle (Books.csv, Ratings.csv, Users.csv) were collected and cleaned. Exploratory Data Analysis (EDA) was performed to understand rating patterns and user-book relationships. In Milestone 2, machine learning models were trained for the three recommendation techniques. Milestone 3 focused on developing an interactive front-end using Streamlit and connecting it to the trained models for real-time recommendations.

This end-to-end project highlights the importance of combining well-engineered features with scalable machine learning models and user-friendly design to build a practical and intelligent recommendation system.


