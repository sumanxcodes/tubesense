# 🎥 TubeSense Analytics

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28-FF4B4B)

**TubeSense Analytics** is an advanced, AI-powered dashboard that transforms raw YouTube comments into actionable marketing intelligence. By leveraging state-of-the-art Natural Language Processing (NLP), TubeSense instantly extracts audience sentiment, categorizes latent topics, and identifies critical creator action items.

---

## ✨ Key Features

* **🧠 Advanced NLP Pipeline:** Utilizes `BERTopic` and `SentenceTransformers` (all-MiniLM-L6-v2) for robust topic modeling, and `twitter-roberta-base-sentiment` for highly accurate sentiment analysis.
* **📊 Aspect-Based Sentiment (ABSA):** Cross-references extracted topics with sentiment to tell you exactly *what* viewers loved and *what* they hated.
* **🎯 Intent & Entity Recognition:** Automatically routes comments into actionable queues (Questions, Feature Requests, Praise) and extracts mentions of specific competitor brands or products.
* **📈 Controversy & Velocity Tracking:** Plots comment velocity against likes and sentiment to identify highly polarizing or viral community engagements.
* **⚡ High-Performance Architecture:** An asynchronous **FastAPI** backend designed to handle hundreds of comments while preventing PyTorch thread collisions and memory leaks.
* **💅 Premium UI/UX:** A highly polished **Streamlit** frontend featuring custom Google Fonts, Material Icons, Lottie animations, and a glassmorphism aesthetic.

---

## 🏗️ Architecture

TubeSense is separated into two primary microservices that run concurrently:
1. **Backend (FastAPI):** Ingests YouTube URLs, orchestrates the NLP modeling, and serves a JSON REST API.
2. **Frontend (Streamlit):** Consumes the API and renders the interactive, cross-filterable data visualization dashboard.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
* Python 3.10+
* A valid **YouTube Data API v3** Key (from Google Cloud Console).

### 1. Clone & Configure
```bash
git clone https://github.com/sumanxcodes/tubesense.git
cd tubesense

# Copy the example env file and insert your API key
cp .env.example .env
```

### 2. Run the Application
TubeSense includes a unified startup script that automatically creates a virtual environment, installs dependencies, and boots both the API and the Dashboard concurrently.

```bash
chmod +x start.sh
./start.sh
```

Once running, navigate to:
* **Dashboard:** [http://localhost:8501](http://localhost:8501)
* **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🐳 Docker Deployment

TubeSense is fully containerized and production-ready.

```bash
# Build the image
docker build -t tubesense-app .

# Run the container (pass your YouTube API key)
docker run -p 8000:8000 -p 8501:8501 -e YOUTUBE_API_KEY="your_api_key_here" tubesense-app
```

---

## 🛠️ CI/CD & Testing

This repository includes full GitHub Actions workflows:
* **CI (`ci.yml`):** Runs `pytest`, `ruff` (linting), and `bandit` (security scanning) on every Pull Request.
* **CD (`cd.yml`):** Automatically builds the Docker container, scans for vulnerabilities using `Trivy`, and deploys to **Google Cloud Run** upon merge to `main`.

Run tests locally:
```bash
pytest tests/
```
