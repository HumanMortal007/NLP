# 🚀 Quick Start Guide - CreatorGPT

## Overview
This system allows you to input a YouTube video ID through a browser interface and get comprehensive sentiment analysis powered by AI.

## Prerequisites
✅ Python 3.8 or higher
✅ Node.js 16 or higher
✅ npm or yarn package manager

## Step-by-Step Setup

### 1️⃣ Backend Setup (Python)

**Navigate to project directory:**
```powershell
# Clone or navigate to the repository
git clone https://github.com/HumanMortal007/NLP.git
cd NLP
```

**Install Python dependencies (already done):**
```powershell
pip install google-api-python-client google-generativeai transformers torch pandas matplotlib seaborn fastapi uvicorn websockets python-multipart
```

**Start the backend server:**
```powershell
python backend/api_enhanced.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

✅ Backend is now running!

---

### 2️⃣ Frontend Setup (React)

**Open a NEW terminal and navigate to frontend folder:**
```powershell
cd frontend
```

**Install Node dependencies:**
```powershell
npm install
```

This will install:
- React 18
- Vite (build tool)
- Tailwind CSS (styling)
- Axios (API calls)
- Recharts (visualizations)

**Start the development server:**
```powershell
npm run dev
```

You should see:
```
  VITE v5.0.0  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

✅ Frontend is now running!

---

## 3️⃣ Using the Application

### Open in Browser
1. Open your browser and go to: **http://localhost:3000**

### Input YouTube Video
2. You'll see a form with three fields:
   - **YouTube Video ID or URL** (required)
   - **Maximum Comments to Analyze** (default: 1000)
   - **Batch Size** (default: 50)

### Enter Video ID
3. You can enter the video ID in multiple formats:
   ```
   ✅ Just the ID: dQw4w9WgXcQ
   ✅ Full URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ✅ Short URL: https://youtu.be/dQw4w9WgXcQ
   ```

### Start Analysis
4. Click **"🚀 Start Analysis"**

### Watch Real-Time Progress
5. You'll see live updates:
   - ⬇️ Extracting comments from YouTube
   - 🤖 Processing with Gemini AI
   - 😊 Analyzing sentiment with Transformers
   - 📊 Generating visualizations

### View Dashboard
6. After completion, you'll see:
   - **Sentiment Distribution** (pie chart)
   - **Batch Insights** (AI-generated summaries)
   - **Trending Themes** (word cloud)
   - **Temporal Analysis** (timeline)
   - **Top Comments** (highest engagement)

---

## 🎯 Example Videos to Try

### High Engagement Videos:
```
Video ID: dQw4w9WgXcQ
Description: Classic music video with massive comments
```

### Tutorial Videos:
```
Video ID: 9bZkp7q19f0
Description: Programming tutorial (diverse opinions)
```

### Product Reviews:
```
Video ID: (any tech review video)
Description: Mixed sentiment analysis
```

---

## 📊 What You'll Get

### 1. YouTube Extraction
- Video title, channel name, view count
- Up to 5000 comments with metadata
- Reply threads included

### 2. Gemini AI Analysis
- Key themes identified
- Constructive suggestions
- Sentiment overview
- Top representative comments

### 3. Transformer Sentiment Scoring
- 0-100 sentiment score per comment
- Positive/Negative/Neutral classification
- Confidence levels

### 4. Visualizations
- 📈 Sentiment distribution pie chart
- 📊 Score histogram
- 🔥 Temporal heatmap
- 📉 Trendline over time
- 🎯 Scatter plot analysis

---

## 🛑 Troubleshooting

### Backend won't start
**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```powershell
pip install fastapi uvicorn
```

### Frontend won't start
**Error:** `Cannot find module 'vite'`

**Solution:**
```powershell
cd frontend
npm install
```

### CORS errors in browser
**Error:** `Access to fetch at 'http://localhost:8000' has been blocked`

**Solution:** Make sure backend is running on port 8000

### No comments extracted
**Error:** `Quota exceeded`

**Solution:** Wait 24 hours or use a different YouTube API key

### WebSocket connection failed
**Error:** `WebSocket connection to 'ws://localhost:8000/ws' failed`

**Solution:** Restart the backend server

---

## 🔧 Configuration

### Change API Keys (Backend Only)
Edit `backend/api_enhanced.py`:
```python
YOUTUBE_API_KEY = 'your-youtube-api-key-here'
GEMINI_API_KEY = 'your-gemini-api-key-here'
```

### Change Ports
**Backend (api_enhanced.py):**
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Frontend (vite.config.js):**
```javascript
server: {
  port: 3000
}
```

---

## 📁 File Structure

```
nlp/
├── backend/
│   ├── api_enhanced.py          ← Start this first
│   ├── youtube_improved.py      ← Comment extraction
│   ├── batch_processor.py       ← Gemini AI analysis
│   ├── sentiment_analyzer.py    ← Transformer scoring
│   └── data_utilities.py        ← Helper functions
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              ← Main app logic
│   │   ├── components/
│   │   │   ├── AnalysisForm.jsx        ← Video ID input form
│   │   │   ├── RealTimeAnalysis.jsx    ← Progress tracker
│   │   │   └── FullScreenDashboard.jsx ← Results display
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
└── data/                        ← Output files (auto-created)
    ├── all_comments.csv
    ├── sentiment_analyzed_comments.csv
    └── visualizations/
```

---

## 🎬 Complete Workflow

```
1. User enters video ID in browser
   ↓
2. Frontend sends POST request to /api/analyze
   ↓
3. Backend extracts comments from YouTube
   ↓
4. Comments grouped into batches
   ↓
5. Gemini AI analyzes each batch
   ↓
6. Transformer model scores sentiment (0-100)
   ↓
7. Visualizations generated
   ↓
8. WebSocket sends real-time progress updates
   ↓
9. Dashboard displays complete analysis
```

---

## ✅ Success Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Browser opens to form interface
- [ ] Can enter YouTube video ID
- [ ] Analysis starts when clicking button
- [ ] Real-time progress updates appear
- [ ] Dashboard shows after completion
- [ ] Can start new analysis with "New Analysis" button

---

## 🎉 You're Ready!

Open **http://localhost:3000** in your browser and start analyzing YouTube comments with AI!

**Pro Tip:** Start with a small video (100-500 comments) to test the system quickly.
