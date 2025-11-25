"""
Simple Example: Basic Usage of CreatorGPT
Demonstrates how to use individual components
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from backend.youtube_improved import YouTubeCommentExtractor
from backend.sentiment_analyzer import SentimentAnalyzer


def example_1_extract_comments():
    """Example 1: Extract and save YouTube comments"""
    print("\n" + "="*60)
    print("Example 1: Extract YouTube Comments")
    print("="*60 + "\n")
    
    # Your API key (replace with actual key)
    api_key = 'YOUR_YOUTUBE_API_KEY'
    video_id = 'mME51l0K9yA'
    
    # Initialize extractor
    extractor = YouTubeCommentExtractor(api_key, output_dir='data/outputs')
    
    # Collect comments
    comments = extractor.collect_comments_until_5000(
        video_id,
        max_comments=100  # Small number for testing
    )
    
    print(f"\n✓ Collected {len(comments)} comments")
    
    # Save outputs
    extractor.save_all_comments_csv()
    extractor.save_cleaned_comments_csv()
    
    # Show sample comments
    print("\nSample comments:")
    for i, comment in enumerate(comments[:3], 1):
        print(f"{i}. {comment['text'][:100]}...")


def example_2_analyze_sentiment():
    """Example 2: Analyze sentiment of existing comments"""
    print("\n" + "="*60)
    print("Example 2: Analyze Sentiment")
    print("="*60 + "\n")
    
    # Make sure you have comments CSV from Example 1
    csv_file = 'data/outputs/cleaned_all_comments.csv'
    
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        print("Please run Example 1 first to extract comments")
        return
    
    # Initialize analyzer
    analyzer = SentimentAnalyzer(output_dir='data/outputs')
    
    # Analyze sentiment
    df = analyzer.analyze_sentiment(csv_file)
    
    # Show results
    print("\nSentiment Distribution:")
    print(df['sentiment_label'].value_counts())
    
    print(f"\nAverage Confidence Score: {df['confidence_score'].mean():.2f}/100")
    
    # Save results
    analyzer.save_analyzed_comments()
    analyzer.generate_detailed_report()
    
    print("\n✓ Results saved!")


def example_3_generate_visualizations():
    """Example 3: Generate visualizations from analyzed data"""
    print("\n" + "="*60)
    print("Example 3: Generate Visualizations")
    print("="*60 + "\n")
    
    # Make sure you have analyzed comments from Example 2
    csv_file = 'data/outputs/sentiment_analyzed_comments.csv'
    
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        print("Please run Example 2 first to analyze sentiment")
        return
    
    # Initialize analyzer with existing data
    analyzer = SentimentAnalyzer(output_dir='data/outputs')
    
    # Load analyzed data
    import pandas as pd
    analyzer.results = pd.read_csv(csv_file)
    
    # Generate visualizations
    viz_files = analyzer.generate_visualizations()
    
    print(f"\n✓ Generated {len(viz_files)} visualizations")
    print("\nVisualization files:")
    for viz_file in viz_files:
        print(f"  - {viz_file}")


def example_4_custom_analysis():
    """Example 4: Custom sentiment analysis with filtering"""
    print("\n" + "="*60)
    print("Example 4: Custom Analysis")
    print("="*60 + "\n")
    
    import pandas as pd
    
    csv_file = 'data/outputs/sentiment_analyzed_comments.csv'
    
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        return
    
    df = pd.read_csv(csv_file)
    
    # Filter high-confidence positive comments
    high_positive = df[
        (df['sentiment_label'] == 'Positive') & 
        (df['confidence_score'] > 80)
    ]
    
    print(f"High-confidence positive comments: {len(high_positive)}")
    print("\nTop 3 most positive comments:")
    for idx, row in high_positive.nlargest(3, 'confidence_score').iterrows():
        print(f"\nScore: {row['confidence_score']}/100")
        text_col = 'cleaned_text' if 'cleaned_text' in df.columns else 'text'
        print(f"Comment: {row[text_col][:150]}...")
    
    # Filter high-engagement comments
    if 'likes' in df.columns:
        high_engagement = df[df['likes'] > df['likes'].quantile(0.9)]
        print(f"\n\nHigh-engagement comments (top 10%): {len(high_engagement)}")
        print(f"Their sentiment distribution:")
        print(high_engagement['sentiment_label'].value_counts())
        print(f"Average sentiment score: {high_engagement['confidence_score'].mean():.2f}")


def main():
    """Main function to run examples"""
    print("\n" + "="*80)
    print("CreatorGPT - Usage Examples")
    print("="*80)
    
    print("\nWhich example would you like to run?")
    print("1. Extract YouTube comments")
    print("2. Analyze sentiment")
    print("3. Generate visualizations")
    print("4. Custom analysis (filtering & statistics)")
    print("5. Run all examples in sequence")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-5): ").strip()
    
    if choice == "1":
        example_1_extract_comments()
    elif choice == "2":
        example_2_analyze_sentiment()
    elif choice == "3":
        example_3_generate_visualizations()
    elif choice == "4":
        example_4_custom_analysis()
    elif choice == "5":
        print("\nRunning all examples...\n")
        example_1_extract_comments()
        example_2_analyze_sentiment()
        example_3_generate_visualizations()
        example_4_custom_analysis()
    elif choice == "0":
        print("\nGoodbye!")
        return
    else:
        print("\n❌ Invalid choice!")
        return
    
    print("\n" + "="*80)
    print("Example complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
