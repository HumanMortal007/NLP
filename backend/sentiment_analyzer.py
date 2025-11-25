import os
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from transformers import pipeline
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json


class SentimentAnalyzer:
    """
    Advanced sentiment analysis using transformer models.
    Provides confidence scoring, visualization, and detailed reporting.
    """
    
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest",
                 output_dir: str = "data/outputs"):
        """
        Initialize sentiment analyzer with transformer model.
        Uses RoBERTa-based model (better than DistilBERT) trained on 124M tweets.
        Supports multilingual sentiment with 3 classes: negative, neutral, positive.
        
        Args:
            model_name: HuggingFace model for sentiment analysis
            output_dir: Directory for outputs
        """
        self.output_dir = output_dir
        self.viz_dir = os.path.join(output_dir, "../visualizations")
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.viz_dir, exist_ok=True)
        
        print("Loading advanced sentiment analysis model (RoBERTa)...")
        print("Model: cardiffnlp/twitter-roberta-base-sentiment-latest")
        print("Trained on 124M tweets - Multilingual support ✓")
        
        # Initialize the transformer pipeline. return_all_scores=True provides
        # per-label probabilities which we use to compute robust confidence scores.
        # We prefer batch processing (see analyze_sentiment) for reliability.
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            return_all_scores=True
        )
        print(f"✓ Model loaded successfully!")
        
        self.results = []
    
    def _convert_to_score(self, label: str, confidence: float) -> int:
        """
        Convert label probabilities to 0-100 confidence scores.
        
        Returns:
            int: Score from 0 (very negative) to 100 (very positive)
        """
        if label == "POSITIVE":
            # Positive: 50-100 based on confidence
            return int(50 + (confidence * 50))
        else:  # NEGATIVE
            # Negative: 0-50 based on confidence
            return int(50 - (confidence * 50))
    
    def _categorize_sentiment(self, score: int) -> str:
        """Categorize sentiment based on score."""
        if score >= 60:
            return "Positive"
        elif score >= 40:
            return "Neutral"
        else:
            return "Negative"
    
    def analyze_comment(self, text: str) -> Dict:
        """
        Analyze sentiment of a single comment using RoBERTa.
        RoBERTa labels: LABEL_0 (negative), LABEL_1 (neutral), LABEL_2 (positive)
        
        Returns:
            Dict with sentiment label, confidence score, and probabilities
        """
        # Single-comment analysis kept for backward compatibility. The
        # analyze_sentiment method uses batch processing which is preferred.
        try:
            clean_text = self._clean_text(text)
            if len(clean_text) > 512:
                clean_text = clean_text[:512]

            # Pipeline returns a list of label/score dicts (because return_all_scores=True)
            raw = self.sentiment_pipeline(clean_text)[0]

            # Normalize keys: model may return LABEL_0/1/2 or NEGATIVE/NEUTRAL/POSITIVE
            label_map = {item['label'].upper(): item['score'] for item in raw}

            # Resolve probabilities with robust fallback
            neg_score = label_map.get('LABEL_0', label_map.get('NEGATIVE', 0.0))
            neu_score = label_map.get('LABEL_1', label_map.get('NEUTRAL', 0.0))
            pos_score = label_map.get('LABEL_2', label_map.get('POSITIVE', 0.0))

            # If none detected, try to infer from available keys
            if all(v == 0.0 for v in (neg_score, neu_score, pos_score)):
                # take top label
                sorted_items = sorted(label_map.items(), key=lambda x: x[1], reverse=True)
                if sorted_items:
                    top_label, top_score = sorted_items[0]
                    if 'POS' in top_label:
                        pos_score = top_score
                    elif 'NEU' in top_label:
                        neu_score = top_score
                    else:
                        neg_score = top_score

            # Compute primary label and a 0-100 confidence score
            probs = {'neg': neg_score, 'neu': neu_score, 'pos': pos_score}
            primary = max(probs, key=probs.get)
            primary_conf = probs[primary]

            if primary == 'pos':
                score = 50 + (pos_score * 50)
            elif primary == 'neg':
                score = 50 - (neg_score * 50)
            else:
                score = 50

            category = self._categorize_sentiment(int(score))

            return {
                'sentiment_label': category,
                'confidence_score': round(float(score), 2),
                'positive_prob': round(float(pos_score), 4),
                'neutral_prob': round(float(neu_score), 4),
                'negative_prob': round(float(neg_score), 4),
                'primary_confidence': round(float(primary_conf), 4)
            }

        except Exception as e:
            # Return safe neutral fallback
            print(f"Error analyzing comment: {e}")
            return {
                'sentiment_label': 'Neutral',
                'confidence_score': 50.0,
                'positive_prob': 0.33,
                'neutral_prob': 0.34,
                'negative_prob': 0.33,
                'primary_confidence': 0.34
            }

    def _clean_text(self, text: str) -> str:
        """Lightweight text cleaning to improve transformer robustness.

        - Remove URLs
        - Strip excessive whitespace
        - Remove simple user mentions
        """
        try:
            import re
            t = str(text)
            t = re.sub(r'http\S+|www\.\S+', ' ', t)
            t = re.sub(r'@\w+', ' ', t)
            t = re.sub(r'\s+', ' ', t).strip()
            return t
        except Exception:
            return str(text)
    
    def analyze_sentiment(self, input_csv: str, 
                         text_column: str = 'cleaned_text',
                         batch_size: int = 32) -> pd.DataFrame:
        """
        Analyze sentiment for all comments in a CSV file.
        
        Args:
            input_csv: Path to input CSV with comments
            text_column: Column name containing comment text
            batch_size: Number of comments to process at once
            
        Returns:
            DataFrame with sentiment analysis results
        """
        print(f"\nLoading comments from {input_csv}...")
        df = pd.read_csv(input_csv)
        
        if text_column not in df.columns:
            print(f"Column '{text_column}' not found. Using 'text' column.")
            text_column = 'text'
        
        total = len(df)
        print(f"Analyzing sentiment for {total} comments...")
        
        # Batch processing for better throughput and stability
        texts = df[text_column].astype(str).tolist()
        results = []
        from math import ceil
        n_batches = ceil(len(texts) / batch_size) if batch_size > 0 else 1

        for b in range(n_batches):
            start = b * batch_size
            end = start + batch_size
            batch_texts = [self._clean_text(t)[:512] for t in texts[start:end]]

            try:
                raw_predictions = self.sentiment_pipeline(batch_texts)
            except Exception:
                # Fallback to per-item analysis if batch call fails
                raw_predictions = [self.sentiment_pipeline(t)[0] for t in batch_texts]

            for raw in raw_predictions:
                # raw may be list of dicts
                if isinstance(raw, list):
                    label_map = {item['label'].upper(): item['score'] for item in raw}
                elif isinstance(raw, dict):
                    label_map = {raw.get('label', '').upper(): raw.get('score', 0.0)}
                else:
                    label_map = {}

                neg_score = label_map.get('LABEL_0', label_map.get('NEGATIVE', 0.0))
                neu_score = label_map.get('LABEL_1', label_map.get('NEUTRAL', 0.0))
                pos_score = label_map.get('LABEL_2', label_map.get('POSITIVE', 0.0))

                # Fallback inference
                if all(v == 0.0 for v in (neg_score, neu_score, pos_score)):
                    sorted_items = sorted(label_map.items(), key=lambda x: x[1], reverse=True)
                    if sorted_items:
                        top_label, top_score = sorted_items[0]
                        if 'POS' in top_label:
                            pos_score = top_score
                        elif 'NEU' in top_label:
                            neu_score = top_score
                        else:
                            neg_score = top_score

                probs = {'neg': neg_score, 'neu': neu_score, 'pos': pos_score}
                primary = max(probs, key=probs.get)
                primary_conf = probs[primary]

                if primary == 'pos':
                    score = 50 + (pos_score * 50)
                elif primary == 'neg':
                    score = 50 - (neg_score * 50)
                else:
                    score = 50

                category = self._categorize_sentiment(int(score))

                results.append({
                    'sentiment_label': category,
                    'confidence_score': round(float(score), 2),
                    'positive_prob': round(float(pos_score), 4),
                    'neutral_prob': round(float(neu_score), 4),
                    'negative_prob': round(float(neg_score), 4),
                    'primary_confidence': round(float(primary_conf), 4)
                })

            # Progress
            processed = min(end, total)
            percentage = (processed / total) * 100
            print(f"Progress: {processed}/{total} ({percentage:.1f}%)")
        
        # Add results to dataframe
        for key in results[0].keys():
            df[key] = [r[key] for r in results]
        
        self.results = df
        print(f"✓ Sentiment analysis complete!")
        
        return df
    
    def save_analyzed_comments(self, filename: str = "sentiment_analyzed_comments.csv") -> str:
        """Save analyzed comments to CSV."""
        if self.results is None or len(self.results) == 0:
            print("No results to save. Run analyze_sentiment first.")
            return None
        
        filepath = os.path.join(self.output_dir, filename)
        self.results.to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"✓ Saved analyzed comments to {filepath}")
        return filepath
    
    def generate_detailed_report(self, filename: str = "detailed_sentiment_results.txt") -> str:
        """Generate comprehensive text report of sentiment analysis."""
        if self.results is None or len(self.results) == 0:
            print("No results to report. Run analyze_sentiment first.")
            return None
        
        filepath = os.path.join(self.output_dir, filename)
        
        df = self.results
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("DETAILED SENTIMENT ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Comments Analyzed: {len(df)}\n\n")
            
            # Overall statistics
            f.write("-" * 80 + "\n")
            f.write("OVERALL SENTIMENT DISTRIBUTION\n")
            f.write("-" * 80 + "\n")
            
            sentiment_counts = df['sentiment_label'].value_counts()
            for sentiment, count in sentiment_counts.items():
                percentage = (count / len(df)) * 100
                f.write(f"{sentiment}: {count} ({percentage:.2f}%)\n")
            
            f.write(f"\nAverage Confidence Score: {df['confidence_score'].mean():.2f}/100\n")
            f.write(f"Median Confidence Score: {df['confidence_score'].median():.2f}/100\n")
            
            # Score distribution
            f.write("\n" + "-" * 80 + "\n")
            f.write("CONFIDENCE SCORE RANGES\n")
            f.write("-" * 80 + "\n")
            
            bins = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
            for low, high in bins:
                count = len(df[(df['confidence_score'] >= low) & (df['confidence_score'] < high)])
                percentage = (count / len(df)) * 100
                label = "Very Negative" if low == 0 else "Negative" if low == 20 else "Neutral" if low == 40 else "Positive" if low == 60 else "Very Positive"
                f.write(f"{low}-{high} ({label}): {count} ({percentage:.2f}%)\n")
            
            # Top positive comments
            f.write("\n" + "-" * 80 + "\n")
            f.write("TOP 10 MOST POSITIVE COMMENTS\n")
            f.write("-" * 80 + "\n\n")
            
            top_positive = df.nlargest(10, 'confidence_score')
            for idx, row in top_positive.iterrows():
                text_col = 'cleaned_text' if 'cleaned_text' in df.columns else 'text'
                f.write(f"Score: {row['confidence_score']}/100\n")
                f.write(f"Comment: {row[text_col][:200]}...\n")
                f.write(f"Author: {row.get('author', 'Unknown')}\n")
                f.write(f"Likes: {row.get('likes', 0)}\n\n")
            
            # Top negative comments
            f.write("-" * 80 + "\n")
            f.write("TOP 10 MOST NEGATIVE COMMENTS\n")
            f.write("-" * 80 + "\n\n")
            
            top_negative = df.nsmallest(10, 'confidence_score')
            for idx, row in top_negative.iterrows():
                text_col = 'cleaned_text' if 'cleaned_text' in df.columns else 'text'
                f.write(f"Score: {row['confidence_score']}/100\n")
                f.write(f"Comment: {row[text_col][:200]}...\n")
                f.write(f"Author: {row.get('author', 'Unknown')}\n")
                f.write(f"Likes: {row.get('likes', 0)}\n\n")
            
            # Time-based analysis if timestamp available
            if 'published_at' in df.columns:
                f.write("-" * 80 + "\n")
                f.write("TEMPORAL SENTIMENT TRENDS\n")
                f.write("-" * 80 + "\n\n")
                
                df_temp = df.copy()
                df_temp['published_at'] = pd.to_datetime(df_temp['published_at'])
                df_temp['date'] = df_temp['published_at'].dt.date
                
                daily_sentiment = df_temp.groupby('date')['confidence_score'].agg(['mean', 'count'])
                
                f.write("Daily Average Sentiment:\n")
                for date, row in daily_sentiment.iterrows():
                    f.write(f"{date}: {row['mean']:.2f} (n={row['count']})\n")
        
        print(f"✓ Detailed report saved to {filepath}")
        return filepath
    
    def generate_visualizations(self, minimal: bool = True) -> List[str]:
        """
        Generate comprehensive visualizations:
        - Pie chart of sentiment distribution
        - Trendline of sentiment over time
        - Heatmap of sentiment by day/hour
        - Score distribution histogram
        """
        if self.results is None or len(self.results) == 0:
            print("No results to visualize. Run analyze_sentiment first.")
            return []
        
        df = self.results
        filepaths = []
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        
        # 1. Sentiment Distribution Pie Chart
        print("Generating pie chart...")
        plt.figure(figsize=(10, 8))
        sentiment_counts = df['sentiment_label'].value_counts()
        colors = {'Positive': '#4CAF50', 'Neutral': '#FFC107', 'Negative': '#F44336'}
        pie_colors = [colors.get(label, '#999') for label in sentiment_counts.index]
        
        plt.pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%',
                colors=pie_colors, startangle=90, textprops={'fontsize': 14, 'weight': 'bold'})
        plt.title('Sentiment Distribution', fontsize=18, weight='bold', pad=20)
        
        filepath = os.path.join(self.viz_dir, 'sentiment_pie_chart.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        filepaths.append(filepath)
        print(f"  ✓ Saved: {filepath}")
        
        # 2. Confidence Score Distribution
        print("Generating score distribution...")
        plt.figure(figsize=(12, 6))
        plt.hist(df['confidence_score'], bins=50, color='#2196F3', edgecolor='black', alpha=0.7)
        plt.xlabel('Confidence Score', fontsize=14, weight='bold')
        plt.ylabel('Frequency', fontsize=14, weight='bold')
        plt.title('Distribution of Sentiment Confidence Scores', fontsize=16, weight='bold', pad=20)
        plt.axvline(df['confidence_score'].mean(), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {df["confidence_score"].mean():.1f}')
        plt.legend(fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        
        filepath = os.path.join(self.viz_dir, 'score_distribution.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        filepaths.append(filepath)
        print(f"  ✓ Saved: {filepath}")
        
        # 3. Sentiment Trend Over Time (if timestamp available and not in minimal mode)
        if (not minimal) and ('published_at' in df.columns) and len(df) > 30:
            print("Generating sentiment trendline...")
            df_temp = df.copy()
            df_temp['published_at'] = pd.to_datetime(df_temp['published_at'])
            df_temp = df_temp.sort_values('published_at')

            # Daily aggregation
            df_temp['date'] = df_temp['published_at'].dt.date
            daily_sentiment = df_temp.groupby('date').agg({
                'confidence_score': 'mean',
                'sentiment_label': 'count'
            }).reset_index()

            fig, ax1 = plt.subplots(figsize=(14, 6))

            ax1.plot(daily_sentiment['date'], daily_sentiment['confidence_score'], 
                    color='#2196F3', linewidth=2, marker='o', markersize=6)
            ax1.set_xlabel('Date', fontsize=14, weight='bold')
            ax1.set_ylabel('Average Sentiment Score', fontsize=14, weight='bold', color='#2196F3')
            ax1.tick_params(axis='y', labelcolor='#2196F3')
            ax1.grid(True, alpha=0.3)

            ax2 = ax1.twinx()
            ax2.bar(daily_sentiment['date'], daily_sentiment['sentiment_label'], 
                   alpha=0.3, color='#FFC107')
            ax2.set_ylabel('Number of Comments', fontsize=14, weight='bold', color='#FFC107')
            ax2.tick_params(axis='y', labelcolor='#FFC107')

            plt.title('Sentiment Trend Over Time', fontsize=16, weight='bold', pad=20)
            plt.xticks(rotation=45)

            filepath = os.path.join(self.viz_dir, 'sentiment_trendline.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            filepaths.append(filepath)
            print(f"  ✓ Saved: {filepath}")

            # 4. Heatmap (Day of Week vs Hour) - only create when not minimal and sufficient data
            if len(df_temp) > 100:
                print("Generating sentiment heatmap...")
                df_temp['day_of_week'] = df_temp['published_at'].dt.day_name()
                df_temp['hour'] = df_temp['published_at'].dt.hour

                # Create pivot table
                heatmap_data = df_temp.pivot_table(
                    values='confidence_score',
                    index='day_of_week',
                    columns='hour',
                    aggfunc='mean'
                )

                # Reorder days
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                heatmap_data = heatmap_data.reindex([d for d in day_order if d in heatmap_data.index])

                plt.figure(figsize=(16, 8))
                sns.heatmap(heatmap_data, cmap='RdYlGn', annot=False, fmt='.1f',
                           cbar_kws={'label': 'Average Sentiment Score'}, linewidths=0.5)
                plt.title('Sentiment Heatmap by Day and Hour', fontsize=16, weight='bold', pad=20)
                plt.xlabel('Hour of Day', fontsize=14, weight='bold')
                plt.ylabel('Day of Week', fontsize=14, weight='bold')

                filepath = os.path.join(self.viz_dir, 'sentiment_heatmap.png')
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                plt.close()
                filepaths.append(filepath)
                print(f"  ✓ Saved: {filepath}")
        
        # 5. Sentiment by Engagement (likes)
        if 'likes' in df.columns:
            print("Generating engagement analysis...")
            plt.figure(figsize=(12, 6))
            
            # Filter out extreme outliers for better visualization
            q99 = df['likes'].quantile(0.99)
            df_filtered = df[df['likes'] <= q99]
            
            for sentiment in df_filtered['sentiment_label'].unique():
                data = df_filtered[df_filtered['sentiment_label'] == sentiment]
                plt.scatter(data['likes'], data['confidence_score'], 
                          label=sentiment, alpha=0.5, s=50,
                          color=colors.get(sentiment, '#999'))
            
            plt.xlabel('Number of Likes', fontsize=14, weight='bold')
            plt.ylabel('Sentiment Score', fontsize=14, weight='bold')
            plt.title('Sentiment vs. Engagement (Likes)', fontsize=16, weight='bold', pad=20)
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3)
            
            filepath = os.path.join(self.viz_dir, 'sentiment_vs_engagement.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            filepaths.append(filepath)
            print(f"  ✓ Saved: {filepath}")
        
        print(f"\n✓ Generated {len(filepaths)} visualizations in {self.viz_dir}")
        return filepaths


def main():
    """Example usage of SentimentAnalyzer."""
    analyzer = SentimentAnalyzer(output_dir='data/outputs')
    
    # Analyze comments
    df = analyzer.analyze_sentiment('data/outputs/cleaned_all_comments.csv')
    
    # Save results
    analyzer.save_analyzed_comments()
    analyzer.generate_detailed_report()
    
    # Generate visualizations
    viz_files = analyzer.generate_visualizations()
    
    print(f"\n{'='*60}")
    print(f"Sentiment Analysis Complete!")
    print(f"{'='*60}")
    print(f"Visualizations: {len(viz_files)}")
    print(f"Output directory: data/outputs")


if __name__ == "__main__":
    main()
