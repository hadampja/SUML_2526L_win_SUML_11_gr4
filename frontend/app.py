import os
import requests
import pandas as pd
import streamlit as st

# Adres API - lokalnie: http://127.0.0.1:8000
# W docker-compose: http://backend:8000
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Rekomendacje gier Steam", page_icon="🎮")
st.title("🎮 Rekomendacje gier Steam")
st.write("Podaj swój `user_id` ze zbioru danych, aby zobaczyć rekomendowane gry.")

user_id_str = st.text_input("user_id (liczba całkowita):", "")

if st.button("Pobierz rekomendacje"):
    if not user_id_str.strip():
        st.error("Podaj poprawny user_id.")
    else:
        try:
            user_id = int(user_id_str)
        except ValueError:
            st.error("user_id musi być liczbą całkowitą.")
        else:
            try:
                resp = requests.get(f"{API_URL}/users/{user_id}/recommendations", timeout=10)
            except requests.RequestException as e:
                st.error(f"Nie udało się połączyć z API: {e}")
            else:
                if resp.status_code == 404:
                    st.warning("Brak rekomendacji dla tego użytkownika.")
                elif resp.status_code != 200:
                    st.error(f"Błąd API: {resp.status_code} — {resp.text}")
                else:
                    data = resp.json()
                    recs = pd.DataFrame(data["recommendations"])
                    st.subheader(f"Top {data['n_recommendations']} gier dla użytkownika {data['user_id']}")
                    st.dataframe(recs)
