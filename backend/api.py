from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import os
import asyncio
from datetime import datetime
import pandas as pd

from youtube_improved import YouTubeCommentExtractor
from batch_processor import BatchProcessor
from sentiment_analyzer import SentimentAnalyzer
from data_utilities import (
    extract_channel_info,
    parse_batch_analysis,
    extract_comments_from_detailed_results,
    aggregate_analytics
)


app = FastAPI(title="CreatorGPT API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class AnalysisRequest(BaseModel):
    video_id: str
    youtube_api_key: str
    gemini_api_key: str
    max_comments: Optional[int] = 5000
    batch_size: Optional[int] = 100


class AnalysisStatus(BaseModel):
    status: str
    progress: float
    current_step: str
    message: str
    data: Optional[Dict] = None


# Global state management
analysis_state = {
    'status': 'idle',
    'progress': 0,
    'current_step': '',
    'message': '',
    'results': None
}

active_websockets: List[WebSocket] = []


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


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
async def run_analysis_pipeline(request: AnalysisRequest):
    """Execute complete analysis pipeline in background."""
    try:
        await update_status('running', 0, 'initialization', 'Starting analysis pipeline...')
        
        # Step 1: Extract YouTube comments
        await update_status('running', 10, 'extraction', 'Extracting YouTube comments...')
        
        extractor = YouTubeCommentExtractor(
            request.youtube_api_key,
            output_dir='data/outputs'
        )
        
        comments = extractor.collect_comments_until_5000(
            request.video_id,
            max_comments=request.max_comments
        )
        
        # Save outputs
        extractor.save_all_comments_csv()
        extractor.save_cleaned_comments_csv()
        channel_metadata_file = extractor.save_channel_metadata()
        
        await update_status('running', 30, 'extraction', 
                          f'Extracted {len(comments)} comments successfully')
        
        # Step 2: Create batches
        await update_status('running', 35, 'batching', 'Creating comment batches...')
        
        batch_files = extractor.create_batches(
            batch_size=request.batch_size,
            output_dir='data/batches'
        )
        
        await update_status('running', 40, 'batching', 
                          f'Created {len(batch_files)} batches')
        
        # Step 3: LLM batch processing
        await update_status('running', 45, 'llm_analysis', 'Processing batches with LLM...')
        
        processor = BatchProcessor(request.gemini_api_key, output_dir='data/outputs')
        
        # Process batches with progress updates
        for idx, batch_file in enumerate(batch_files, 1):
            progress = 45 + (idx / len(batch_files)) * 20
            await update_status('running', progress, 'llm_analysis',
                              f'Processing batch {idx}/{len(batch_files)}...')
            
            processor.process_batch(batch_file, idx)
        
        # Consolidate analyses
        comprehensive_file = processor.consolidate_all_analyses()
        
        await update_status('running', 65, 'llm_analysis', 
                          'LLM analysis complete')
        
        # Step 4: Sentiment analysis
        await update_status('running', 70, 'sentiment', 'Analyzing sentiment with transformers...')
        
        analyzer = SentimentAnalyzer(output_dir='data/outputs')
        df = analyzer.analyze_sentiment('data/outputs/cleaned_all_comments.csv')
        
        await update_status('running', 85, 'sentiment', 
                          'Sentiment analysis complete')
        
        # Save sentiment results
        analyzer.save_analyzed_comments()
        report_file = analyzer.generate_detailed_report()
        
        # Step 5: Generate visualizations
        await update_status('running', 90, 'visualization', 'Generating visualizations...')
        
        viz_files = analyzer.generate_visualizations()
        
        await update_status('running', 95, 'finalization', 'Finalizing results...')
        
        # Compile final results
        results = {
            'channel_info': extract_channel_info(channel_metadata_file),
            'total_comments': len(comments),
            'batches_processed': len(batch_files),
            'sentiment_summary': {
                'positive': int(df[df['sentiment_label'] == 'Positive'].shape[0]),
                'neutral': int(df[df['sentiment_label'] == 'Neutral'].shape[0]),
                'negative': int(df[df['sentiment_label'] == 'Negative'].shape[0]),
                'avg_score': float(df['confidence_score'].mean())
            },
            'files': {
                'comments_csv': 'data/outputs/all_comments.csv',
                'cleaned_csv': 'data/outputs/cleaned_all_comments.csv',
                'analyzed_csv': 'data/outputs/sentiment_analyzed_comments.csv',
                'detailed_report': report_file,
                'comprehensive_analysis': comprehensive_file,
                'visualizations': viz_files
            },
            'completed_at': datetime.now().isoformat()
        }
        
        analysis_state['results'] = results
        
        await update_status('completed', 100, 'done', 
                          'Analysis pipeline completed successfully!', results)
        
    except Exception as e:
        error_msg = f"Error in analysis pipeline: {str(e)}"
        await update_status('failed', 0, 'error', error_msg)
        raise


# API Endpoints

@app.get("/")
async def root():
    """API health check."""
    return {
        "name": "CreatorGPT API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.post("/api/analyze")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start new YouTube comment analysis.
    Runs in background and updates via WebSocket.
    """
    global analysis_state
    
    if analysis_state['status'] == 'running':
        raise HTTPException(status_code=409, detail="Analysis already in progress")
    
    # Reset state
    analysis_state = {
        'status': 'queued',
        'progress': 0,
        'current_step': 'queued',
        'message': 'Analysis queued',
        'results': None
    }
    
    # Run analysis in background
    background_tasks.add_task(run_analysis_pipeline, request)
    
    return {"message": "Analysis started", "status": "queued"}


@app.get("/api/status")
async def get_status():
    """Get current analysis status."""
    return AnalysisStatus(**analysis_state)


@app.get("/api/dashboard-data")
async def get_dashboard_data():
    """
    Serve aggregated data for dashboard UI.
    Includes sentiment distribution, trends, and key metrics.
    """
    if not analysis_state.get('results'):
        return JSONResponse(
            status_code=404,
            content={"error": "No analysis results available"}
        )
    
    results = analysis_state['results']
    
    # Load analyzed data
    try:
        df = pd.read_csv(results['files']['analyzed_csv'])
        
        # Prepare dashboard data
        dashboard_data = {
            'overview': {
                'total_comments': results['total_comments'],
                'video_title': results['channel_info'].get('video_title', 'N/A'),
                'channel_name': results['channel_info'].get('channel_title', 'N/A'),
                'avg_sentiment_score': results['sentiment_summary']['avg_score'],
                'analysis_date': results['completed_at']
            },
            'sentiment_distribution': results['sentiment_summary'],
            'trending_keywords': extract_trending_keywords(df),
            'batch_summaries': parse_batch_summaries(),
            'temporal_trends': get_temporal_trends(df),
            'engagement_metrics': get_engagement_metrics(df)
        }
        
        return dashboard_data
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error generating dashboard data: {str(e)}"}
        )


@app.get("/api/comprehensive-analysis")
async def get_comprehensive_analysis():
    """
    Return aggregated comprehensive report.
    Includes all batch analyses, sentiment insights, and recommendations.
    """
    if not analysis_state.get('results'):
        return JSONResponse(
            status_code=404,
            content={"error": "No analysis results available"}
        )
    
    results = analysis_state['results']
    
    try:
        # Read comprehensive analysis
        comprehensive_file = results['files']['comprehensive_analysis']
        with open(comprehensive_file, 'r', encoding='utf-8') as f:
            comprehensive_text = f.read()
        
        # Read detailed sentiment report
        report_file = results['files']['detailed_report']
        with open(report_file, 'r', encoding='utf-8') as f:
            sentiment_report = f.read()
        
        # Aggregate everything
        aggregated_report = {
            'channel_info': results['channel_info'],
            'sentiment_summary': results['sentiment_summary'],
            'llm_analysis': comprehensive_text,
            'sentiment_report': sentiment_report,
            'visualizations': results['files']['visualizations'],
            'recommendations': generate_recommendations(results),
            'generated_at': results['completed_at']
        }
        
        return aggregated_report
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error generating comprehensive analysis: {str(e)}"}
        )


@app.websocket("/ws/analysis")
async def websocket_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis updates.
    Clients receive progress updates as analysis runs.
    """
    await manager.connect(websocket)
    
    try:
        # Send current status immediately
        await websocket.send_json(analysis_state)
        
        # Keep connection alive
        while True:
            # Wait for messages (ping/pong)
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "status":
                await websocket.send_json(analysis_state)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Helper functions for dashboard data

def extract_trending_keywords(df: pd.DataFrame, top_n: int = 20) -> List[Dict]:
    """Extract trending keywords from comments."""
    from collections import Counter
    import re
    
    text_col = 'cleaned_text' if 'cleaned_text' in df.columns else 'text'
    all_text = ' '.join(df[text_col].astype(str).tolist())
    
    # Simple word extraction (can be enhanced with NLP)
    words = re.findall(r'\b\w+\b', all_text.lower())
    
    # Filter stopwords (basic list)
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    
    words = [w for w in words if w not in stopwords and len(w) > 3]
    
    word_counts = Counter(words).most_common(top_n)
    
    return [{'word': word, 'count': count} for word, count in word_counts]


def parse_batch_summaries() -> List[Dict]:
    """Parse summaries from batch analysis files."""
    summaries = []
    batch_dir = 'data/outputs'
    
    try:
        files = sorted([f for f in os.listdir(batch_dir) if f.startswith('analyzed_comments_batch_')])
        
        for file in files:
            batch_num = int(file.split('_')[-1].replace('.txt', ''))
            filepath = os.path.join(batch_dir, file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract key themes (simple parsing)
            themes = []
            if "KEY THEMES" in content:
                lines = content.split('\n')
                in_themes = False
                for line in lines:
                    if "KEY THEMES" in line:
                        in_themes = True
                        continue
                    if in_themes and (line.strip().startswith('-') or line.strip().startswith('Theme')):
                        themes.append(line.strip())
                    elif in_themes and line.strip() and not line.strip().startswith(' ') and len(themes) > 0:
                        break
            
            summaries.append({
                'batch_number': batch_num,
                'themes': themes[:3],  # Top 3 themes
                'file': file
            })
    
    except Exception as e:
        print(f"Error parsing batch summaries: {e}")
    
    return summaries


def get_temporal_trends(df: pd.DataFrame) -> Dict:
    """Calculate temporal sentiment trends."""
    if 'published_at' not in df.columns:
        return {}
    
    df_temp = df.copy()
    df_temp['published_at'] = pd.to_datetime(df_temp['published_at'])
    df_temp['date'] = df_temp['published_at'].dt.date
    
    daily = df_temp.groupby('date').agg({
        'confidence_score': 'mean',
        'sentiment_label': 'count'
    }).reset_index()
    
    return {
        'daily_trends': [
            {
                'date': str(row['date']),
                'avg_score': float(row['confidence_score']),
                'count': int(row['sentiment_label'])
            }
            for _, row in daily.iterrows()
        ]
    }


def get_engagement_metrics(df: pd.DataFrame) -> Dict:
    """Calculate engagement-based metrics."""
    if 'likes' not in df.columns:
        return {}
    
    return {
        'total_likes': int(df['likes'].sum()),
        'avg_likes_per_comment': float(df['likes'].mean()),
        'top_liked_sentiment': df.nlargest(100, 'likes')['sentiment_label'].mode()[0] if len(df) > 0 else 'N/A',
        'high_engagement_positive': int(df[(df['likes'] > df['likes'].quantile(0.75)) & 
                                           (df['sentiment_label'] == 'Positive')].shape[0])
    }


def generate_recommendations(results: Dict) -> List[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations = []
    
    sentiment_summary = results['sentiment_summary']
    total = sum(sentiment_summary.values()) - sentiment_summary.get('avg_score', 0)
    
    # Sentiment-based recommendations
    positive_pct = (sentiment_summary['positive'] / total * 100) if total > 0 else 0
    negative_pct = (sentiment_summary['negative'] / total * 100) if total > 0 else 0
    
    if positive_pct > 70:
        recommendations.append("Strong positive sentiment detected. Consider creating similar content to maintain engagement.")
    
    if negative_pct > 30:
        recommendations.append("Significant negative sentiment found. Review criticism themes and address viewer concerns.")
    
    if sentiment_summary['avg_score'] < 45:
        recommendations.append("Overall sentiment is below neutral. Consider community engagement to understand pain points.")
    
    recommendations.append("Analyze batch summaries for specific content suggestions from viewers.")
    recommendations.append("Monitor temporal trends to identify optimal posting times.")
    
    return recommendations


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
