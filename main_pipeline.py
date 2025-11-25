"""
CreatorGPT: YouTube Comment Sentiment Intelligence
Main orchestrator script that runs the complete pipeline
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from backend.youtube_improved import YouTubeCommentExtractor
from backend.batch_processor import BatchProcessor
from backend.sentiment_analyzer import SentimentAnalyzer
from backend.data_utilities import aggregate_analytics, generate_summary_report


class CreatorGPT:
    """Main orchestrator for YouTube comment analysis pipeline."""
    
    def __init__(self, youtube_api_key: str, gemini_api_key: str):
        self.youtube_api_key = youtube_api_key
        self.gemini_api_key = gemini_api_key
        self.output_dir = Path('data/outputs')
        self.batch_dir = Path('data/batches')
        self.viz_dir = Path('data/visualizations')
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.batch_dir.mkdir(parents=True, exist_ok=True)
        self.viz_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {}
    
    def run_complete_analysis(self, video_id: str, max_comments: int = 5000, 
                             batch_size: int = 100):
        """
        Run complete analysis pipeline.
        
        Args:
            video_id: YouTube video ID
            max_comments: Maximum comments to collect
            batch_size: Comments per batch for LLM processing
        """
        print("\n" + "="*80)
        print("CreatorGPT: YouTube Comment Sentiment Intelligence")
        print("="*80)
        print(f"\nVideo ID: {video_id}")
        print(f"Target Comments: {max_comments}")
        print(f"Batch Size: {batch_size}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "="*80 + "\n")
        
        try:
            # Step 1: Extract YouTube Comments
            print("STEP 1: EXTRACTING YOUTUBE COMMENTS")
            print("-" * 80)
            
            extractor = YouTubeCommentExtractor(
                self.youtube_api_key,
                output_dir=str(self.output_dir)
            )
            
            comments = extractor.collect_comments_until_5000(
                video_id,
                max_comments=max_comments
            )
            
            if not comments:
                print("❌ No comments collected. Exiting.")
                return None
            
            # Save extracted comments
            extractor.save_all_comments_csv()
            extractor.save_cleaned_comments_csv()
            metadata_file = extractor.save_channel_metadata()
            
            print(f"\n✓ Extracted {len(comments)} comments\n")
            
            # Step 2: Create Batches
            print("\nSTEP 2: CREATING COMMENT BATCHES")
            print("-" * 80)
            
            batch_files = extractor.create_batches(
                batch_size=batch_size,
                output_dir=str(self.batch_dir)
            )
            
            print(f"\n✓ Created {len(batch_files)} batches\n")
            
            # Step 3: LLM Batch Processing
            print("\nSTEP 3: LLM BATCH ANALYSIS")
            print("-" * 80)
            
            processor = BatchProcessor(
                self.gemini_api_key,
                output_dir=str(self.output_dir)
            )
            
            batch_results = processor.process_all_batches(str(self.batch_dir))
            
            # Consolidate analyses
            comprehensive_file = processor.consolidate_all_analyses()
            
            print(f"\n✓ Processed {len(batch_results)} batches\n")
            
            # Step 4: Sentiment Analysis
            print("\nSTEP 4: SENTIMENT ANALYSIS")
            print("-" * 80)
            
            analyzer = SentimentAnalyzer(output_dir=str(self.output_dir))
            
            df = analyzer.analyze_sentiment(
                str(self.output_dir / 'cleaned_all_comments.csv')
            )
            
            # Save results
            analyzer.save_analyzed_comments()
            report_file = analyzer.generate_detailed_report()
            
            print(f"\n✓ Analyzed sentiment for {len(df)} comments\n")
            
            # Step 5: Generate Visualizations
            print("\nSTEP 5: GENERATING VISUALIZATIONS")
            print("-" * 80)
            
            viz_files = analyzer.generate_visualizations()
            
            print(f"\n✓ Generated {len(viz_files)} visualizations\n")
            
            # Step 6: Aggregate Analytics
            print("\nSTEP 6: AGGREGATING ANALYTICS")
            print("-" * 80)
            
            analytics = aggregate_analytics(str(self.output_dir))
            
            # Save analytics
            analytics_file = self.output_dir / 'complete_analytics.json'
            with open(analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✓ Saved analytics to {analytics_file}")
            
            # Generate summary report
            summary_file = generate_summary_report(
                analytics,
                str(self.output_dir / 'summary_report.txt')
            )
            
            # Compile results
            self.results = {
                'video_id': video_id,
                'total_comments': len(comments),
                'batches_processed': len(batch_results),
                'sentiment_summary': {
                    'positive': int(df[df['sentiment_label'] == 'Positive'].shape[0]),
                    'neutral': int(df[df['sentiment_label'] == 'Neutral'].shape[0]),
                    'negative': int(df[df['sentiment_label'] == 'Negative'].shape[0]),
                    'avg_score': float(df['confidence_score'].mean())
                },
                'files': {
                    'all_comments': str(self.output_dir / 'all_comments.csv'),
                    'cleaned_comments': str(self.output_dir / 'cleaned_all_comments.csv'),
                    'analyzed_comments': str(self.output_dir / 'sentiment_analyzed_comments.csv'),
                    'detailed_report': report_file,
                    'comprehensive_analysis': comprehensive_file,
                    'summary_report': summary_file,
                    'analytics': str(analytics_file),
                    'visualizations': [str(f) for f in viz_files]
                },
                'completed_at': datetime.now().isoformat()
            }
            
            # Print final summary
            self.print_summary()
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ Error in pipeline: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def print_summary(self):
        """Print final analysis summary."""
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\n📊 Results Summary:")
        print(f"   Total Comments Analyzed: {self.results['total_comments']:,}")
        print(f"   Batches Processed: {self.results['batches_processed']}")
        print(f"\n😊 Sentiment Distribution:")
        sent = self.results['sentiment_summary']
        print(f"   Positive: {sent['positive']:,} ({sent['positive']/self.results['total_comments']*100:.1f}%)")
        print(f"   Neutral:  {sent['neutral']:,} ({sent['neutral']/self.results['total_comments']*100:.1f}%)")
        print(f"   Negative: {sent['negative']:,} ({sent['negative']/self.results['total_comments']*100:.1f}%)")
        print(f"   Average Score: {sent['avg_score']:.2f}/100")
        print(f"\n📁 Output Files:")
        for key, value in self.results['files'].items():
            if isinstance(value, list):
                print(f"   {key}:")
                for item in value:
                    print(f"      - {item}")
            else:
                print(f"   {key}: {value}")
        print(f"\n✅ Completed at: {self.results['completed_at']}")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    
    # Configuration - Replace with your API keys
    YOUTUBE_API_KEY = 'AIzaSyA-PBiOG1Xj3kn1ZnKQxyiLzcmmUnl2u-c'
    GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY'  # Replace with your Gemini API key
    
    # Video to analyze
    VIDEO_ID = 'mME51l0K9yA'  # Replace with your video ID
    
    # Initialize CreatorGPT
    creator_gpt = CreatorGPT(YOUTUBE_API_KEY, GEMINI_API_KEY)
    
    # Run complete analysis
    results = creator_gpt.run_complete_analysis(
        video_id=VIDEO_ID,
        max_comments=5000,
        batch_size=100
    )
    
    if results:
        print("\n🎉 Analysis pipeline completed successfully!")
        print("You can now:")
        print("  1. View visualizations in: data/visualizations/")
        print("  2. Read detailed reports in: data/outputs/")
        print("  3. Start the API server: cd backend && python api.py")
        print("  4. Start the frontend: cd frontend && npm run dev")
    else:
        print("\n❌ Analysis pipeline failed. Check the logs above.")


if __name__ == "__main__":
    main()
