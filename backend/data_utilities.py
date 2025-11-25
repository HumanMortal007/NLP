import json
import os
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re
from collections import Counter


def extract_channel_info(metadata_file: str) -> Dict:
    """
    Extract channel and video information from metadata file.
    
    Args:
        metadata_file: Path to youtube_analytics.json
        
    Returns:
        Dict with channel information
    """
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'video_id': data.get('video_id'),
            'video_title': data.get('video_title'),
            'channel_id': data.get('channel_id'),
            'channel_title': data.get('channel_title'),
            'channel_subscribers': data.get('channel_subscribers'),
            'video_views': data.get('video_views'),
            'video_likes': data.get('video_likes'),
            'total_video_comments': data.get('video_comments_count'),
            'comments_collected': data.get('total_comments_collected'),
            'published_at': data.get('published_at'),
            'extraction_date': data.get('extraction_date'),
            'collection_stats': data.get('collection_stats', {})
        }
    except Exception as e:
        print(f"Error extracting channel info: {e}")
        return {}


def parse_batch_analysis(analysis_file: str) -> Dict:
    """
    Parse structured data from LLM batch analysis file.
    
    Args:
        analysis_file: Path to analyzed_comments_batch_X.txt
        
    Returns:
        Dict with extracted themes, suggestions, sentiment, etc.
    """
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = {
            'themes': [],
            'suggestions': [],
            'appreciation': [],
            'concerns': [],
            'top_comments': [],
            'sentiment_distribution': {},
            'recommendations': []
        }
        
        # Extract sentiment distribution
        sentiment_match = re.search(r'Positive comments:\s*(\d+\.?\d*)%', content)
        if sentiment_match:
            result['sentiment_distribution']['positive'] = float(sentiment_match.group(1))
        
        neutral_match = re.search(r'Neutral comments:\s*(\d+\.?\d*)%', content)
        if neutral_match:
            result['sentiment_distribution']['neutral'] = float(neutral_match.group(1))
        
        negative_match = re.search(r'Negative comments:\s*(\d+\.?\d*)%', content)
        if negative_match:
            result['sentiment_distribution']['negative'] = float(negative_match.group(1))
        
        # Extract themes
        result['themes'] = extract_section_items(content, 'KEY THEMES')
        
        # Extract suggestions
        result['suggestions'] = extract_section_items(content, 'VIEWER SUGGESTIONS')
        
        # Extract appreciation
        result['appreciation'] = extract_section_items(content, 'APPRECIATION')
        
        # Extract concerns
        result['concerns'] = extract_section_items(content, 'CONCERNS')
        
        # Extract top comments
        result['top_comments'] = extract_section_items(content, 'TOP COMMENTS')
        
        # Extract recommendations
        result['recommendations'] = extract_section_items(content, 'RECOMMENDATIONS')
        
        return result
        
    except Exception as e:
        print(f"Error parsing batch analysis: {e}")
        return {}


def extract_section_items(content: str, section_name: str, max_items: int = 10) -> List[str]:
    """
    Extract items from a specific section of the analysis.
    
    Args:
        content: Full analysis text
        section_name: Section header to look for
        max_items: Maximum number of items to extract
        
    Returns:
        List of extracted items
    """
    items = []
    
    if section_name not in content:
        return items
    
    lines = content.split('\n')
    in_section = False
    
    for line in lines:
        if section_name in line:
            in_section = True
            continue
        
        if in_section:
            # Check if we've moved to next section
            if line.strip() and not line.startswith(' ') and not line.startswith('\t') and \
               not line.startswith('-') and not line.startswith('•') and \
               not line[0].isdigit() and len(items) > 0:
                break
            
            # Extract bullet points or numbered items
            if line.strip().startswith('-') or line.strip().startswith('•') or \
               (line.strip() and line.strip()[0].isdigit() and '.' in line[:5]):
                # Clean the item
                item = re.sub(r'^[\s\-•\d.]+', '', line).strip()
                if item:
                    items.append(item)
            
            if len(items) >= max_items:
                break
    
    return items


