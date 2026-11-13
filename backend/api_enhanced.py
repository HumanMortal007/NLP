"""
Enhanced FastAPI Backend with Video ID Input Support
Combines all components: YouTube extraction, Gemini analysis, Sentiment scoring
"""

from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import os
import asyncio
from datetime import datetime
import pandas as pd
import time

# Import our components
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from youtube_improved import YouTubeCommentExtractor
from batch_processor import BatchProcessor
from sentiment_analyzer import SentimentAnalyzer
from data_utilities import (
    extract_channel_info,
    parse_batch_analysis,
    aggregate_analytics,
    generate_summary_report,
    generate_creator_json
)

# Configuration - API keys stored in backend
#my key:- AIzaSyBRtmiRIwGZwoi_lSCz9DDMdCejjb9tLRI
#v key:- AIzaSyBA3yNOiZhhjw1sBzzquECwZU9ppUedN2A
YOUTUBE_API_KEY = 'AIzaSyA-PBiOG1Xj3kn1ZnKQxyiLzcmmUnl2u-c'
GEMINI_API_KEY = 'AIzaSyBRtmiRIwGZwoi_lSCz9DDMdCejjb9tLRI'

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
BATCHES_DIR = DATA_DIR / "batches"
VIZ_DIR = DATA_DIR / "visualizations"

app = FastAPI(title="CreatorGPT YouTube Analyzer", version="2.0.0")

# Mount static files for visualizations
VIZ_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/visualizations", StaticFiles(directory=str(VIZ_DIR)), name="visualizations")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class AnalysisRequest(BaseModel):
    video_id: str
    max_comments: Optional[int] = 1000
    batch_size: Optional[int] = 50


class AnalysisStatus(BaseModel):
    status: str
    progress: float
    current_step: str
    message: str
    data: Optional[Dict] = None


