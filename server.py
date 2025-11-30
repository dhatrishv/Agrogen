from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import asyncio
from datetime import date

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)


def safe_analyze(image_path, city, crop):
    """Attempt to use SupervisorAgent from `vision.py`. On failure return a stubbed response."""
    try:
        # import here so app can run even if vision dependencies are not installed
        from vision import SupervisorAgent

        sup = SupervisorAgent()
        # SupervisorAgent.analyze_image_parallel is async and accepts commodity
        result = asyncio.run(sup.analyze_image_parallel(image_path, city, crop))
        return result
    except Exception as e:
        # Return a helpful stub when external APIs / credentials aren't available
        today = date.today().isoformat()
        return {
            "vision_result": {
                "disease": "Unable to analyze",
                "confidence": 0.0,
                "severity": "unknown",
                "recommendation": "Ensure Vertex AI credentials and APIs are configured. Returned stub response.",
                "explanation": str(e)
            },
            "weather": {
                "city": city,
                "temperature": 25.0,
                "humidity": 60,
                "condition": "clear sky",
                "wind_speed": 2.5
            },
            "mandi_prices": {
                "commodity": crop,
                "city": city,
                "date": today,
                "prices": [{"market": "Local Market", "min_price": 10, "max_price": 12, "modal_price": 11}],
                "source": "stub"
            }
        }


@app.route("/api/diagnose", methods=["POST"])
def diagnose():
    # Expecting multipart/form-data with fields: image (file), city (string), crop (string)
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files["image"]
    city = request.form.get("city", "").strip()
    crop = request.form.get("crop", "").strip()

    # Require both city and crop to be provided by the user
    if not city or not crop:
        return jsonify({"error": "Both 'city' and 'crop' fields are required."}), 400

    filename = image.filename or "upload.jpg"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(save_path)

    result = safe_analyze(save_path, city, crop)

    return jsonify(result)


@app.route("/", methods=["GET"])
def index():
    # Serve the static frontend
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)
