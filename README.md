# Gridlock (DRISHTI)

**Project Overview**

Gridlock (also known as DRISHTI) is an event‑driven traffic forecasting and resource deployment system for Bengaluru. It ingests traffic incident reports, classifies them using machine‑learning models, predicts resolution times, and surfaces historical precedents to help traffic police allocate resources efficiently.

**Key Features**
- Multilingual incident classification (Kannada, English, code‑mixed)
- Impact forecasting and resolution time prediction
- Historical precedent lookup with confidence scoring
- Optional temporal baseline and hotspot detection extensions

**Running the Backend**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server (development mode)
uvicorn app:app --reload
```
The API will be available at `http://127.0.0.1:8000` with Swagger UI at `/docs`.

**Running the Frontend**
```bash
# Install Node dependencies (from the `frontend` directory)
cd frontend
npm install

# Launch the Vite development server
npm run dev
```
The frontend will be served at `http://localhost:5173` and proxies API calls to the backend.

**Additional Setup**
- Ensure a PostgreSQL (or SQLite for local dev) database is configured via the `DATABASE_URL` environment variable.
- Seed initial historical data if running for the first time:
```bash
python memory/seed_historical.py
```
- (Optional) Train or update the ML models files if needed.

**Contributing**
Feel free to open issues or submit pull requests. Follow the existing code style and run the test suites before submitting changes.