# Global state
analysis_state = {
    'status': 'idle',
    'progress': 0,
    'current_step': '',
    'message': 'Ready to analyze',
    'results': None,
    'video_info': None
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# Helper function to update status
async def update_status(status: str, progress: float, step: str, message: str, data: Dict = None):
    """Update global status and broadcast to WebSocket clients."""
    global analysis_state
    
    analysis_state.update({
        'status': status,
        'progress': progress,
        'current_step': step,
        'message': message,
        'data': data
    })
    
    await manager.broadcast(analysis_state)


# Background analysis task
async def run_analysis_pipeline(video_id: str, max_comments: int, batch_size: int):
    """Execute complete analysis pipeline in background."""
    try:
        await update_status('running', 0, 'initialization', 'Starting analysis pipeline...')
        
        # Create output directories
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        BATCHES_DIR.mkdir(parents=True, exist_ok=True)
        VIZ_DIR.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Extract YouTube comments
        await update_status('running', 5, 'extraction', f'Connecting to YouTube API...')
        
        extractor = YouTubeCommentExtractor(
            YOUTUBE_API_KEY,
            output_dir=str(OUTPUTS_DIR)
        )
        
        await update_status('running', 10, 'extraction', f'Extracting comments from video {video_id}...')
        
        comments = extractor.collect_comments_until_5000(
            video_id,
            max_comments=max_comments
        )
        
        if not comments:
            await update_status('failed', 0, 'error', 'No comments found or video not accessible')
            return
        
        # Save outputs
        extractor.save_all_comments_csv()
        extractor.save_cleaned_comments_csv()
        channel_metadata_file = extractor.save_channel_metadata()
        
        video_info = {
            'video_id': video_id,
            'video_title': extractor.channel_info.get('video_title', 'N/A'),
            'channel_title': extractor.channel_info.get('channel_title', 'N/A'),
            'total_comments_available': extractor.channel_info.get('video_comments_count', 0),
            'comments_extracted': len(comments)
        }
        
        analysis_state['video_info'] = video_info
        
        await update_status('running', 30, 'extraction', 
                          f'✓ Extracted {len(comments)} comments from "{video_info["video_title"]}"')
        
        await asyncio.sleep(1)
        
        # Step 2: Create batches
        await update_status('running', 35, 'batching', 'Creating comment batches for LLM analysis...')
        
        batch_files = extractor.create_batches(
            batch_size=batch_size,
            output_dir=str(BATCHES_DIR)
        )
        
        await update_status('running', 40, 'batching', 
                          f'✓ Created {len(batch_files)} batches ({batch_size} comments each)')
        
        await asyncio.sleep(1)
        
        # Step 3: LLM batch processing with Gemini
        await update_status('running', 45, 'llm_analysis', 'Starting Gemini AI analysis...')
        
        processor = BatchProcessor(GEMINI_API_KEY, output_dir=str(OUTPUTS_DIR))
        
        # Process batches with progress updates
        for idx, batch_file in enumerate(batch_files, 1):
            progress = 45 + (idx / len(batch_files)) * 25
            await update_status('running', progress, 'llm_analysis',
                              f'Analyzing batch {idx}/{len(batch_files)} with Gemini AI...')
            
            processor.process_batch(batch_file, idx)
            await asyncio.sleep(0.5)
        
        # Consolidate analyses
        comprehensive_file = processor.consolidate_all_analyses()
        
        await update_status('running', 70, 'llm_analysis', 
                          f'✓ Gemini AI analysis complete - {len(batch_files)} batches processed')
        
        await asyncio.sleep(1)
        
        # Step 4: Sentiment analysis with transformers
        await update_status('running', 75, 'sentiment', 'Loading sentiment analysis model...')
        
        analyzer = SentimentAnalyzer(output_dir=str(OUTPUTS_DIR))
        
        await update_status('running', 80, 'sentiment', 'Analyzing sentiment with transformers...')
        
        df = analyzer.analyze_sentiment(str(OUTPUTS_DIR / 'cleaned_all_comments.csv'))
        
        await update_status('running', 90, 'sentiment', 
                          f'✓ Sentiment analysis complete - {len(df)} comments scored')
        
        # Save sentiment results
        analyzer.save_analyzed_comments()
        report_file = analyzer.generate_detailed_report()
        
        await asyncio.sleep(1)
        
        # Step 5: Generate visualizations
        await update_status('running', 93, 'visualization', 'Generating charts and visualizations...')
        
        viz_files = analyzer.generate_visualizations()
        
        await update_status('running', 96, 'visualization', 
                          f'✓ Generated {len(viz_files)} visualizations')
        
        await asyncio.sleep(1)
        
        # Step 6: Finalize results
        await update_status('running', 98, 'finalization', 'Compiling final results...')
        
        # Aggregate analytics
        analytics = aggregate_analytics(str(OUTPUTS_DIR))
        
        # Compile final results
        # Prepare detailed results for API consumers
        # Add top_keyword_terms (simple list) for easy consumption
        top_keywords_raw = analytics.get('top_keywords', [])
        top_keyword_terms = [k['keyword'] for k in top_keywords_raw] if isinstance(top_keywords_raw, list) else top_keywords_raw

        # Sentiment breakdown with per-label average confidence
        try:
            avg_pos_conf = float(df[df['sentiment_label'] == 'Positive']['confidence_score'].mean()) if 'sentiment_label' in df.columns else 0.0
            avg_neu_conf = float(df[df['sentiment_label'] == 'Neutral']['confidence_score'].mean()) if 'sentiment_label' in df.columns else 0.0
            avg_neg_conf = float(df[df['sentiment_label'] == 'Negative']['confidence_score'].mean()) if 'sentiment_label' in df.columns else 0.0
        except Exception:
            avg_pos_conf = avg_neu_conf = avg_neg_conf = 0.0

        sentiment_breakdown = {
            'positive': int(df[df['sentiment_label'] == 'Positive'].shape[0]) if 'sentiment_label' in df.columns else 0,
            'neutral': int(df[df['sentiment_label'] == 'Neutral'].shape[0]) if 'sentiment_label' in df.columns else 0,
            'negative': int(df[df['sentiment_label'] == 'Negative'].shape[0]) if 'sentiment_label' in df.columns else 0,
            'avg_confidence': float(df['confidence_score'].mean()) if 'confidence_score' in df.columns else 0.0,
            'avg_confidence_positive': avg_pos_conf,
            'avg_confidence_neutral': avg_neu_conf,
            'avg_confidence_negative': avg_neg_conf
        }

        results = {
            'video_info': video_info,
            'total_comments': len(comments),
            'batches_processed': len(batch_files),
            'sentiment_summary': sentiment_breakdown,
            'top_keywords': analytics.get('top_keywords', [])[:20],
            'top_keyword_terms': top_keyword_terms[:20],
            'files': {
                'comments_csv': str(OUTPUTS_DIR / 'all_comments.csv'),
                'analyzed_csv': str(OUTPUTS_DIR / 'sentiment_analyzed_comments.csv'),
                'detailed_report': report_file,
                'comprehensive_analysis': comprehensive_file,
                'visualizations': viz_files
            },
            'completed_at': datetime.now().isoformat()
        }
        # Generate a minimal creator-focused JSON summary for quick consumption
        try:
            creator_summary_file = generate_creator_json(analytics, df, output_file=str(OUTPUTS_DIR / 'creator_summary.json'))
            if creator_summary_file:
                results['files']['creator_summary'] = creator_summary_file
        except Exception as e:
            print(f"Warning: could not generate creator summary JSON: {e}")
        
        analysis_state['results'] = results
        analysis_state['completed'] = True
        
        await update_status('completed', 100, 'done', 
                          f'✓ Analysis complete! {video_info["video_title"]}', results)
        
    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}"
        print(traceback.format_exc())
        await update_status('failed', 0, 'error', error_msg)


