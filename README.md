# CreatorGPT: YouTube Comment Sentiment Intelligence

**Automate collection, batching, and sentiment tagging of YouTube comments for content creators**

A comprehensive Natural Language Processing system that provides rapid insights into YouTube comment streams using AI-powered analysis.

---

## 🎯 Project Overview

CreatorGPT is an end-to-end NLP pipeline that:
- Fetches comments from YouTube videos via API
- Processes them in batches for LLM analysis
- Applies transformer-based sentiment scoring
- Generates actionable insights and visualizations
- Provides real-time dashboards for content creators

---

## ✨ Features

### Data Extraction Pipeline (`youtube_improved.py`)
- ✅ Validates environment and channel metadata
- ✅ Downloads up to 5000 comments with quota management
- ✅ Cleans text and saves to `all_comments.csv` and `cleaned_all_comments.csv`
- ✅ Segments batches (`comments_batch_N.txt`) for LLM processing
- ✅ Real-time progress tracking with `log_progress()`
- ✅ Handles resumable runs and safe appends
- ✅ Produces channel metadata snapshot (`youtube_analytics.json`)

### LLM Batch Summarization (`batch_processor.py`)
- ✅ Structured prompts via `enhanced_prompt()` for comprehensive analysis
- ✅ Gemini API integration with failure recovery
- ✅ Extracts themes, suggestions, appreciation, top comments
- ✅ Status tracking through `get_batch_status()`
- ✅ Outputs: `analyzed_comments_batch_N.txt` and consolidated reports

### Sentiment Analysis Engine (`sentiment_analyzer.py`)
- ✅ Transformer pipeline using DistilBERT
- ✅ Confidence-weighted 0-100 scoring via `_convert_to_score()`
- ✅ Generates rich charts and text reports
- ✅ Outputs:
  - `sentiment_analyzed_comments.csv`
  - `detailed_sentiment_results.txt`
- ✅ `generate_visualizations()` → Pie charts, trendlines, heatmaps

### Backend Services (`api.py`)
- ✅ FastAPI endpoints:
  - `/api/analyze` – Run new analysis
  - `/api/status` – Batch progress monitoring
  - `/api/dashboard-data` – Serve JSON for UI
  - `/api/comprehensive-analysis` – Aggregated report
- ✅ WebSocket streaming for real-time UI updates (`/ws/analysis`)
- ✅ Data utilities: `extract_channel_info()`, `parse_batch_analysis()`, etc.

### Frontend Dashboard (React + Tailwind CSS)
- ✅ **RealTimeAnalysis** → Live progress pane with WebSocket updates
- ✅ **FullScreenDashboard** → Comprehensive insights view
- ✅ Shows:
  - Sentiment distribution pie charts
  - Trending keywords bar charts
  - Temporal sentiment trends
  - Batch-wise summaries
  - Engagement metrics

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend)
- YouTube Data API key
- Google Gemini API key

### Backend Setup

```powershell
# Clone repository
git clone https://github.com/HumanMortal007/NLP.git
cd NLP

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Return to root
cd ..
```

---

## 🚀 Quick Start

### Option 1: Run Complete Pipeline (CLI)

```powershell
# Edit main_pipeline.py to add your API keys
# YOUTUBE_API_KEY = 'your_youtube_api_key'
# GEMINI_API_KEY = 'your_gemini_api_key'
# VIDEO_ID = 'your_video_id'

# Run the pipeline
python main_pipeline.py
```

### Option 2: Use Individual Modules

