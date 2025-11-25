# Troubleshooting Guide

## Common Issues and Solutions

### 1. Import Errors

**Problem:** `ModuleNotFoundError` or `ImportError`

**Solution:**
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# For specific packages:
pip install fastapi uvicorn transformers google-generativeai
```

---

### 2. API Key Issues

**Problem:** YouTube API returns 403 or "API key not valid"

**Solution:**
1. Check `.env` file has correct key
2. Verify API is enabled in Google Cloud Console:
   - Go to: https://console.cloud.google.com/apis/library
   - Search "YouTube Data API v3"
   - Click "Enable"
3. Check API key restrictions aren't blocking requests

**Problem:** Gemini API errors

**Solution:**
1. Get new key from: https://makersuite.google.com/app/apikey
2. Check rate limits (free tier: 60 requests/minute)
3. Increase `GEMINI_API_DELAY` in config.py

---

### 3. Quota Exceeded

**Problem:** "quotaExceeded" error from YouTube API

**Solution:**
1. YouTube API has 10,000 units/day default quota
2. Each comment fetch costs ~1 unit
3. Wait 24 hours or request quota increase
4. Temporarily reduce `max_comments` parameter:
   ```python
   extractor.collect_comments_until_5000(video_id, max_comments=500)
   ```

---

### 4. No Comments Found

**Problem:** 0 comments collected

**Solution:**
1. Check video ID is correct
2. Verify video has comments enabled
3. Check video is public (not private/unlisted)
4. Some videos disable comments - try different video ID

---

### 5. Sentiment Model Download Issues

**Problem:** Model download fails or is very slow

**Solution:**
```python
# Pre-download the model
from transformers import pipeline

# This will download and cache the model
pipeline("sentiment-analysis", 
         model="distilbert-base-uncased-finetuned-sst-2-english")
```

Or use offline mode:
```python
# Download model first, then use local path
analyzer = SentimentAnalyzer(
    model_name="path/to/local/model"
)
```

---

### 6. Visualization Not Generating

**Problem:** No PNG files in visualizations folder

**Solution:**
1. Check matplotlib backend:
   ```python
   import matplotlib
   matplotlib.use('Agg')  # Non-interactive backend
   ```

2. Install missing dependencies:
   ```powershell
   pip install matplotlib seaborn pillow
   ```

3. Verify output directory exists:
   ```python
   import os
   os.makedirs('data/visualizations', exist_ok=True)
   ```

---

### 7. Frontend Won't Start

**Problem:** `npm run dev` fails

**Solution:**
```powershell
# Delete node_modules and reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
npm install

# Clear npm cache if needed
npm cache clean --force
npm install
```

**Problem:** Cannot connect to API

**Solution:**
1. Verify backend is running: http://localhost:8000
2. Check CORS settings in `api.py`
3. Update frontend API URL in `.env`:
   ```
   VITE_API_URL=http://localhost:8000
   ```

---

### 8. WebSocket Connection Fails

**Problem:** Real-time updates not working

**Solution:**
1. Check backend WebSocket endpoint is running
2. Verify WebSocket URL in frontend:
   ```javascript
   const websocket = new WebSocket('ws://localhost:8000/ws/analysis');
   ```
3. Check browser console for connection errors
4. Some networks block WebSockets - try different network

---

### 9. Memory Issues

**Problem:** "MemoryError" or system slowdown

**Solution:**
1. Reduce batch size:
   ```python
   processor.process_all_batches(batch_size=50)  # Default: 100
   ```

2. Process in smaller chunks:
   ```python
   extractor.collect_comments_until_5000(video_id, max_comments=1000)
   ```

3. Close other applications
4. Increase system virtual memory

---

### 10. Slow Processing

**Problem:** Analysis takes too long

**Solution:**
1. **Reduce comment count:**
   ```python
   max_comments=500  # Instead of 5000
   ```

2. **Skip LLM analysis for testing:**
   ```python
   # Just run extraction and sentiment
   # Skip batch_processor step
   ```

3. **Increase API delays** (if hitting rate limits):
   ```python
   # In config.py
   GEMINI_API_DELAY = 5.0  # Increase from 2.0
   ```

4. **Use smaller batches:**
   ```python
   batch_size=50  # Instead of 100
   ```

---

### 11. File Not Found Errors

**Problem:** Cannot find CSV or output files

**Solution:**
1. Check working directory:
   ```python
   import os
   print(os.getcwd())
   ```

2. Use absolute paths:
   ```python
   from pathlib import Path
   output_dir = Path(__file__).parent / 'data' / 'outputs'
   ```

3. Verify files were created:
   ```python
   import os
   print(os.listdir('data/outputs'))
   ```

---

### 12. Encoding Errors

**Problem:** Unicode or encoding errors with comments

**Solution:**
1. Always use UTF-8:
   ```python
   with open(file, 'r', encoding='utf-8') as f:
       content = f.read()
   ```

2. Handle special characters in comments:
   ```python
   text = text.encode('utf-8', errors='ignore').decode('utf-8')
   ```

---

### 13. API Server Won't Start

**Problem:** `uvicorn` command not found

**Solution:**
```powershell
# Install uvicorn
pip install uvicorn[standard]

# Or run with python -m
python -m uvicorn api:app --reload
```

**Problem:** Port already in use

**Solution:**
```powershell
# Use different port
uvicorn api:app --reload --port 8001

# Or kill process on port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
```

---

### 14. Transformer Model Errors

**Problem:** "torch not found" or CUDA errors

**Solution:**
```powershell
# Install PyTorch (CPU version for simplicity)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Or use specific version
pip install torch==2.1.1
```

---

### 15. Data Not Appearing in Dashboard

**Problem:** Dashboard shows "No data available"

**Solution:**
1. Verify analysis completed successfully
2. Check API endpoint returns data:
   - Visit: http://localhost:8000/api/status
   - Visit: http://localhost:8000/api/dashboard-data
3. Check browser console for errors
4. Verify WebSocket connection established

---

## Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or in config.py:
```python
LOG_LEVEL = 'DEBUG'
```

---

## Getting Help

1. **Check logs** in console output
2. **Verify configuration** with:
   ```powershell
   python config.py
   ```
3. **Test individual components** with:
   ```powershell
   python examples.py
   ```
4. **Check API documentation**:
   - Visit: http://localhost:8000/docs

---

## Quick Test

Run this to verify everything works:

```python
# test_setup.py
def test_imports():
    try:
        import fastapi
        import transformers
        import google.generativeai
        from googleapiclient.discovery import build
        import pandas
        import matplotlib
        print("✓ All imports successful")
    except ImportError as e:
        print(f"✗ Import failed: {e}")

def test_directories():
    import os
    dirs = ['data/outputs', 'data/batches', 'data/visualizations']
    for d in dirs:
        if os.path.exists(d):
            print(f"✓ {d} exists")
        else:
            print(f"✗ {d} missing")
            os.makedirs(d, exist_ok=True)
            print(f"  Created {d}")

def test_config():
    from config import validate_config
    errors = validate_config()
    if errors:
        print("✗ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Configuration valid")

if __name__ == "__main__":
    test_imports()
    test_directories()
    test_config()
```

Run with: `python test_setup.py`

---

## Still Having Issues?

1. Delete virtual environment and recreate:
   ```powershell
   Remove-Item -Recurse -Force venv
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Try minimal example first (examples.py)
3. Check system requirements:
   - Python 3.8+
   - 4GB+ RAM
   - 2GB+ free disk space
   - Stable internet connection