# API Endpoints

@app.get("/")
async def root():
    """API health check."""
    return {
        "name": "CreatorGPT YouTube Analyzer",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "YouTube comment extraction",
            "Gemini AI analysis",
            "Transformer sentiment scoring",
            "Real-time progress updates",
            "Interactive visualizations"
        ]
    }


@app.post("/api/analyze")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start new YouTube comment analysis with user-provided video ID.
    """
    global analysis_state
    
    if analysis_state['status'] == 'running':
        raise HTTPException(status_code=409, detail="Analysis already in progress")
    
    # Validate video ID
    if not request.video_id or len(request.video_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid video ID")
    
    # Reset state
    analysis_state = {
        'status': 'queued',
        'progress': 0,
        'current_step': 'queued',
        'message': f'Analysis queued for video: {request.video_id}',
        'results': None,
        'video_info': None
    }
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis_pipeline,
        request.video_id,
        request.max_comments,
        request.batch_size
    )
    
    return {
        "message": "Analysis started",
        "video_id": request.video_id,
        "max_comments": request.max_comments,
        "status": "queued"
    }


@app.get("/api/status")
async def get_status():
    """Get current analysis status."""
    return AnalysisStatus(**analysis_state)


@app.get("/api/results")
async def get_results():
    """Get analysis results."""
    if not analysis_state.get('results'):
        raise HTTPException(status_code=404, detail="No analysis results available")
    
    return analysis_state['results']


@app.get("/api/dashboard-data")
async def get_dashboard_data():
    """Serve aggregated data for dashboard UI."""
    if not analysis_state.get('results'):
        raise HTTPException(status_code=404, detail="No analysis results available")
    
    results = analysis_state['results']
    
    try:
        df = pd.read_csv(OUTPUTS_DIR / 'sentiment_analyzed_comments.csv')
        
        # Temporal trends
        temporal_trends = []
        if 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'])
            df['date'] = df['published_at'].dt.date
            daily = df.groupby('date').agg({
                'confidence_score': 'mean',
                'sentiment_label': 'count'
            }).reset_index()
            
            temporal_trends = [
                {
                    'date': str(row['date']),
                    'avg_score': float(row['confidence_score']),
                    'count': int(row['sentiment_label'])
                }
                for _, row in daily.iterrows()
            ]
        
        # Check for visualization files
        visualizations = []
        if VIZ_DIR.exists():
            for viz_file in VIZ_DIR.glob('*.png'):
                visualizations.append({
                    'name': viz_file.stem,
                    'url': f'http://localhost:8001/visualizations/{viz_file.name}',
                    'filename': viz_file.name
                })
        
        # Load batch summaries
        batch_summaries = []
        batch_files = sorted([f for f in os.listdir(OUTPUTS_DIR) if f.startswith('batch_') and f.endswith('_analysis.json')])
        for batch_file in batch_files[:10]:  # Show first 10 batches
            try:
                with open(OUTPUTS_DIR / batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    batch_summaries.append({
                        'batch_number': len(batch_summaries) + 1,
                        'themes': batch_data.get('themes', [])[:5],
                        'suggestions': batch_data.get('suggestions', [])[:3],
                        'sentiment': batch_data.get('sentiment_distribution', ''),
                        'top_comments': batch_data.get('top_comments', [])[:2]
                    })
            except:
                continue
        
        dashboard_data = {
            'overview': {
                'video_id': results['video_info']['video_id'],
                'video_title': results['video_info']['video_title'],
                'channel_name': results['video_info']['channel_title'],
                'total_comments': results['total_comments'],
                'total_comments_available': results['video_info'].get('total_comments_available', 0),
                'video_views': results['video_info'].get('video_views', 0),
                'video_likes': results['video_info'].get('video_likes', 0),
                'avg_sentiment_score': results['sentiment_summary'].get('avg_confidence', results['sentiment_summary'].get('avg_score', 0)),
                'analysis_date': results['completed_at']
            },
            'sentiment_distribution': results['sentiment_summary'],
            'trending_keywords': results.get('top_keywords', []),
            'top_keyword_terms': results.get('top_keyword_terms', []),  # Add string list version
            'temporal_trends': temporal_trends,
            'engagement_metrics': {
                'comment_likes_total': int(df['likes'].sum()) if 'likes' in df.columns else 0,  # Renamed for clarity
                'comment_likes_avg': float(df['likes'].mean()) if 'likes' in df.columns else 0,
                'video_likes': results['video_info'].get('video_likes', 0),  # Add video likes from metadata
                'video_views': results['video_info'].get('video_views', 0)
            },
            'visualizations': visualizations,
            'batch_summaries': batch_summaries
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard data: {str(e)}")


class ChatRequest(BaseModel):
    """Request model for AI chat questions."""
    question: str


@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """
    AI-powered chat to answer questions about video comments analysis.
    Creators can ask questions and get insights from their comment data.
    """
    if not analysis_state.get('completed'):
        raise HTTPException(status_code=400, detail="Please complete an analysis first before asking questions")
    
    try:
        # Load comment data
        df = pd.read_csv(OUTPUTS_DIR / 'sentiment_analyzed_comments.csv')
        results = analysis_state.get('results', {})
        
        # Load batch analyses if available
        batch_insights = []
        batch_files = [f for f in os.listdir(OUTPUTS_DIR) if f.startswith('batch_') and f.endswith('_analysis.json')]
        for batch_file in batch_files[:5]:  # Use first 5 batches as context
            with open(OUTPUTS_DIR / batch_file, 'r', encoding='utf-8') as f:
                batch_insights.append(json.load(f))
        
        # Create context from analysis results (keep minimal and robust)
        top_kw_str = ', '.join(results.get('top_keyword_terms', [])[:15]) if results.get('top_keyword_terms') else ''
        total_comments = results.get('total_comments', 0)
        pos = results.get('sentiment_summary', {}).get('positive', 0)
        neu = results.get('sentiment_summary', {}).get('neutral', 0)
        neg = results.get('sentiment_summary', {}).get('negative', 0)
        avg_conf = results.get('sentiment_summary', {}).get('avg_confidence', 0)

        context = f"""
