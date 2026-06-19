# SENTRY (Gridlock)

SENTRY is an event-driven traffic forecasting and resource deployment system designed for Bengaluru. It leverages multiple machine learning models and a historical memory store to classify incoming traffic incidents (in Kannada, English, or code-mixed text), forecast their impact and resolution times, and provide precedent data to help deploy resources efficiently.

---

## Project Structure & Components

The application is modularized into the following core components:

### 1. `memory/` (The Database & Memory Store)
Stores live and historical events, providing precedent search capabilities.
- **`db.py` / `models.py` / `schema.sql`**: SQLAlchemy setup and database schema. Works on SQLite for local development and Postgres for production.
- **`memory_store.py`**: Handles writing new live events and retrieving similar historical events based on `police_station`, `event_cause`, and `corridor`.
- **`confidence.py`**: Calculates a confidence tier ("no_precedent", "thin", "moderate", "strong") based on the frequency of similar past events.

### 2. `ml_models/` (Machine Learning Models)
Contains three separate ML pipelines that can be independently trained and tested.
- **`bilingual_event_classifier/`**: 
  - *Goal*: Classifies raw event text (Kannada/English) into an `event_cause` and a `severity` priority.
  - *Under the hood*: Uses `sentence-transformers` to generate embeddings and Logistic Regression for the final classification.
- **`resolution_predictor/`**:
  - *Goal*: Predicts the number of minutes required to clear an incident based on structured features (cause, corridor, time of day, closure required, etc).
  - *Under the hood*: Employs an XGBoost regressor, trained on historical closure times.
- **`impact_forecaster/`**:
  - *Goal*: Retrieves similar historical events purely based on the text description to provide qualitative precedent.
  - *Under the hood*: Utilizes a Nearest Neighbors index over text embeddings.

### 3. Root Level Files
- **`app.py`**: The main FastAPI application. It orchestrates the memory store and the three ML models to provide endpoints for event reporting, classification, resolution tracking, and hotspot generation.
- **`pipeline.py`**: A standalone script that runs the full inference and data-logging pipeline.
- **`test_each_model.py` / `test_integration.py`**: Scripts to independently verify each ML model and test the end-to-end integration.

---

## How to Run the Application

### 1. Environment Setup

Ensure you have Python 3 installed. Install the dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Prepare the Database and Models

If this is your first time running the application, you need to set up the database and train/evaluate the models.

*Initialize the database and seed historical data (if applicable):*
```bash
python memory/seed_historical.py
```

*Train the ML Models (if they aren't pre-trained):*
Navigate to each model folder and run the respective scripts. For example, for the classifier:
```bash
python ml_models/bilingual_event_classifier/run_pipeline.py
```
*(Check the `src/` folders within each `ml_models` sub-directory for individual `clean_data.py`, `train_model.py`, etc., if you wish to run them separately.)*

### 3. Start the FastAPI Server

Run the backend server using `uvicorn`:

```bash
uvicorn app:app --reload
```

The server will start on `http://127.0.0.1:8000`.

### 4. Exploring the Endpoints

Once the server is running, you can access the interactive API documentation (Swagger UI) at:
**[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

Key Endpoints:
- `POST /classify`: Classify a raw text string into a cause and severity.
- `POST /events/report`: Log a new traffic event. This will automatically classify it, retrieve similar precedents, estimate resolution time, and store it.
- `PATCH /events/{event_id}/resolve`: Mark an event as resolved, which updates its duration and improves future predictions.
- `GET /events/hotspot`: Retrieve current traffic hotspot data.

---

## Testing

To verify that all machine learning models are functioning correctly:
```bash
python test_each_model.py
```

To run full integration tests:
```bash
python test_integration.py
```
# SENTRY - Resolution Intelligence Dashboard

This is the SENTRY Resolution Intelligence frontend application — an internal operational dashboard for Bengaluru traffic police, intended to interact with three ML models:
- Bilingual Event Classifier
- Impact Forecaster
- Resolution Predictor

Currently, this frontend is intentionally backend-independent until teammates' APIs are ready. It simulates backend calls utilizing predefined mock data to showcase and test UI functionality.

## How to Run

To run the application locally, install the dependencies and start the Vite development server:

```bash
npm install
npm run dev
```

The application will typically start at `http://localhost:5173`.

## Moving to Real API Data

Currently, all mock data and simulated endpoints are localized inside `src/mockData.js`. 

To transition from the UI mock state to the production application, edit **`src/mockData.js`** to swap out the mock functions for real `fetch()` calls once the teammate APIs are complete:

- Update `mockPredictEvent` to send `POST` requests with `formData` to the Impact Forecaster/Resolution Predictor endpoints.
- Update `mockClassify` to send the `text` string to the Bilingual Event Classifier API endpoint.
- Swap out `HOTSPOT_JUNCTIONS` and `CAUSE_TOTALS` to fetch live historical data instead of static arrays.

*Note: This architecture intentionally decouples the UI layout logic from data retrieval to maintain parallel development streams.*