```python
from backend.youtube_improved import YouTubeCommentExtractor
from backend.batch_processor import BatchProcessor
from backend.sentiment_analyzer import SentimentAnalyzer

# 1. Extract comments
extractor = YouTubeCommentExtractor('YOUR_API_KEY', output_dir='data/outputs')
comments = extractor.collect_comments_until_5000('VIDEO_ID', max_comments=5000)
extractor.save_all_comments_csv()
extractor.save_cleaned_comments_csv()
batch_files = extractor.create_batches(batch_size=100)

# 2. Process batches with LLM
processor = BatchProcessor('YOUR_GEMINI_KEY', output_dir='data/outputs')
results = processor.process_all_batches('data/batches')

# 3. Analyze sentiment
analyzer = SentimentAnalyzer(output_dir='data/outputs')
df = analyzer.analyze_sentiment('data/outputs/cleaned_all_comments.csv')
analyzer.save_analyzed_comments()
analyzer.generate_detailed_report()
viz_files = analyzer.generate_visualizations()
```

### Option 3: Run API Server + Frontend

```powershell
# Terminal 1: Start FastAPI backend
cd backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start React frontend
cd frontend
npm run dev
```

Then:
1. Open browser to `http://localhost:5173` (or frontend URL)
2. Use the UI to submit analysis requests
3. Monitor real-time progress via WebSocket

---

## 📊 Output Files

### CSV Files
- `data/outputs/all_comments.csv` - Raw extracted comments
- `data/outputs/cleaned_all_comments.csv` - Preprocessed comments
- `data/outputs/sentiment_analyzed_comments.csv` - Comments with sentiment scores

### Text Reports
- `data/outputs/detailed_sentiment_results.txt` - Comprehensive sentiment report
- `data/outputs/comprehensive_analysis.txt` - Consolidated LLM batch analyses
- `data/outputs/summary_report.txt` - Executive summary

### JSON Files
- `data/outputs/youtube_analytics.json` - Channel and video metadata
- `data/outputs/batch_processing_summary.json` - Batch processing status
- `data/outputs/complete_analytics.json` - Aggregated analytics

### Visualizations
- `data/visualizations/sentiment_pie_chart.png`
- `data/visualizations/score_distribution.png`
- `data/visualizations/sentiment_trendline.png`
- `data/visualizations/sentiment_heatmap.png`
- `data/visualizations/sentiment_vs_engagement.png`

---

## 🏗️ Project Structure

```
nlp/
├── backend/
│   ├── youtube_improved.py         # YouTube extraction pipeline
│   ├── batch_processor.py          # LLM batch processing
│   ├── sentiment_analyzer.py       # Sentiment analysis engine
│   ├── data_utilities.py           # Helper functions
│   └── api.py                      # FastAPI server
├── frontend/
│   ├── src/
│   │   └── components/
│   │       ├── RealTimeAnalysis.jsx
│   │       └── FullScreenDashboard.jsx
│   └── package.json
├── data/
│   ├── batches/                    # Comment batches for LLM
│   ├── outputs/                    # Analysis results
│   └── visualizations/             # Generated charts
├── main_pipeline.py                # Main orchestrator
├── requirements.txt
└── README.md
```

---

## 🔑 API Endpoints

### POST `/api/analyze`
Start new analysis
```json
{
  "video_id": "VIDEO_ID",
  "youtube_api_key": "YOUR_KEY",
  "gemini_api_key": "YOUR_KEY",
  "max_comments": 5000,
  "batch_size": 100
}
```

### GET `/api/status`
Get current analysis status

### GET `/api/dashboard-data`
Get dashboard data (sentiment distribution, trends, keywords)

### GET `/api/comprehensive-analysis`
Get complete analysis report with all insights

### WebSocket `/ws/analysis`
Real-time progress updates

---

## 📈 Results & Insights

### Sentiment Analysis
- **0-100 confidence scores** for each comment
- **Categorization**: Positive (60-100), Neutral (40-60), Negative (0-40)
- **Distribution charts**: Pie charts showing sentiment breakdown
- **Temporal trends**: Sentiment changes over time

### LLM-Extracted Insights
- **Key Themes**: Top 5 topics discussed
- **Viewer Suggestions**: Actionable feedback from audience
- **Appreciation**: What viewers praised
- **Concerns**: Main criticisms
- **Top Comments**: Most impactful/representative comments
- **Engagement Patterns**: Questions, CTAs, community interactions
- **Content Recommendations**: Data-driven action items

