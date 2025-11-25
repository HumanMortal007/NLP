"""
Complete YouTube Comment Sentiment Analyzer
Combines extraction, LLM analysis, and sentiment scoring in one script
"""

import os
import re
import csv
import json
import time
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.generativeai as genai
from transformers import pipeline
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==================== CONFIGURATION ====================
YOUTUBE_API_KEY = 'AIzaSyA-PBiOG1Xj3kn1ZnKQxyiLzcmmUnl2u-c'
GEMINI_API_KEY = 'AIzaSyBA3yNOiZhhjw1sBzzquECwZU9ppUedN2A'

# Create output directories
os.makedirs('nlp/analysis_results', exist_ok=True)
os.makedirs('nlp/visualizations', exist_ok=True)


# ==================== YOUTUBE EXTRACTION ====================

def get_all_replies(youtube, comment_id, replies, token=''):
    """Fetch replies to a given comment."""
    try:
        replies_response = youtube.comments().list(
            part='snippet',
            parentId=comment_id,
            pageToken=token,
            maxResults=100
        ).execute()

        for reply in replies_response['items']:
            replies.append({
                'text': reply['snippet']['textDisplay'],
                'author': reply['snippet']['authorDisplayName'],
                'likes': reply['snippet']['likeCount'],
                'published_at': reply['snippet']['publishedAt']
            })

        if 'nextPageToken' in replies_response:
            return get_all_replies(youtube, comment_id, replies, replies_response['nextPageToken'])
    except HttpError as e:
        print(f"Error fetching replies: {e}")
    
    return replies


def get_comments(youtube, video_id, max_comments=1000):
    """Fetch all top-level comments for a given YouTube video."""
    comments = []
    next_page_token = None
    
    print(f"\n{'='*60}")
    print(f"Extracting comments from video: {video_id}")
    print(f"{'='*60}\n")
    
    while len(comments) < max_comments:
        try:
            video_response = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                pageToken=next_page_token,
                maxResults=100,
                order='relevance'
            ).execute()

            for item in video_response['items']:
                if len(comments) >= max_comments:
                    break
                
                comment = item['snippet']['topLevelComment']['snippet']
                
                comment_data = {
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'likes': comment['likeCount'],
                    'published_at': comment['publishedAt'],
                    'is_reply': False
                }
                
                comments.append(comment_data)
                
                # Get replies
                total_reply_count = item['snippet']['totalReplyCount']
                if total_reply_count > 0 and len(comments) < max_comments:
                    if 'replies' in item:
                        for reply in item['replies']['comments']:
                            if len(comments) >= max_comments:
                                break
                            reply_snippet = reply['snippet']
                            comments.append({
                                'text': reply_snippet['textDisplay'],
                                'author': reply_snippet['authorDisplayName'],
                                'likes': reply_snippet['likeCount'],
                                'published_at': reply_snippet['publishedAt'],
                                'is_reply': True
                            })

                # Progress update
                if len(comments) % 100 == 0:
                    print(f"Progress: {len(comments)}/{max_comments} comments extracted...")

            next_page_token = video_response.get('nextPageToken')
            if not next_page_token:
                break
            
            time.sleep(0.1)  # Rate limiting
            
        except HttpError as e:
            print(f"Error: {e}")
            break
    
    print(f"\n✓ Extracted {len(comments)} comments\n")
    return comments


def get_youtube_client(api_key):
    """Initialize the YouTube API client."""
    return build('youtube', 'v3', developerKey=api_key)


def clean_text(text):
    """Clean and preprocess comment text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove URLs
    text = re.sub(r'http\S+|www.\S+', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()


def save_comments_csv(comments, filename='nlp/analysis_results/comments.csv'):
    """Save comments to CSV file."""
    df = pd.DataFrame(comments)
    df['cleaned_text'] = df['text'].apply(clean_text)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"✓ Saved comments to {filename}")
    return df


# ==================== GEMINI LLM ANALYSIS ====================

def analyze_with_gemini(comments_batch, batch_num):
    """Analyze a batch of comments with Gemini API."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    comments_text = '\n'.join([f"{i+1}. {c}" for i, c in enumerate(comments_batch)])
    
    prompt = f"""Analyze these YouTube comments and provide:

COMMENTS:
{comments_text}

Provide analysis in this structure:

1. SENTIMENT OVERVIEW
   - Overall sentiment (Positive/Neutral/Negative percentages)
   - Dominant emotions

2. KEY THEMES (Top 5)
   - Main topics discussed

3. VIEWER FEEDBACK
   - What viewers liked
   - What viewers want improved
   - Common suggestions

4. NOTABLE COMMENTS
   - Most insightful comments (quote 2-3)

Keep it concise and actionable."""

    try:
        print(f"Analyzing batch {batch_num} with Gemini AI...")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return f"Error analyzing batch {batch_num}"


