import os
import json
import csv
import re
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from typing import List, Dict, Optional
import time


class YouTubeCommentExtractor:
    """
    Enhanced YouTube comment extraction with quota management,
    progress tracking, and channel analytics.
    """
    
    def __init__(self, api_key: str, output_dir: str = "data"):
        self.api_key = api_key
        self.output_dir = output_dir
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.comments = []
        self.channel_info = {}
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
    def get_video_details(self, video_id: str) -> Dict:
        """Fetch video metadata including channel information."""
        try:
            response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            if not response['items']:
                raise ValueError(f"Video {video_id} not found")
                
            video = response['items'][0]
            
            # Extract channel info
            channel_id = video['snippet']['channelId']
            channel_response = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            ).execute()
            
            channel = channel_response['items'][0]
            
            self.channel_info = {
                'video_id': video_id,
                'video_title': video['snippet']['title'],
                'channel_id': channel_id,
                'channel_title': channel['snippet']['title'],
                'channel_subscribers': int(channel['statistics'].get('subscriberCount', 0)),
                'video_views': int(video['statistics'].get('viewCount', 0)),
                'video_likes': int(video['statistics'].get('likeCount', 0)),
                'video_comments_count': int(video['statistics'].get('commentCount', 0)),
                'published_at': video['snippet']['publishedAt'],
                'extraction_date': datetime.now().isoformat()
            }
            
            return self.channel_info
            
        except HttpError as e:
            print(f"Error fetching video details: {e}")
            raise
    
    def get_all_replies(self, comment_id: str) -> List[Dict]:
        """Fetch all replies to a specific comment."""
        replies = []
        next_page_token = None
        
        while True:
            try:
                response = self.youtube.comments().list(
                    part='snippet',
                    parentId=comment_id,
                    pageToken=next_page_token,
                    maxResults=100
                ).execute()
                
                for reply in response['items']:
                    replies.append({
                        'text': reply['snippet']['textDisplay'],
                        'author': reply['snippet']['authorDisplayName'],
                        'likes': reply['snippet']['likeCount'],
                        'published_at': reply['snippet']['publishedAt'],
                        'is_reply': True
                    })
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                print(f"Error fetching replies: {e}")
                break
                
        return replies
    
    def collect_comments_until_5000(self, video_id: str, 
                                     max_comments: int = 5000,
                                     days_filter: Optional[int] = None) -> List[Dict]:
        """
        Collect up to max_comments from a video with optional date filtering.
        Includes progress logging and resumable functionality.
        """
        self.get_video_details(video_id)
        self.comments = []
        next_page_token = None
        comment_count = 0
        
        # Date filter setup
        cutoff_date = None
        if days_filter:
            cutoff_date = datetime.now() - timedelta(days=days_filter)
        
        print(f"Starting comment collection for video: {self.channel_info['video_title']}")
        print(f"Target: {max_comments} comments")
        
        while comment_count < max_comments:
            try:
                response = self.youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    pageToken=next_page_token,
                    maxResults=100,
                    order='relevance'
                ).execute()
                
                for item in response['items']:
                    # Check if we've reached the limit
                    if comment_count >= max_comments:
                        break
                    
                    comment = item['snippet']['topLevelComment']['snippet']
                    published_at = datetime.fromisoformat(comment['publishedAt'].replace('Z', '+00:00'))
                    
                    # Apply date filter if specified
                    if cutoff_date and published_at < cutoff_date:
                        continue
                    
                    comment_data = {
                        'id': item['snippet']['topLevelComment']['id'],
                        'text': comment['textDisplay'],
                        'author': comment['authorDisplayName'],
                        'likes': comment['likeCount'],
                        'published_at': comment['publishedAt'],
                        'is_reply': False,
                        'reply_count': item['snippet']['totalReplyCount']
                    }
                    
                    self.comments.append(comment_data)
                    comment_count += 1
                    
                    # Collect replies if available
                    if item['snippet']['totalReplyCount'] > 0:
                        # Check if replies are already included
                        if 'replies' in item:
                            for reply in item['replies']['comments']:
                                if comment_count >= max_comments:
                                    break
                                reply_snippet = reply['snippet']
                                self.comments.append({
                                    'id': reply['id'],
                                    'text': reply_snippet['textDisplay'],
                                    'author': reply_snippet['authorDisplayName'],
                                    'likes': reply_snippet['likeCount'],
                                    'published_at': reply_snippet['publishedAt'],
                                    'is_reply': True,
                                    'reply_count': 0
                                })
                                comment_count += 1
                        else:
                            # Fetch replies separately if needed
                            replies = self.get_all_replies(item['snippet']['topLevelComment']['id'])
                            for reply in replies:
                                if comment_count >= max_comments:
                                    break
                                self.comments.append(reply)
                                comment_count += 1
                    
                    # Progress logging
                    if comment_count % 100 == 0:
                        self.log_progress(comment_count, max_comments)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    print(f"\nReached end of available comments. Total collected: {comment_count}")
                    break
                    
                # Rate limiting
                time.sleep(0.1)
                
            except HttpError as e:
                print(f"\nError collecting comments: {e}")
                if e.resp.status == 403:
                    print("API quota exceeded. Saving current progress...")
                break
        
        self.log_progress(comment_count, max_comments, final=True)
        return self.comments
    
    def log_progress(self, current: int, target: int, final: bool = False):
        """Log collection progress."""
        percentage = (current / target) * 100
        bar_length = 50
        filled = int(bar_length * current / target)
        bar = '█' * filled + '-' * (bar_length - filled)
        
        if final:
            print(f"\n✓ Collection complete: {current}/{target} ({percentage:.1f}%)")
        else:
            print(f"\rProgress: |{bar}| {current}/{target} ({percentage:.1f}%)", end='')
    
    def preprocess_text(self, text: str) -> str:
        """
        Advanced text preprocessing for sentiment analysis.
        Keeps emojis (important for sentiment), removes noise.
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs but keep the context
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Remove excessive punctuation (keep single instances)
        text = re.sub(r'([!?.]){2,}', r'\1', text)
        
        # Keep emojis - they're crucial for sentiment analysis
        # Remove only control characters
        text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        
        # Remove @mentions (less relevant for sentiment)
        text = re.sub(r'@\w+', '', text)
        
        # Normalize common abbreviations
        replacements = {
            ' u ': ' you ',
            ' ur ': ' your ',
            ' r ': ' are ',
            ' thx ': ' thanks ',
            ' plz ': ' please ',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def save_all_comments_csv(self, filename: str = "all_comments.csv"):
        """Save raw comments to CSV."""
        filepath = os.path.join(self.output_dir, filename)
        
        df = pd.DataFrame(self.comments)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"✓ Saved {len(self.comments)} comments to {filepath}")
        return filepath
    
    def save_cleaned_comments_csv(self, filename: str = "cleaned_all_comments.csv"):
        """Save preprocessed comments to CSV."""
        filepath = os.path.join(self.output_dir, filename)
        
        df = pd.DataFrame(self.comments)
        df['cleaned_text'] = df['text'].apply(self.preprocess_text)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"✓ Saved cleaned comments to {filepath}")
        return filepath
    
    def save_channel_metadata(self, filename: str = "youtube_analytics.json"):
        """Save channel and video metadata."""
        filepath = os.path.join(self.output_dir, filename)
        
        metadata = {
            **self.channel_info,
            'total_comments_collected': len(self.comments),
            'collection_stats': {
                'top_level_comments': sum(1 for c in self.comments if not c['is_reply']),
                'replies': sum(1 for c in self.comments if c['is_reply']),
                'total_likes': sum(c['likes'] for c in self.comments)
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved metadata to {filepath}")
        return filepath
    
    def create_batches(self, batch_size: int = 100, 
                       output_dir: str = "data/batches") -> List[str]:
        """
        Segment comments into batches for LLM processing.
        Returns list of batch file paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        batch_files = []
        
        # Use cleaned text
        texts = [self.preprocess_text(c['text']) for c in self.comments]
        
        for i in range(0, len(texts), batch_size):
            batch_num = i // batch_size + 1
            batch = texts[i:i + batch_size]
            
            filename = f"comments_batch_{batch_num}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for idx, comment in enumerate(batch, 1):
                    f.write(f"{idx}. {comment}\n")
            
            batch_files.append(filepath)
        
        print(f"✓ Created {len(batch_files)} batches in {output_dir}")
        return batch_files


def main():
    """Example usage of the YouTubeCommentExtractor."""
    api_key = 'AIzaSyA-PBiOG1Xj3kn1ZnKQxyiLzcmmUnl2u-c'
    video_id = 'mME51l0K9yA'
    
    extractor = YouTubeCommentExtractor(api_key, output_dir='data/outputs')
    
    # Collect comments
    comments = extractor.collect_comments_until_5000(video_id, max_comments=5000)
    
    # Save outputs
    extractor.save_all_comments_csv()
    extractor.save_cleaned_comments_csv()
    extractor.save_channel_metadata()
    
    # Create batches for LLM processing
    batch_files = extractor.create_batches(batch_size=100, output_dir='data/batches')
    
    print(f"\n{'='*60}")
    print(f"Extraction Complete!")
    print(f"{'='*60}")
    print(f"Total comments: {len(comments)}")
    print(f"Batches created: {len(batch_files)}")
    print(f"Output directory: data/outputs")


if __name__ == "__main__":
    main()
