# ⚡ Quick Command Reference

## 🚀 Fastest Way to Start

### Option 1: Automated Startup (Recommended)
```powershell
cd NLP
.\start.ps1
```
This automatically:
- Starts backend on port 8000
- Starts frontend on port 3000
- Opens browser to http://localhost:3000

---

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```powershell
cd NLP
python backend/api_enhanced.py
```

**Terminal 2 - Frontend:**
```powershell
cd NLP/frontend
npm run dev
```

**Browser:**
```
Open: http://localhost:3000
```

---

## 📦 First Time Setup

### Install Frontend Dependencies (One-Time)
```powershell
cd NLP/frontend
npm install
```

This installs React, Vite, Tailwind CSS, Axios, Recharts, etc.

---

## 🛑 How to Stop Servers

### If using start.ps1:
Close the two PowerShell windows that opened

### If manual:
Press `Ctrl+C` in each terminal

---

## 🔍 Check Status

### Backend Status:
```powershell
# Should show server running
curl http://localhost:8000/health
```

### Frontend Status:
```
Open browser to: http://localhost:3000
```

---

## 📊 Example Usage

### 1. Start Servers
```powershell
.\start.ps1
```

### 2. In Browser (http://localhost:3000)
```
Video ID: dQw4w9WgXcQ
Max Comments: 1000
Batch Size: 50
Click: [🚀 Start Analysis]
```

### 3. Watch Progress
Real-time updates show:
- Comment extraction progress
- AI batch processing
- Sentiment scoring
- Visualization generation

### 4. View Results
Dashboard displays:
- Sentiment distribution charts
- AI-generated insights
- Top comments
- Trending themes

---

## 🐛 Quick Troubleshooting

### Backend won't start
```powershell
pip install fastapi uvicorn
```

### Frontend won't start
```powershell
cd frontend
npm install
```

### Port already in use
```powershell
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### CORS error
Make sure backend is running on port 8000

---

## 📂 Output Location

All results saved to:
```
backend/data/
```

Files created:
- `all_comments.csv` - Raw comments
- `sentiment_analyzed_comments.csv` - With sentiment scores
- `youtube_analytics.json` - Video metadata
- `visualizations/*.png` - Charts

---

## 🔑 API Keys Location

**IMPORTANT:** API keys are in `backend/api_enhanced.py`

Current values:
```python
YOUTUBE_API_KEY = 'AIzaSyA-PBiOG1Xj3kn1ZnKQxyiLzcmmUnl2u-c'
GEMINI_API_KEY = 'AIzaSyBA3yNOiZhhjw1sBzzquECwZU9ppUedN2A'
```

To change keys, edit this file only. Never put keys in frontend!

---

## 📚 More Help

- **Full Guide:** See `QUICK_START.md`
- **Documentation:** See `README_COMPLETE.md`
- **Implementation Details:** See `IMPLEMENTATION_SUMMARY.md`

---

## ✨ That's It!

**You're ready to analyze YouTube comments!** 🎉

Just run `.\start.ps1` and open http://localhost:3000 in your browser!
