# Steam Game Recommender (`ai_project_s28551_s26302`)

System rekomendacji gier Steam zbudowany na publicznym zbiorze `steam-200k`.
Glownym modelem projektu jest item-based collaborative filtering: aplikacja
buduje podobienstwo gier na podstawie historii grania uzytkownikow i serwuje
Top-5 rekomendacji przez FastAPI oraz prosty interfejs Streamlit.

> Projekt zaliczeniowy z przedmiotu SUML, PJATK, lato 2026.

## Architektura

```text
data/raw/steam-200k.csv
        |
        v
Kedro: eda -> preprocessing -> modeling -> evaluation
        |
        v
data/reporting/recommendations_top5.csv
data/reporting/recommender_metrics.json
        |
        v
FastAPI backend -> Streamlit frontend
```

Podzial zgodny z wymaganiem `data | model | app`:

| Warstwa | Lokalizacja | Odpowiedzialnosc |
|---|---|---|
| data | `conf/`, `src/ai_project_s28551/pipelines/eda`, `pipelines/preprocessing` | wczytanie danych, EDA, czyszczenie, split danych |
| model | `src/ai_project_s28551/pipelines/modeling`, `pipelines/evaluation` | budowa rekomendacji item-CF i ewaluacja Precision@K / Recall@K |
| app | `app/main.py`, `frontend/app.py` | API REST i interfejs uzytkownika |

## Wyniki modelu

Pipeline raportuje metryki rekomendera w `data/reporting/recommender_metrics.json`.
Dla Top-5 rekomendacji liczone sa:

| Metryka | Znaczenie |
|---|---|
| `precision_at_k` | jaka czesc rekomendacji trafia w gry z hold-out |
| `recall_at_k` | jaka czesc gier z hold-out zostala odzyskana w rekomendacjach |
| `coverage` | jaka czesc katalogu gier pojawia sie w rekomendacjach |
| `users_evaluated` | liczba uzytkownikow uzytych w ewaluacji |
| `users_with_recommendations` | liczba uzytkownikow z wygenerowanymi rekomendacjami |
| `unique_recommended_games` | liczba unikalnych gier w wynikach |

Projekt nie raportuje klasyfikatora z `accuracy=1.0`, poniewaz poprzednia wersja
tworzyla target z tej samej kolumny, ktora byla cecha modelu. Aktualna wersja
skupia sie na realistycznej ewaluacji systemu rekomendacji.

## Wymagania systemowe
Wymagane do poprawnego działania aplikacji 
- Python 3.11 lub 3.12
- opcjonalnie Finch albo Docker do uruchomienia w kontenerach

## requirements
- zaleznosci runtime w `requirements.txt`
- narzedzia developerskie w `requirements-dev.txt`

## Uruchomienie lokalne - Windows
Aplikacja zawiera pliki uruchumieniowe Windows:
- `run_windows.bat` - plik uruchomieniowy
- `run_windows.ps1` - plik pomocniczy

Dzialanie skryptu
- sprawdza dostępność wymaganej wersji Pythona,
- tworzy środowisko wirtualne .venv,
- instaluje zależności z pliku requirements.txt,
- uruchamia pipeline Kedro,
- uruchamia backend FastAPI,
- uruchamia frontend Streamlit.

## Uruchomienie lokalne

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

kedro run

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
streamlit run frontend/app.py
```


## Uruchomienie przez Makefile

```bash
make install
make kedro-all
make run-api
make run-ui
```

`kedro run` oraz `make kedro-all` uruchamiaja pelny pipeline:

```text
eda -> preprocessing -> modeling -> evaluation
```

Pojedyncze etapy mozna uruchomic jawnie:

```bash
kedro run --pipeline=eda
kedro run --pipeline=preprocessing
kedro run --pipeline=modeling
kedro run --pipeline=evaluation
```

## Uruchomienie w kontenerach

```bash
docker compose up --build
```

Backend: `http://localhost:8000`

Frontend: `http://localhost:8501`

Kontener backendu kopiuje `data/reporting/` w trakcie buildu. Po ponownym
uruchomieniu `kedro run` warto przebudowac kontenery, aby API uzywalo swiezych
rekomendacji.

## Endpointy API

Pelny Swagger jest dostepny pod `http://localhost:8000/docs`.

| Metoda | Sciezka | Opis |
|---|---|---|
| `GET` | `/` | health check |
| `GET` | `/users?limit=N` | lista przykladowych `user_id` |
| `GET` | `/users/{user_id}/recommendations` | Top-K rekomendacji dla uzytkownika |

Przyklady:

```bash
curl http://localhost:8000/users?limit=5
curl http://localhost:8000/users/5250/recommendations
```

## Pipeline Kedro

| Pipeline | Co robi | Glowne artefakty |
|---|---|---|
| `eda` | filtruje interakcje `play`, liczy statystyki i wykresy | `data/intermediate/steam_play_interactions.csv`, `eda_*.csv` |
| `preprocessing` | usuwa duplikaty, wartosci niepoprawne i outliery, robi split 70/15/15 | `clean_data.csv`, `train.csv`, `val.csv`, `test.csv` |
| `modeling` | buduje item-based CF recommendations | `data/reporting/recommendations_top5.csv` |
| `evaluation` | liczy Precision@K, Recall@K i coverage | `data/reporting/recommender_metrics.json` |

## Jakosc kodu

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
ruff check .
pylint --rcfile=.pylintrc --fail-under=8.0 src/ai_project_s28551 app
```

## Struktura

```text
app/                       FastAPI
frontend/                  Streamlit UI
conf/                      konfiguracja Kedro
data/                      dane i artefakty pipeline'u
docs/                      wykresy EDA
src/ai_project_s28551/     kod pipeline'ow Kedro
src/tests/                 testy pytest
docker-compose.yml         backend + frontend
requirements.txt           zaleznosci runtime
requirements-dev.txt       testy i linting
```

## Autor

Jan Wojda, indeks s28551
Adam Harasimowicz, indeks s26302
