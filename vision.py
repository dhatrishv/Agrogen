
import os
import json
import asyncio
import requests
import traceback

HAS_VERTEX = True
try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel, Image
except Exception:
    HAS_VERTEX = False
    
    GenerativeModel = None
    Image = None


# =================================================================
# CONFIGURATION (EDIT THESE)
# =================================================================
# Configuration: prefer environment variables; fall back to file defaults.
PROJECT_ID = os.environ.get("PROJECT_ID", "alien-bruin-478312-q5")
LOCATION = os.environ.get("LOCATION", "us-central1")

# It's preferable to set `GOOGLE_APPLICATION_CREDENTIALS` outside this file (env)
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "key.json")

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "59c7e0a874493adca423dc207440fd2a")
DATA_GOV_API_KEY = os.environ.get("DATA_GOV_API_KEY", "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b")

IMAGE_PATH = os.environ.get("IMAGE_PATH", "test.jpeg")



# INITIALIZE VERTEX AI

def init_vertex():
    """Initialize Vertex AI if available. Safe to call multiple times."""
    if not HAS_VERTEX:
        return False
    try:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        return True
    except Exception:
        # don't crash import; let callers handle lack of init
        traceback.print_exc()
        return False


# =================================================================
# VISION AGENT (REAL GEMINI VISION)
# =================================================================
class VisionAgent:
    def __init__(self):
        # Lazy initialize Vertex model; allow running without Vertex packages.
        self.model = None
        if HAS_VERTEX:
            try:
                init_vertex()
                self.model = GenerativeModel("gemini-2.0-flash")
            except Exception:
                traceback.print_exc()
                self.model = None

        self.SYSTEM_PROMPT = """
        You are an agricultural plant disease detection expert.
        ALWAYS respond only in JSON with these keys:
        disease, confidence, severity, recommendation, explanation.
        No extra text.
        """

        self.USER_PROMPT = "Analyze this plant leaf image and return JSON only."

    def analyze_image(self, image_path):
        print(f"\n[VisionAgent] Loading: {image_path}")
        if not self.model or not HAS_VERTEX:
            # If Vertex is not available, return a deterministic stub
            return {
                "disease": "unknown",
                "confidence": 0.0,
                "severity": "unknown",
                "recommendation": "Vertex AI not configured. Provide credentials or run in stub mode.",
                "explanation": "Vertex/Generative model unavailable"
            }

        try:
            # load Image using the generative_models.Image helper
            img = Image.load_from_file(image_path)

            print("[VisionAgent] Sending to Gemini Vision...")

            response = self.model.generate_content([self.SYSTEM_PROMPT, self.USER_PROMPT, img])
            raw = response.text.strip()

            try:
                return json.loads(raw)
            except Exception:
                cleaned = raw[raw.find("{"): raw.rfind("}") + 1]
                return json.loads(cleaned)
        except Exception:
            traceback.print_exc()
            return {
                "disease": "error",
                "confidence": 0.0,
                "severity": "unknown",
                "recommendation": "Error calling vision model; check logs",
                "explanation": "See server logs for traceback"
            }