def create_batches_and_analyze(comments, batch_size=50):
    """Create batches and analyze with Gemini."""
    print(f"\n{'='*60}")
    print(f"LLM Analysis with Gemini")
    print(f"{'='*60}\n")
    
    all_analyses = []
    texts = [clean_text(c['text']) for c in comments]
    
    for i in range(0, len(texts), batch_size):
        batch_num = i // batch_size + 1
        batch = texts[i:i + batch_size]
        
        analysis = analyze_with_gemini(batch, batch_num)
        all_analyses.append({
            'batch_num': batch_num,
            'analysis': analysis
        })
        
        # Save individual batch
        with open(f'nlp/analysis_results/batch_{batch_num}_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(f"BATCH {batch_num} ANALYSIS\n{'='*60}\n\n{analysis}")
        
        print(f"✓ Batch {batch_num} analyzed\n")
        time.sleep(2)  # Rate limiting
    
    # Save consolidated analysis
    with open('nlp/analysis_results/gemini_full_analysis.txt', 'w', encoding='utf-8') as f:
        f.write("COMPLETE GEMINI ANALYSIS REPORT\n")
        f.write(f"{'='*80}\n\n")
        for item in all_analyses:
            f.write(f"BATCH {item['batch_num']}\n{'-'*80}\n{item['analysis']}\n\n")
    
    print(f"✓ LLM analysis complete! Analyzed {len(all_analyses)} batches\n")
    return all_analyses


# ==================== SENTIMENT ANALYSIS ====================

def analyze_sentiment(df):
    """Analyze sentiment using transformer model."""
    print(f"\n{'='*60}")
    print(f"Sentiment Analysis with Transformers")
    print(f"{'='*60}\n")
    
    print("Loading sentiment model...")
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        return_all_scores=True
    )
    print("✓ Model loaded\n")
    
    results = []
    total = len(df)
    
    for idx, row in df.iterrows():
        text = str(row['cleaned_text'])[:512]  # Limit to 512 tokens
        
        try:
            predictions = sentiment_pipeline(text)[0]
            pos_score = next(p['score'] for p in predictions if p['label'] == 'POSITIVE')
            neg_score = next(p['score'] for p in predictions if p['label'] == 'NEGATIVE')
            
            # Convert to 0-100 score
            if pos_score > neg_score:
                score = int(50 + (pos_score * 50))
                label = "Positive" if score >= 60 else "Neutral"
            else:
                score = int(50 - (neg_score * 50))
                label = "Negative" if score < 40 else "Neutral"
            
            results.append({
                'sentiment_label': label,
                'confidence_score': score,
                'positive_prob': round(pos_score, 4),
                'negative_prob': round(neg_score, 4)
            })
            
        except Exception as e:
            results.append({
                'sentiment_label': 'Neutral',
                'confidence_score': 50,
                'positive_prob': 0.5,
                'negative_prob': 0.5
            })
        
        if (idx + 1) % 50 == 0 or (idx + 1) == total:
            print(f"Progress: {idx + 1}/{total} comments analyzed...")
    
    # Add to dataframe
    for key in results[0].keys():
        df[key] = [r[key] for r in results]
    
    # Save analyzed data
    df.to_csv('nlp/analysis_results/sentiment_analyzed.csv', index=False, encoding='utf-8')
    print(f"\n✓ Sentiment analysis complete!\n")
    
    return df


# ==================== VISUALIZATION ====================

