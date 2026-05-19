# 🍵 MatchaMind - Smart Lifestyle & Expense Companion

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red.svg)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Google-Gemini-blue.svg)](https://ai.google.dev/)

MatchaMind is an AI-powered expense tracking application that turns every receipt into actionable insights. It leverages the Google Gemini API to automatically parse transaction text and provides intelligent coaching to help you save money.

---

## ✨ Features

- **🤖 AI-Powered Parsing**: Just paste receipt text, AI extracts amount, merchant & category automatically
- **🎯 Smart Categorization**: Automatically categorizes transactions into customizable categories
- **📊 Beautiful Dashboard**: Visualize spending habits with interactive charts and graphs
- **💡 AI Coaching**: Detects spending patterns and gives personalized money-saving advice
- **📱 Mobile Friendly**: Responsive design works on desktop, tablet, and mobile
- **🔔 Smart Alerts**: Get notified when spending exceeds limits or unusual patterns detected

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone [https://github.com/yourusername/matchamind.git](https://github.com/yourusername/matchamind.git)
   cd matchamind

2. **Set up environment variables**
cp .env.example .env
# Edit .env and add your Gemini API key

3. **Run the application**
chmod +x start.sh
./start.sh

4. **Open your browser**
Frontend: http://localhost:8501
API Docs: http://localhost:8000/docs

**Docker Setup**
docker-compose up --build

## 📖 Usage

**Adding Expenses**

- ***AI Parse Mode**: Paste receipt text like "RM 45.90 - Tealive (Matcha Latte)"
- **Manual Mode**: Enter merchant, amount, and category manually

**Viewing Insights**

- Dashboard shows spending trends and category breakdowns
- Insights page provides AI-powered recommendations
- Alerts page shows coaching messages and warnings

**Sample Inputs to Test**

✅ RM 45.90 - Tealive (Matcha Latte with oat milk)
✅ KFC: RM 32.40 (2pc combo + fries)
✅ Nasi Kandar Pelita - RM 18.50 - Roti Canai + Teh Tarik
✅ Paid RM 129 for Matcha powder from Shopee

## 🏗️ Architecture

┌─────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)             │
│  Dashboard │ Add Expense │ Insights │ Alerts        │
└─────────────────────┬───────────────────────────────┘
                      │ 
                      │ HTTP/REST API
                      ▼
┌─────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                 │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Transaction  │  │   AI Parser  │                 │
│  │   Service    │◄─┤   (OpenAI)   │                 │
│  └──────────────┘  └──────────────┘                 │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │    Coach     │  │  Analytics   │                 │
│  │   Service    │  │   Service    │                 │
│  └──────────────┘  └──────────────┘                 │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              Database (Supabase/PostgreSQL)         │
│  Users │ Categories │ Transactions │ Alerts         │
└─────────────────────────────────────────────────────┘

## 🧪 Testing

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend --cov-report=html

# Run specific test
pytest tests/test_api.py -v

## 🚢 Deployment

**Deploy to Railway (Recommended)**
railway login
railway up

**Deploy to Render**
- Use the render.yaml configuration file.

**Deploy Frontend to Streamlit Cloud**

- Push code to GitHub
- Go to share.streamlit.io
- Connect your repository
- Add secrets: API_URL = your backend URL

## 📊 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/health` | Health check |
| **GET** | `/transactions/recent` | Get recent transactions |
| **POST** | `/transactions/parse-and-add` | Parse and add transaction |
| **GET** | `/analytics/summary` | Get spending summary |
| **GET** | `/alerts` | Get AI coaching alerts |
| **GET** | `/categories` | Get user categories |

## 🛠️ Tech Stack

- Backend: FastAPI, Python 3.11
- Frontend: Streamlit, Plotly
- AI: OpenAI GPT-3.5/4 API
- Database: PostgreSQL (Supabase)
- Deployment: Railway, Render, Streamlit Cloud
- Testing: Pytest, Pytest-cov

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- OpenAI for GPT API
- Streamlit for amazing UI framework
- FastAPI for high-performance backend

## 📧 Contact

- Muhammad Azhan Bin Muhammad Nazam - azhannazam@gmail.com
- Project Link: https://github.com/azhannazam/matchamind
