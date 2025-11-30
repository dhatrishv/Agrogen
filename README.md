# Smart Agro Advisor — Local Demo

This repository includes a minimal Flask backend and a clean static frontend you can run locally. The UI lets a farmer upload a leaf photo, enter a city (for weather) and crop name (for market/mandi prices). The backend will attempt to call the included `vision.py` agents (Vertex AI + OpenWeather + market agent). If those services or credentials are not configured it returns a helpful stubbed response.

Quick start (Windows PowerShell):

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. (Optional) Configure credentials

- If you want the real `vision.py` agents to work, set `GOOGLE_APPLICATION_CREDENTIALS` and edit `vision.py` configuration (project, location, keys). `key.json` should be present and valid.
- Ensure `vision.py`'s `OPENWEATHER_API_KEY` is valid for weather lookups.

4. Run the server

```powershell
python server.py
```

5. Open your browser to `http://localhost:7860` and test the UI.

Notes
- The backend will import and use `vision.py` if available and configured. If external services are not reachable the server responds with a stubbed (example) diagnosis + weather + market data.
- To integrate fully, ensure `key.json` and API keys are properly set in `vision.py`.

Want React instead?
- I built a static HTML+JS UI to avoid Node tooling. If you prefer a React/Vite app I can scaffold that next.