def generate_visualizations(df):
    """Generate visualization charts."""
    print(f"\n{'='*60}")
    print(f"Generating Visualizations")
    print(f"{'='*60}\n")
    
    sns.set_style("whitegrid")
    
    # 1. Sentiment Pie Chart
    plt.figure(figsize=(10, 8))
    sentiment_counts = df['sentiment_label'].value_counts()
    colors = {'Positive': '#4CAF50', 'Neutral': '#FFC107', 'Negative': '#F44336'}
    pie_colors = [colors.get(label, '#999') for label in sentiment_counts.index]
    
    plt.pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%',
            colors=pie_colors, startangle=90, textprops={'fontsize': 14, 'weight': 'bold'})
    plt.title('Sentiment Distribution', fontsize=18, weight='bold', pad=20)
    plt.savefig('nlp/visualizations/sentiment_pie_chart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved: sentiment_pie_chart.png")
    
    # 2. Score Distribution
    plt.figure(figsize=(12, 6))
    plt.hist(df['confidence_score'], bins=50, color='#2196F3', edgecolor='black', alpha=0.7)
    plt.xlabel('Confidence Score', fontsize=14, weight='bold')
    plt.ylabel('Frequency', fontsize=14, weight='bold')
    plt.title('Sentiment Score Distribution', fontsize=16, weight='bold', pad=20)
    plt.axvline(df['confidence_score'].mean(), color='red', linestyle='--', 
               linewidth=2, label=f'Mean: {df["confidence_score"].mean():.1f}')
    plt.legend(fontsize=12)
    plt.savefig('nlp/visualizations/score_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved: score_distribution.png")
    
    # 3. Top Keywords
    from collections import Counter
    all_text = ' '.join(df['cleaned_text'].astype(str).tolist())
    words = re.findall(r'\b\w+\b', all_text.lower())
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'was', 'are'}
    words = [w for w in words if w not in stopwords and len(w) > 3]
    top_words = Counter(words).most_common(15)
    
    plt.figure(figsize=(12, 6))
    words_list, counts = zip(*top_words)
    plt.barh(range(len(words_list)), counts, color='#FF9800')
    plt.yticks(range(len(words_list)), words_list)
    plt.xlabel('Frequency', fontsize=14, weight='bold')
    plt.title('Top 15 Keywords', fontsize=16, weight='bold', pad=20)
    plt.gca().invert_yaxis()
    plt.savefig('nlp/visualizations/top_keywords.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved: top_keywords.png")
    
    print(f"\n✓ All visualizations generated!\n")


# ==================== REPORTING ====================

def generate_summary_report(df, gemini_analyses):
    """Generate comprehensive summary report."""
    report_path = 'nlp/analysis_results/FINAL_REPORT.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("YOUTUBE COMMENT ANALYSIS - COMPLETE REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Comments Analyzed: {len(df)}\n\n")
        
        # Sentiment Summary
        f.write("-"*80 + "\n")
        f.write("SENTIMENT ANALYSIS SUMMARY\n")
        f.write("-"*80 + "\n\n")
        
        sentiment_dist = df['sentiment_label'].value_counts()
        for sentiment, count in sentiment_dist.items():
            percentage = (count / len(df)) * 100
            f.write(f"{sentiment}: {count} ({percentage:.1f}%)\n")
        
        f.write(f"\nAverage Sentiment Score: {df['confidence_score'].mean():.2f}/100\n")
        f.write(f"Median Sentiment Score: {df['confidence_score'].median():.2f}/100\n\n")
        
        # Top Positive Comments
        f.write("-"*80 + "\n")
        f.write("TOP 5 MOST POSITIVE COMMENTS\n")
        f.write("-"*80 + "\n\n")
        
        top_positive = df.nlargest(5, 'confidence_score')
        for idx, row in top_positive.iterrows():
            f.write(f"Score: {row['confidence_score']}/100\n")
            f.write(f"Comment: {row['text'][:200]}...\n")
            f.write(f"Likes: {row['likes']}\n\n")
        
        # Gemini Insights
        f.write("-"*80 + "\n")
        f.write("GEMINI AI INSIGHTS\n")
        f.write("-"*80 + "\n\n")
        
        for item in gemini_analyses:
            f.write(f"BATCH {item['batch_num']}:\n{item['analysis']}\n\n")
        
        f.write("="*80 + "\n")
        f.write("END OF REPORT\n")
        f.write("="*80 + "\n")
    
    print(f"✓ Final report saved to {report_path}\n")


# ==================== MAIN FUNCTION ====================

def main(video_id, max_comments=1000):
    """Main execution function."""
    print("\n" + "="*80)
    print("YOUTUBE COMMENT SENTIMENT ANALYZER")
    print("="*80)
    print(f"\nVideo ID: {video_id}")
    print(f"Max Comments: {max_comments}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Extract Comments
    youtube = get_youtube_client(YOUTUBE_API_KEY)
    comments = get_comments(youtube, video_id, max_comments)
    
    if not comments:
        print("❌ No comments found!")
        return
    
    # Step 2: Save and Clean
    df = save_comments_csv(comments)
    
    # Step 3: Gemini LLM Analysis
    gemini_analyses = create_batches_and_analyze(comments, batch_size=50)
    
    # Step 4: Sentiment Analysis
    df = analyze_sentiment(df)
    
    # Step 5: Generate Visualizations
    generate_visualizations(df)
    
    # Step 6: Create Final Report
    generate_summary_report(df, gemini_analyses)
    
    # Print Summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\n📊 Results:")
    print(f"   Total Comments: {len(df)}")
    print(f"   Positive: {len(df[df['sentiment_label']=='Positive'])} ({len(df[df['sentiment_label']=='Positive'])/len(df)*100:.1f}%)")
    print(f"   Neutral: {len(df[df['sentiment_label']=='Neutral'])} ({len(df[df['sentiment_label']=='Neutral'])/len(df)*100:.1f}%)")
    print(f"   Negative: {len(df[df['sentiment_label']=='Negative'])} ({len(df[df['sentiment_label']=='Negative'])/len(df)*100:.1f}%)")
    print(f"   Average Score: {df['confidence_score'].mean():.2f}/100")
    print(f"\n📁 Output Files:")
    print(f"   CSV: nlp/analysis_results/sentiment_analyzed.csv")
    print(f"   Report: nlp/analysis_results/FINAL_REPORT.txt")
    print(f"   Gemini Analysis: nlp/analysis_results/gemini_full_analysis.txt")
    print(f"   Visualizations: nlp/visualizations/")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Your video ID
    video_id = 'mME51l0K9yA'
    
    # Run complete analysis
    main(video_id, max_comments=500)  # Start with 500 for testing