You are an AI assistant helping a YouTube content creator understand their video comments.

VIDEO INFORMATION:
- Title: {results.get('video_info', {}).get('video_title', 'N/A')}
- Channel: {results.get('video_info', {}).get('channel_title', 'N/A')}
- Total Comments Analyzed: {total_comments}

SENTIMENT SUMMARY:
- Positive Comments: {pos} ({(pos/max(total_comments,1))*100:.1f}%)
- Neutral Comments: {neu} ({(neu/max(total_comments,1))*100:.1f}%)
- Negative Comments: {neg} ({(neg/max(total_comments,1))*100:.1f}%)
- Average Confidence Score: {avg_conf:.1f}

TOP KEYWORDS/THEMES:
{top_kw_str}

KEY INSIGHTS FROM AI ANALYSIS:
{json.dumps(batch_insights[:2], indent=2) if batch_insights else 'No batch insights available'}

SAMPLE COMMENTS (Top 5 by engagement):
{df.nlargest(5, 'likes')[['text', 'sentiment_label', 'confidence_score', 'likes']].to_string() if 'likes' in df.columns else 'No engagement data'}

Based on this analysis, answer the creator's question clearly and actionably.
"""

        # Create prompt for Gemini
        prompt = f"""{context}

CREATOR'S QUESTION: {request.question}

