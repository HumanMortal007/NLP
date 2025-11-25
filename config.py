"""
Configuration file for CreatorGPT
Centralized settings for all components
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = DATA_DIR / 'outputs'
BATCH_DIR = DATA_DIR / 'batches'
VIZ_DIR = DATA_DIR / 'visualizations'

# API Keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Default Settings
DEFAULT_VIDEO_ID = os.getenv('DEFAULT_VIDEO_ID', 'mME51l0K9yA')
MAX_COMMENTS = int(os.getenv('MAX_COMMENTS', '5000'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))

# API Server Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))

# Sentiment Analysis Configuration
SENTIMENT_MODEL = os.getenv(
    'SENTIMENT_MODEL',
    'distilbert-base-uncased-finetuned-sst-2-english'
)

# Sentiment Thresholds (0-100 scale)
POSITIVE_THRESHOLD = int(os.getenv('POSITIVE_THRESHOLD', '60'))
NEGATIVE_THRESHOLD = int(os.getenv('NEGATIVE_THRESHOLD', '40'))

# Processing Configuration
ENABLE_PARALLEL_PROCESSING = os.getenv('ENABLE_PARALLEL_PROCESSING', 'False').lower() == 'true'
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))

# Rate Limiting
YOUTUBE_API_DELAY = float(os.getenv('YOUTUBE_API_DELAY', '0.1'))  # seconds
GEMINI_API_DELAY = float(os.getenv('GEMINI_API_DELAY', '2.0'))  # seconds

# Retry Configuration
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', '5.0'))  # seconds

# Visualization Configuration
VIZ_DPI = int(os.getenv('VIZ_DPI', '300'))
VIZ_FIGURE_SIZE = tuple(map(int, os.getenv('VIZ_FIGURE_SIZE', '12,8').split(',')))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Feature Flags
ENABLE_WEBSOCKET = os.getenv('ENABLE_WEBSOCKET', 'True').lower() == 'true'
ENABLE_VISUALIZATION = os.getenv('ENABLE_VISUALIZATION', 'True').lower() == 'true'
ENABLE_LLM_ANALYSIS = os.getenv('ENABLE_LLM_ANALYSIS', 'True').lower() == 'true'


def validate_config():
    """Validate configuration settings."""
    errors = []
    
    if not YOUTUBE_API_KEY:
        errors.append("YOUTUBE_API_KEY not set in environment")
    
    if not GEMINI_API_KEY and ENABLE_LLM_ANALYSIS:
        errors.append("GEMINI_API_KEY not set but LLM analysis is enabled")
    
    if MAX_COMMENTS < 1:
        errors.append("MAX_COMMENTS must be at least 1")
    
    if BATCH_SIZE < 1:
        errors.append("BATCH_SIZE must be at least 1")
    
    if POSITIVE_THRESHOLD <= NEGATIVE_THRESHOLD:
        errors.append("POSITIVE_THRESHOLD must be greater than NEGATIVE_THRESHOLD")
    
    return errors


def print_config():
    """Print current configuration."""
    print("=" * 60)
    print("CreatorGPT Configuration")
    print("=" * 60)
    print(f"YouTube API Key: {'✓ Set' if YOUTUBE_API_KEY else '✗ Not Set'}")
    print(f"Gemini API Key: {'✓ Set' if GEMINI_API_KEY else '✗ Not Set'}")
    print(f"Default Video ID: {DEFAULT_VIDEO_ID}")
    print(f"Max Comments: {MAX_COMMENTS:,}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Sentiment Model: {SENTIMENT_MODEL}")
    print(f"Positive Threshold: {POSITIVE_THRESHOLD}")
    print(f"Negative Threshold: {NEGATIVE_THRESHOLD}")
    print(f"API Server: {API_HOST}:{API_PORT}")
    print(f"WebSocket Enabled: {ENABLE_WEBSOCKET}")
    print(f"Visualization Enabled: {ENABLE_VISUALIZATION}")
    print(f"LLM Analysis Enabled: {ENABLE_LLM_ANALYSIS}")
    print("=" * 60)
    
    # Validate and show errors
    errors = validate_config()
    if errors:
        print("\n⚠ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        print()
    else:
        print("✓ Configuration is valid\n")


if __name__ == "__main__":
    print_config()