# =================================================================
# WEATHER AGENT (REAL OPENWEATHER API)
# =================================================================
class WeatherAgent:
    def __init__(self, api_key=OPENWEATHER_API_KEY):
        self.api_key = api_key
        # optional Vertex model to enrich or summarize weather data
        self.model = None
        if HAS_VERTEX:
            try:
                init_vertex()
                self.model = GenerativeModel("gemini-2.0-flash")
            except Exception:
                traceback.print_exc()

        self.SYSTEM_PROMPT_WEATHER = """
        You are a concise weather analyst for farmers. ALWAYS respond only in JSON with these keys:
        city, temperature, humidity, condition, wind_speed, precipitation, advisory.
        'advisory' should contain short, actionable advice for farmers (one or two sentences).
        Do not output any extra text.
        """

    def get_weather(self, city=None):
        """Fetch weather for the given city, optionally enrich/format via Vertex model.
        Returns a JSON-serializable dict with keys: city, temperature, humidity, condition,
        wind_speed, precipitation, and optionally advisory (from Vertex).
        """
        print("\n[WeatherAgent] Fetching weather...")
        if not city:
            print("[WeatherAgent] No city provided")
            return {
                "city": None,
                "temperature": None,
                "humidity": None,
                "condition": "missing_city",
                "wind_speed": None,
                "precipitation": None,
            }

        # Fetch from OpenWeather
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather?"
                f"q={city}&units=metric&appid={self.api_key}"
            )
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception:
            traceback.print_exc()
            return {
                "city": city,
                "temperature": None,
                "humidity": None,
                "condition": "unavailable",
                "wind_speed": None,
                "precipitation": None,
            }

        # Extract precipitation if present (OpenWeather uses 'rain' or 'snow') for current weather
        precip = None
        if isinstance(data.get("rain"), dict):
            precip = data.get("rain").get("1h") or data.get("rain").get("3h")
        elif isinstance(data.get("snow"), dict):
            precip = data.get("snow").get("1h") or data.get("snow").get("3h")

        summary = {
            "city": city,
            "temperature": data.get("main", {}).get("temp"),
            "humidity": data.get("main", {}).get("humidity"),
            "condition": (data.get("weather") and data.get("weather")[0].get("description")) or None,
            "wind_speed": data.get("wind", {}).get("speed"),
            "precipitation": precip,
        }

        # Determine future precipitation by calling the 5-day / 3-hour forecast and
        # scanning the next 24 hours for rain/snow or high precipitation probability.
        advisory = "Nice weather — conditions look good for field work."
        try:
            coord = data.get("coord", {})
            lat = coord.get("lat")
            lon = coord.get("lon")
            if lat is not None and lon is not None:
                f_url = (
                    f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={self.api_key}"
                )
                f_resp = requests.get(f_url, timeout=10)
                f_resp.raise_for_status()
                fdata = f_resp.json()

                rain_expected = False
                heavy_rain = False
                # forecast list contains 3-hour steps; check next 8 entries (~24h)
                for entry in (fdata.get("list") or [])[:8]:
                    # check explicit rain/snow volumes
                    if isinstance(entry.get("rain"), dict) and (entry.get("rain").get("3h") or entry.get("rain").get("1h")):
                        rain_expected = True
                        vol = entry.get("rain").get("3h") or entry.get("rain").get("1h")
                        if vol and vol >= 5:
                            heavy_rain = True
                            break
                    if isinstance(entry.get("snow"), dict) and (entry.get("snow").get("3h") or entry.get("snow").get("1h")):
                        rain_expected = True
                        break
                    # check probability of precipitation (pop) if available
                    pop = entry.get("pop")
                    if isinstance(pop, (int, float)) and pop >= 0.35:
                        rain_expected = True

                if heavy_rain:
                    advisory = "Heavy rain expected in the next 24 hours — secure produce, check drainage, and avoid field operations where waterlogging may occur."
                elif rain_expected:
                    advisory = "Rain expected in the next 24 hours — consider covering sensitive crops, postpone pesticide sprays, and prepare for wet conditions."

        except Exception:
            # If forecast call fails, preserve default advisory and continue
            traceback.print_exc()

        # attach advisory (derived from API forecast) to the summary
        summary["advisory"] = advisory

        # Return summary; do not rely on Vertex for advisory so suggestions come from API data
        return summary


