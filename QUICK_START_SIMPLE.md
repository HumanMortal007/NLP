# Quick Start Guide - Simple YouTube Comment Analyzer

## ✅ What You Have Now

Your `nlpv_id.py` file is now a **complete, standalone analyzer** that does everything:
- ✅ Extracts YouTube comments
- ✅ Analyzes with Gemini AI (themes, feedback, insights)
- ✅ Scores sentiment with transformers (0-100 scale)
- ✅ Generates visualizations (pie charts, bar charts)
- ✅ Creates comprehensive reports

## 🚀 How to Use (3 Simple Steps)

### Step 1: Install Dependencies

```powershell
# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Install required packages
pip install google-api-python-client google-generativeai transformers torch pandas matplotlib seaborn
```

### Step 2: Configure Video ID (Optional)

Open `nlpv_id.py` and change the video ID at the bottom:

```python
if __name__ == "__main__":
    # Change this to your video ID
    video_id = 'YOUR_VIDEO_ID_HERE'
    
    # Adjust max comments (start with 500 for testing)
    main(video_id, max_comments=500)
```

### Step 3: Run Analysis

```powershell
# Run the analyzer
python nlpv_id.py
```

That's it! ✨

---

## 📊 What You'll Get

After running, you'll find:

### 📁 `nlp/analysis_results/`
- `comments.csv` - All extracted comments with metadata
- `sentiment_analyzed.csv` - Comments with sentiment scores
- `FINAL_REPORT.txt` - Complete analysis summary
- `gemini_full_analysis.txt` - AI insights from Gemini
- `batch_X_analysis.txt` - Individual batch analyses

### 📁 `nlp/visualizations/`
- `sentiment_pie_chart.png` - Sentiment distribution
- `score_distribution.png` - Confidence score histogram  
- `top_keywords.png` - Most mentioned words

---

## 🎯 Example Output

```
============================================================
YOUTUBE COMMENT SENTIMENT ANALYZER
============================================================

Video ID: mME51l0K9yA
Max Comments: 500

============================================================
Extracting comments from video: mME51l0K9yA
============================================================

Progress: 100/500 comments extracted...
Progress: 200/500 comments extracted...
...
✓ Extracted 500 comments

✓ Saved comments to nlp/analysis_results/comments.csv

============================================================
LLM Analysis with Gemini
============================================================

Analyzing batch 1 with Gemini AI...
✓ Batch 1 analyzed

...

============================================================
Sentiment Analysis with Transformers
============================================================

Loading sentiment model...
✓ Model loaded

Progress: 50/500 comments analyzed...
Progress: 100/500 comments analyzed...
...
✓ Sentiment analysis complete!

============================================================
Generating Visualizations
============================================================

✓ Saved: sentiment_pie_chart.png
✓ Saved: score_distribution.png
✓ Saved: top_keywords.png

============================================================
ANALYSIS COMPLETE!
============================================================

📊 Results:
   Total Comments: 500
   Positive: 320 (64.0%)
   Neutral: 120 (24.0%)
   Negative: 60 (12.0%)
   Average Score: 62.5/100

📁 Output Files:
   CSV: nlp/analysis_results/sentiment_analyzed.csv
   Report: nlp/analysis_results/FINAL_REPORT.txt
   Gemini Analysis: nlp/analysis_results/gemini_full_analysis.txt
   Visualizations: nlp/visualizations/
```

---

## 🔧 Customization

### Change Number of Comments

```python
main(video_id, max_comments=1000)  # Get 1000 comments
```

### Change Batch Size (for Gemini)

```python
gemini_analyses = create_batches_and_analyze(comments, batch_size=100)
```

### Analyze Different Video

Just change the `video_id`:

```python
video_id = 'dQw4w9WgXcQ'  # Any YouTube video ID
```

---

## 💡 Tips

1. **Start Small**: Test with 500 comments first
2. **API Limits**: YouTube API has daily quotas (10,000 units)
3. **Gemini Rate Limits**: Free tier = 60 requests/minute
4. **Processing Time**: 500 comments ≈ 5-10 minutes

---

## 🆘 Troubleshooting

### "Import errors"
```powershell
pip install --upgrade google-api-python-client google-generativeai transformers
```

### "API quota exceeded"
- Wait 24 hours or use different API key
- Reduce `max_comments` parameter

### "Gemini API error"
- Check your API key is correct
- Reduce batch size
- Add more delay: `time.sleep(5)` instead of `time.sleep(2)`

### "Model download slow"
First run will download the sentiment model (~250MB). This is normal and only happens once.

---

## 🎉 You're Ready!

Your analyzer is fully configured and ready to use. Just run:

```powershell
python nlpv_id.py
```

And watch the magic happen! ✨