Provide a clear, concise, and actionable answer that helps the creator understand their audience better. 
Use specific numbers and examples from the data above. Keep the response under 200 words.
"""

        # Call Gemini API with robust error handling and a dynamic fallback summary
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            answer_text = getattr(response, 'text', str(response))

        except Exception as e:
            # If LLM call fails (quota/network), generate a question-aware fallback
            print(f"Gemini call failed: {e}")
            
            question_lower = request.question.lower()
            fallback = []
            
            # Question-aware responses
            if any(word in question_lower for word in ['theme', 'topic', 'about', 'saying']):
                fallback.append(f"📌 **Main Topics**: {', '.join(top_kw_str.split(', ')[:10])}")
                if batch_insights and batch_insights[0].get('themes'):
                    fallback.append(f"💡 {', '.join(batch_insights[0]['themes'][:3])}")
            
            elif any(word in question_lower for word in ['sentiment', 'feel', 'opinion', 'mood']):
                fallback.append(f"😊 Sentiment: {pos} positive ({(pos/max(total_comments,1))*100:.1f}%)")
                fallback.append(f"😐 {neu} neutral, 😞 {neg} negative")
                fallback.append(f"📊 Avg confidence: {avg_conf:.1f}/100")
            
            elif any(word in question_lower for word in ['like', 'love', 'enjoy', 'positive']):
                fallback.append(f"✅ {pos} viewers expressed positive sentiment ({(pos/max(total_comments,1))*100:.1f}%)")
                if batch_insights and batch_insights[0].get('appreciation'):
                    fallback.append(f"💚 They appreciate: {', '.join(batch_insights[0]['appreciation'][:3])}")
            
            elif any(word in question_lower for word in ['suggest', 'improve', 'change', 'want']):
                if batch_insights and batch_insights[0].get('suggestions'):
                    fallback.append(f"💡 Viewer suggestions:")
                    for s in batch_insights[0]['suggestions'][:3]:
                        fallback.append(f"  • {s}")
                else:
                    fallback.append("No specific suggestions found in comments.")
            
            elif any(word in question_lower for word in ['negative', 'hate', 'dislike', 'concern', 'problem']):
                fallback.append(f"⚠️ {neg} comments were negative ({(neg/max(total_comments,1))*100:.1f}%)")
                if batch_insights and batch_insights[0].get('concerns'):
                    fallback.append(f"😟 Main concerns: {', '.join(batch_insights[0]['concerns'][:3])}")
            
            elif any(word in question_lower for word in ['next', 'future', 'upcoming']):
                if batch_insights and batch_insights[0].get('suggestions'):
                    fallback.append(f"🎥 Based on comments, consider:")
                    for s in batch_insights[0]['suggestions'][:2]:
                        fallback.append(f"  • {s}")
                fallback.append(f"🔑 Popular topics: {', '.join(top_kw_str.split(', ')[:5])}")
            
            else:
                # Generic fallback
                fallback.append(f"🔑 Top keywords: {top_kw_str}")
                sent_summary = results.get('sentiment_summary', {})
                fallback.append(f"😊 Sentiment: +{pos} ({(pos/max(total_comments,1))*100:.1f}%), -{neg} ({(neg/max(total_comments,1))*100:.1f}%)")
                if batch_insights and batch_insights[0].get('suggestions'):
                    fallback.append(f"💡 Top suggestion: {batch_insights[0]['suggestions'][0]}")
            
            # Add note about API limit
            fallback.append("\n⚠️ Note: AI quota exceeded. Showing structured data summary.")
            answer_text = '\n'.join(fallback)

        return {
            'question': request.question,
            'answer': answer_text,
            'context_used': {
                'total_comments': results.get('total_comments', 0),
                'sentiment_avg': results.get('sentiment_summary', {}).get('avg_confidence', 0),
                'video_title': results.get('video_info', {}).get('video_title', 'N/A')
            }
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Analysis data not found. Please run an analysis first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@app.websocket("/ws/analysis")
async def websocket_analysis(websocket: WebSocket):
    """WebSocket endpoint for real-time analysis updates."""
    await manager.connect(websocket)
    
    try:
        # Send current status immediately
        await websocket.send_json(analysis_state)
        
        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "status":
                    await websocket.send_json(analysis_state)
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("CreatorGPT YouTube Analyzer - Starting Server")
    print("="*60)
    print("\nAPI Keys Configured:")
    print(f"  YouTube API: {YOUTUBE_API_KEY[:20]}...")
    print(f"  Gemini API: {GEMINI_API_KEY[:20]}...")
    print("\nServer starting at: http://localhost:8001")
    print("API Documentation: http://localhost:8001/docs")
    print("\nReady to analyze YouTube videos!")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