### Engagement Metrics
- Total likes and average per comment
- High-engagement sentiment correlation
- Reply rates and conversation threads
- Top-liked comment sentiment analysis

---

## 🎨 Visualizations

1. **Pie Chart** - Sentiment distribution (Positive/Neutral/Negative)
2. **Histogram** - Confidence score distribution
3. **Line Chart** - Sentiment trend over time with comment volume
4. **Heatmap** - Sentiment by day of week and hour
5. **Scatter Plot** - Sentiment vs engagement (likes)

---

## 🧩 Key Technologies

- **Python 3.8+**: Core language
- **FastAPI**: Backend API framework
- **Transformers (HuggingFace)**: Sentiment analysis (DistilBERT)
- **Google Gemini API**: LLM batch processing
- **YouTube Data API v3**: Comment extraction
- **React 18**: Frontend framework
- **Tailwind CSS**: UI styling
- **Recharts**: Data visualization
- **WebSockets**: Real-time updates
- **Pandas, NumPy**: Data processing
- **Matplotlib, Seaborn**: Chart generation

---

## 🛠️ Configuration

### Environment Variables (Optional)
Create a `.env` file:

```env
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
DEFAULT_VIDEO_ID=mME51l0K9yA
MAX_COMMENTS=5000
BATCH_SIZE=100
```

### Customization

**Adjust sentiment thresholds**:
```python
# In sentiment_analyzer.py
def _categorize_sentiment(self, score: int) -> str:
    if score >= 65:  # Change from 60
        return "Positive"
    elif score >= 35:  # Change from 40
        return "Neutral"
    else:
        return "Negative"
```

**Change batch size**:
```python
extractor.create_batches(batch_size=150)  # Default: 100
```

**Use different sentiment model**:
```python
analyzer = SentimentAnalyzer(
    model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"
)
```

---

## 🚧 Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| API quota management | Rate limiting, pagination, quota tracking |
| Batch size vs LLM cost | Configurable batch sizes, retry logic |
| Consistent sentiment thresholds | Confidence-weighted 0-100 scoring |
| Missing/malformed batch files | Error handling, batch status tracking |

---

## 🔮 Future Enhancements

- [ ] Multilingual sentiment support
- [ ] Topic modeling with LDA/BERTopic
- [ ] Fine-tuned domain-specific sentiment classifiers
- [ ] Automated alerting for sentiment shifts
- [ ] Integration with creator scheduling tools
- [ ] Historical trend comparison
- [ ] Competitor video analysis
- [ ] Email report generation
- [ ] Export to PDF/PowerPoint

---

## 📝 Usage Example

```python
from main_pipeline import CreatorGPT

# Initialize
creator_gpt = CreatorGPT(
    youtube_api_key='YOUR_KEY',
    gemini_api_key='YOUR_KEY'
)

# Run analysis
results = creator_gpt.run_complete_analysis(
    video_id='mME51l0K9yA',
    max_comments=5000,
    batch_size=100
)

# Access results
print(f"Total comments: {results['total_comments']}")
print(f"Average sentiment: {results['sentiment_summary']['avg_score']}")
```

---

## 🤝 Contributing

This is a capstone project for an NLP course. Contributions, issues, and feature requests are welcome!

---

## 📄 License

This project is created for educational purposes.

---

## 👤 Author

**Thoshan**
- Natural Language Processing Course Capstone Project
- Year: 2025

---

## 🙏 Acknowledgments

- YouTube Data API v3
- Google Gemini API
- HuggingFace Transformers
- FastAPI Team
- React & Tailwind CSS Communities

---

## 📞 Support

For issues or questions:
1. Check the logs in `data/outputs/`
2. Verify API keys are correct
3. Ensure all dependencies are installed
4. Check API quotas (YouTube & Gemini)

---

**Happy Analyzing! 🎉📊😊**
