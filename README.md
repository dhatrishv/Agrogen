# 🌱 AgroGen — AI-Powered Multi-Agent Agriculture Assistant

AgroGen is an AI-powered multi-agent system designed to empower farmers with insights on crop health, weather conditions, market prices, and actionable recommendations. It uses state-of-the-art AI models and government data sources to provide reliable, real-time agricultural intelligence.

---

# 📘 1. Introduction

**AgroGen** combines AI vision, weather intelligence, market analytics, and knowledge reasoning into a unified system to help farmers make informed decisions.

### **Inputs**
- 📸 Crop image  
- 📍 Farmer’s location  
- 🌿 Crop name  

### **Outputs**
- 🦠 Disease detection  
- ☁️ Weather insights  
- 💹 Live mandi (market) prices  
- 🧠 Farmer-friendly recommendations  

### **Multi-Agent Architecture**
- **Vision Agent** → Uses *Gemini Vision* for crop disease identification  
- **Weather Agent** → Fetches weather data via *OpenWeatherMap*  
- **Market Agent** → Retrieves mandi prices from *data.gov.in*  
- **Knowledge Agent** → Generates final recommendations using *Gemini Pro*  
- **Supervisor Agent** → Coordinates all agents in parallel and merges results  

---

# ⭐ 2. Features

- 🤖 Gemini Vision crop disease detection  
- ☁️ Real-time weather data  
- 💹 Live government mandi prices (data.gov.in)  
- ⚡ Parallel multi-agent execution  
- 📦 JSON-structured unified response  
- 🧱 Modular, scalable architecture  
- 📜 Optional memory & logging extensions  
- 🔌 Easy API integration  

---

# 🏗 3. System Architecture

AgroGen uses a **parallel, multi-agent architecture** orchestrated by a Supervisor Agent:

### 🧩 **Supervisor Agent**
- Executes all agents concurrently  
- Merges outputs into a final structured response  

### 👁️ **Vision Agent (Gemini 2.0 Flash)**
- Analyzes crop images  
- Detects diseases, pests, or nutritional issues  

### ☁️ **Weather Agent (OpenWeatherMap)**
- Retrieves weather forecasts  
- Temperature, humidity, rainfall, wind  

### 💹 **Market Agent (data.gov.in)**
- Retrieves mandi prices for crops  
- Uses public government datasets  

### 📘 **Knowledge Agent (Gemini 2.0 flash)**
- Synthesizes insights  
- Generates actionable farming recommendations  

---

# 🔧 4. Prerequisites

Ensure the following tools and accounts are ready:

| Dependency | Purpose |
|-----------|---------|
| **Python 3.13** | Project runtime |
| **Google Cloud Account** | Required for Gemini API |
| **Vertex AI API Enabled** | Needed for model access |
| **OpenWeatherMap API Key** | Weather data |
| **Data.gov.in API Key** | Mandi price data |

---

# 🔑 5. How to Get Your Google Cloud `key.json`

Follow this step-by-step guide:

1. Open **Google Cloud Console**  
2. Go to **IAM & Admin → Service Accounts**  
3. Click **Create Service Account**  
4. Enter a name → Click **Create**  
5. Assign role: **Vertex AI User**  
6. Click **Continue → Done**  
7. Select the service account  
8. Go to **Keys** tab → **Add Key → Create New Key**  
9. Choose **JSON** → Download it  
10. Rename file to **`key.json`**  
11. Move it to your project root folder  
12. Set environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="key.json"