# =================================================================
# MARKET AGENT (REAL INDIA MANDI PRICE API)
# =================================================================
class MarketAgent:
    def __init__(self):
        # Use Vertex AI generative model (Gemini) to produce daily vegetable prices as JSON
        # Make sure LOCATION supports the Gemini model you choose (e.g. "us-west1")
        self.model = None
        if HAS_VERTEX:
            try:
                init_vertex()
                self.model = GenerativeModel("gemini-2.0-flash")
            except Exception:
                traceback.print_exc()
                self.model = None

        self.SYSTEM_PROMPT = """
        You are a reliable agricultural market-price assistant.
        ALWAYS respond only in valid JSON with these keys:
        commodity, city, date, prices (array of {market, min_price, max_price, modal_price}), source.
        Do not output any extra text outside the JSON.
        """

    def get_all_unique_commodities(self):
        print("\n[MarketAgent] Asking Vertex AI for list of commodities...")
        user_prompt = "Provide a JSON array of unique commodity names available in today's mandi data."
        if not self.model:
            # fallback stub
            return ["Potato", "Tomato", "Onion", "Red Chillies"]
        response = self.model.generate_content([self.SYSTEM_PROMPT, user_prompt])
        raw = response.text.strip()
        try:
            return json.loads(raw)
        except Exception:
            cleaned = raw[raw.find("["): raw.rfind("]") + 1]
            return json.loads(cleaned)

    def get_prices(self, commodity=None, city=None):
        """Get mandi prices for the requested commodity and city. Both args are required."""
        print(f"\n[MarketAgent] Asking Vertex AI for prices for '{commodity}' in '{city}'...")
        if not commodity or not city:
            print("[MarketAgent] Missing commodity or city parameter")
            today = __import__('datetime').date.today().isoformat()
            return {
                "commodity": commodity or None,
                "city": city or None,
                "date": today,
                "prices": [],
                "source": "missing_parameters"
            }
        user_prompt = (
            f"Return today's mandi prices for commodity '{commodity}' in '{city}' "
            "as JSON matching the schema: {commodity, city, date, prices:[{market, min_price, max_price, modal_price}], source}."
        )
        if not self.model:
            # Provide a simple stubbed response when model isn't available
            today = __import__('datetime').date.today().isoformat()
            return {
                "commodity": commodity,
                "city": city,
                "date": today,
                "prices": [{"market": "Local Market", "min_price": 10, "max_price": 12, "modal_price": 11}],
                "source": "stub"
            }

        response = self.model.generate_content([self.SYSTEM_PROMPT, user_prompt])
        raw = response.text.strip()
        try:
            return json.loads(raw)
        except Exception:
            # attempt to extract JSON object from noisy output
            cleaned = raw[raw.find("{"): raw.rfind("}") + 1]
            return json.loads(cleaned)


# =================================================================
# KNOWLEDGE AGENT (GEMINI PRO TEXT AGENT)
# =================================================================
class KnowledgeAgent:
    def __init__(self):
        # initialize only if Vertex is available
        self.model = None
        if HAS_VERTEX:
            try:
                init_vertex()
                self.model = GenerativeModel("gemini-2.0-flash")
            except Exception:
                traceback.print_exc()
                self.model = None

    def answer(self, text):
        print("\n[KnowledgeAgent] Generating knowledge answer...")
        if not self.model:
            # fallback short deterministic answer
            return {"answer": "Please configure knowledge model (Vertex) to get full answers."}

        response = self.model.generate_content(f"You are an agriculture expert. Answer briefly: {text}")
        return {"answer": response.text}


# =================================================================
# SUPERVISOR AGENT (PARALLEL EXECUTION)
# =================================================================
class SupervisorAgent:
    def __init__(self):
        self.vision = VisionAgent()
        self.weather = WeatherAgent()
        # MarketAgent in this file expects no constructor args
        self.market = MarketAgent()
        self.knowledge = KnowledgeAgent()

    async def analyze_image_parallel(self, image_path, city, commodity):
        """Run vision, weather and market agents in parallel. `city` and `commodity` are required."""
        print("\n[SupervisorAgent] Running parallel agents...")

        vision_task = asyncio.to_thread(self.vision.analyze_image, image_path)
        weather_task = asyncio.to_thread(self.weather.get_weather, city)
        # pass commodity and city to market agent
        market_task = asyncio.to_thread(self.market.get_prices, commodity, city)

        vision_result, weather_data, mandi_prices = await asyncio.gather(
            vision_task, weather_task, market_task
        )

        return {
            "vision_result": vision_result,
            "weather": weather_data,
            "mandi_prices": mandi_prices
        }


# =================================================================
# =================================================================
if __name__ == "__main__":
    import sys

    print("\n========== SMART AGRO PARALLEL AGENT SYSTEM ==========")

    # allow passing city and commodity via CLI or environment variables
    city = os.environ.get("AGENT_CITY", "Bangalore")
    commodity = os.environ.get("AGENT_COMMODITY", "Potato")

    # CLI args: [script] [image_path] [city] [commodity]
    if len(sys.argv) >= 2:
        IMAGE_PATH = sys.argv[1]
    if len(sys.argv) >= 3:
        city = sys.argv[2]
    if len(sys.argv) >= 4:
        commodity = sys.argv[3]

    sup = SupervisorAgent()

    # RUN PARALLEL WORKFLOW with commodity forwarded
    output = asyncio.run(sup.analyze_image_parallel(IMAGE_PATH, city, commodity))

    print("\n=============== FINAL OUTPUT ===============")
    print(json.dumps(output, indent=4))
    print("===========================================\n")