def extract_comments_from_detailed_results(results_file: str, 
                                           category: str = 'positive',
                                           top_n: int = 10) -> List[Dict]:
    """
    Extract specific comments from detailed sentiment results.
    
    Args:
        results_file: Path to detailed_sentiment_results.txt
        category: 'positive', 'negative', or 'neutral'
        top_n: Number of comments to extract
        
    Returns:
        List of comment dictionaries
    """
    comments = []
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine section to look for
        if category.lower() == 'positive':
            section = 'TOP 10 MOST POSITIVE COMMENTS'
        elif category.lower() == 'negative':
            section = 'TOP 10 MOST NEGATIVE COMMENTS'
        else:
            return comments
        
        if section not in content:
            return comments
        
        lines = content.split('\n')
        in_section = False
        current_comment = {}
        
        for line in lines:
            if section in line:
                in_section = True
                continue
            
            if in_section:
                # Check for next section
                if line.startswith('-' * 20) and len(comments) > 0:
                    break
                
                if line.startswith('Score:'):
                    if current_comment:
                        comments.append(current_comment)
                        current_comment = {}
                    
                    score = re.search(r'Score:\s*(\d+)', line)
                    if score:
                        current_comment['score'] = int(score.group(1))
                
                elif line.startswith('Comment:'):
                    current_comment['text'] = line.replace('Comment:', '').strip()
                
                elif line.startswith('Author:'):
                    current_comment['author'] = line.replace('Author:', '').strip()
                
                elif line.startswith('Likes:'):
                    likes = re.search(r'Likes:\s*(\d+)', line)
                    if likes:
                        current_comment['likes'] = int(likes.group(1))
        
        # Add last comment
        if current_comment:
            comments.append(current_comment)
        
        return comments[:top_n]
        
    except Exception as e:
        print(f"Error extracting comments: {e}")
        return []


def aggregate_analytics(output_dir: str = 'data/outputs') -> Dict:
    """
    Aggregate all analytics from various output files.
    
    Args:
        output_dir: Directory containing analysis outputs
        
    Returns:
        Comprehensive analytics dictionary
    """
    analytics = {
        'channel_info': {},
        'comment_stats': {},
        'sentiment_summary': {},
        'batch_insights': [],
        'temporal_trends': {},
        'engagement_metrics': {},
        'top_keywords': [],
        'top_keyword_terms': [],
        'generated_at': datetime.now().isoformat()
    }
    
    try:
        # Load channel info
        metadata_file = os.path.join(output_dir, 'youtube_analytics.json')
        if os.path.exists(metadata_file):
            analytics['channel_info'] = extract_channel_info(metadata_file)
        
        # Load sentiment analysis
        sentiment_file = os.path.join(output_dir, 'sentiment_analyzed_comments.csv')
        if os.path.exists(sentiment_file):
            df = pd.read_csv(sentiment_file)
            
            analytics['comment_stats'] = {
                'total_comments': len(df),
                'avg_comment_length': df['text'].str.len().mean() if 'text' in df.columns else 0,
                'total_likes': df['likes'].sum() if 'likes' in df.columns else 0
            }
            
            analytics['sentiment_summary'] = {
                'positive_count': int(df[df['sentiment_label'] == 'Positive'].shape[0]),
                'neutral_count': int(df[df['sentiment_label'] == 'Neutral'].shape[0]),
                'negative_count': int(df[df['sentiment_label'] == 'Negative'].shape[0]),
                'avg_confidence_score': float(df['confidence_score'].mean()),
                'median_confidence_score': float(df['confidence_score'].median()),
                'positive_percentage': float(df[df['sentiment_label'] == 'Positive'].shape[0] / len(df) * 100),
                'negative_percentage': float(df[df['sentiment_label'] == 'Negative'].shape[0] / len(df) * 100)
            }
            
            # Temporal trends
            if 'published_at' in df.columns:
                df['published_at'] = pd.to_datetime(df['published_at'])
                analytics['temporal_trends'] = calculate_temporal_trends(df)
            
            # Engagement metrics
            if 'likes' in df.columns:
                analytics['engagement_metrics'] = calculate_engagement_metrics(df)
            
            # Top keywords
            analytics['top_keywords'] = extract_keywords(df)
            # Also expose a simple list of keyword strings for easy joins/usage
            analytics['top_keyword_terms'] = [k['keyword'] for k in analytics['top_keywords']]
        
        # Parse batch analyses
        batch_files = [f for f in os.listdir(output_dir) if f.startswith('analyzed_comments_batch_')]
        for batch_file in sorted(batch_files):
            batch_path = os.path.join(output_dir, batch_file)
            batch_data = parse_batch_analysis(batch_path)
            batch_data['batch_file'] = batch_file
            analytics['batch_insights'].append(batch_data)
        
        return analytics

    except Exception as e:
        print(f"Error aggregating analytics: {e}")
        return analytics


def calculate_temporal_trends(df: pd.DataFrame) -> Dict:
    """Calculate temporal trends from comment data."""
    trends = {}
    
    try:
        # Daily trends
        df['date'] = df['published_at'].dt.date
        daily = df.groupby('date').agg({
            'confidence_score': ['mean', 'count'],
            'sentiment_label': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        trends['daily'] = daily.to_dict('records')
        
        # Hourly patterns
        df['hour'] = df['published_at'].dt.hour
        hourly = df.groupby('hour')['confidence_score'].mean().to_dict()
        trends['hourly_avg_sentiment'] = hourly
        
        # Weekly patterns
        df['day_of_week'] = df['published_at'].dt.day_name()
        weekly = df.groupby('day_of_week')['confidence_score'].mean().to_dict()
        trends['weekly_avg_sentiment'] = weekly
        
    except Exception as e:
        print(f"Error calculating temporal trends: {e}")
    
    return trends


def generate_creator_json(analytics: Dict, df: Optional[pd.DataFrame] = None, output_file: str = None) -> Optional[str]:
    """Produce a minimal, creator-focused JSON summary.

    Contains: top_keywords (strings), sentiment_breakdown (counts + avg confidence per label),
    top positive/negative comments (top 3 each) and a short actionables list (from batch_insights).
    """
    try:
        if output_file is None:
            output_file = os.path.join('data', 'outputs', 'creator_summary.json')

        report = {
            'generated_at': analytics.get('generated_at'),
            'video_info': analytics.get('channel_info', {}),
            'top_keywords': analytics.get('top_keyword_terms', []),
            'sentiment_breakdown': analytics.get('sentiment_summary', {}),
            'action_items': [],
            'top_positive_comments': [],
            'top_negative_comments': []
        }

        # derive top comments from DataFrame if available
        if df is not None and len(df) > 0:
            text_col = 'cleaned_text' if 'cleaned_text' in df.columns else ('text' if 'text' in df.columns else df.columns[0])

            top_pos = df.nlargest(min(3, len(df)), 'confidence_score')
            for _, r in top_pos.iterrows():
                report['top_positive_comments'].append({
                    'text': str(r.get(text_col, ''))[:300],
                    'score': float(r.get('confidence_score', 0.0)),
                    'likes': int(r.get('likes', 0)) if 'likes' in r.index else 0
                })

            top_neg = df.nsmallest(min(3, len(df)), 'confidence_score')
            for _, r in top_neg.iterrows():
                report['top_negative_comments'].append({
                    'text': str(r.get(text_col, ''))[:300],
                    'score': float(r.get('confidence_score', 0.0)),
                    'likes': int(r.get('likes', 0)) if 'likes' in r.index else 0
                })

        # collect simple action items from batch insights
        if analytics.get('batch_insights'):
            actions = []
            for b in analytics['batch_insights'][:3]:
                for s in b.get('suggestions', [])[:2]:
                    actions.append(s)
            report['action_items'] = actions

        # Save
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✓ Creator summary saved to {output_file}")
        return output_file

    except Exception as e:
        print(f"Error generating creator JSON summary: {e}")
        return None


def calculate_engagement_metrics(df: pd.DataFrame) -> Dict:
    """Calculate engagement-related metrics."""
    metrics = {}
    
    try:
        metrics['total_likes'] = int(df['likes'].sum())
        metrics['avg_likes_per_comment'] = float(df['likes'].mean())
        metrics['median_likes'] = float(df['likes'].median())
        
        # Top liked comments sentiment
        top_10_percent = df.nlargest(int(len(df) * 0.1), 'likes')
        metrics['top_liked_sentiment_dist'] = top_10_percent['sentiment_label'].value_counts().to_dict()
        
        # High engagement correlation with sentiment
        high_engagement = df[df['likes'] > df['likes'].quantile(0.75)]
        metrics['high_engagement_avg_sentiment'] = float(high_engagement['confidence_score'].mean())
        
        # Replies analysis
        if 'is_reply' in df.columns:
            metrics['total_replies'] = int(df[df['is_reply'] == True].shape[0])
            metrics['reply_rate'] = float(df[df['is_reply'] == True].shape[0] / len(df) * 100)
        
    except Exception as e:
        print(f"Error calculating engagement metrics: {e}")
    
    return metrics


def extract_keywords(df: pd.DataFrame, top_n: int = 50) -> List[Dict]:
    """Extract top keywords from comments."""
    try:
        text_col = 'cleaned_text' if 'cleaned_text' in df.columns else 'text'
        all_text = ' '.join(df[text_col].astype(str).tolist())
        
        # Extract words
        words = re.findall(r'\b\w+\b', all_text.lower())
        
        # Common stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
            'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'just', 'dont',
            'im', 'youre', 'cant', 'wont', 'really', 'also', 'well', 'even', 'still'
        }
        
        # Filter
        words = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Count
        word_counts = Counter(words).most_common(top_n)
        
        return [{'keyword': word, 'count': count} for word, count in word_counts]
        
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []


def generate_summary_report(analytics: Dict, output_file: str = 'summary_report.txt') -> str:
    """
    Generate a human-readable summary report.
    
    Args:
        analytics: Aggregated analytics dictionary
        output_file: Output file path
        
    Returns:
        Path to generated report
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("YOUTUBE COMMENT ANALYSIS - EXECUTIVE SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {analytics['generated_at']}\n\n")
            
            # Channel info
            if analytics['channel_info']:
                info = analytics['channel_info']
                f.write("-" * 80 + "\n")
                f.write("VIDEO & CHANNEL INFORMATION\n")
                f.write("-" * 80 + "\n")
                f.write(f"Video: {info.get('video_title', 'N/A')}\n")
                f.write(f"Channel: {info.get('channel_title', 'N/A')}\n")
                f.write(f"Subscribers: {info.get('channel_subscribers', 0):,}\n")
                f.write(f"Video Views: {info.get('video_views', 0):,}\n")
                f.write(f"Video Likes: {info.get('video_likes', 0):,}\n")
                f.write(f"Comments Analyzed: {info.get('comments_collected', 0):,}\n\n")
            
            # Sentiment summary
            if analytics['sentiment_summary']:
                sent = analytics['sentiment_summary']
                f.write("-" * 80 + "\n")
                f.write("SENTIMENT ANALYSIS SUMMARY\n")
                f.write("-" * 80 + "\n")
                f.write(f"Positive: {sent.get('positive_percentage', 0):.1f}% ({sent.get('positive_count', 0):,} comments)\n")
                f.write(f"Negative: {sent.get('negative_percentage', 0):.1f}% ({sent.get('negative_count', 0):,} comments)\n")
                f.write(f"Neutral: {sent.get('neutral_count', 0):,} comments\n")
                f.write(f"\nAverage Sentiment Score: {sent.get('avg_confidence_score', 0):.2f}/100\n")
                f.write(f"Median Sentiment Score: {sent.get('median_confidence_score', 0):.2f}/100\n\n")
            
            # Top keywords
            if analytics['top_keywords']:
                f.write("-" * 80 + "\n")
                f.write("TOP 20 KEYWORDS\n")
                f.write("-" * 80 + "\n")
                for i, kw in enumerate(analytics['top_keywords'][:20], 1):
                    f.write(f"{i}. {kw['keyword']} ({kw['count']} mentions)\n")
                f.write("\n")
            
            # Engagement metrics
            if analytics['engagement_metrics']:
                eng = analytics['engagement_metrics']
                f.write("-" * 80 + "\n")
                f.write("ENGAGEMENT METRICS\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total Likes: {eng.get('total_likes', 0):,}\n")
                f.write(f"Avg Likes per Comment: {eng.get('avg_likes_per_comment', 0):.2f}\n")
                f.write(f"High Engagement Avg Sentiment: {eng.get('high_engagement_avg_sentiment', 0):.2f}/100\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF SUMMARY REPORT\n")
            f.write("=" * 80 + "\n")
        
        print(f"✓ Summary report saved to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error generating summary report: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    analytics = aggregate_analytics('data/outputs')
    print(json.dumps(analytics, indent=2, default=str))
    
    generate_summary_report(analytics, 'data/outputs/summary_report.txt')
