import os
import json
import time
from typing import List, Dict, Optional
import google.generativeai as genai
from pathlib import Path


class BatchProcessor:
    """
    Processes comment batches using Google Gemini API for 
    theme extraction, sentiment analysis, and summarization.
    """
    
    def __init__(self, api_key: str, output_dir: str = "data/outputs"):
        self.api_key = api_key
        self.output_dir = output_dir
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.batch_status = {}
        
        os.makedirs(output_dir, exist_ok=True)
    
    def enhanced_prompt(self, comments_text: str) -> str:
        """
        Generate structured prompt for comprehensive batch analysis.
        """
        prompt = f"""You are an expert YouTube comment analyst. Analyze the following batch of comments and provide a comprehensive, structured analysis.

COMMENTS TO ANALYZE:
{comments_text}

Please provide a detailed analysis in the following structure:

1. OVERALL SENTIMENT DISTRIBUTION
   - Positive comments: [percentage]%
   - Neutral comments: [percentage]%
   - Negative comments: [percentage]%
   - Brief explanation of sentiment patterns

2. KEY THEMES (Top 5)
   List the main topics/themes discussed, ranked by frequency:
   - Theme 1: [description] (mentioned in X% of comments)
   - Theme 2: [description]
   - Theme 3: [description]
   - Theme 4: [description]
   - Theme 5: [description]

3. VIEWER SUGGESTIONS & FEEDBACK (Top 5)
   Actionable suggestions or requests from viewers:
   - Suggestion 1: [detailed description]
   - Suggestion 2: [detailed description]
   - Suggestion 3: [detailed description]
   - Suggestion 4: [detailed description]
   - Suggestion 5: [detailed description]

4. APPRECIATION & PRAISE
   What viewers specifically appreciated:
   - [List specific elements viewers praised]

5. CONCERNS & CRITICISM
   Main concerns or criticisms raised:
   - [List specific concerns]

6. TOP COMMENTS (5 most impactful)
   Quote the most insightful, representative, or highly-engaged comments:
   1. "[exact quote]" - [why it's significant]
   2. "[exact quote]" - [why it's significant]
   3. "[exact quote]" - [why it's significant]
   4. "[exact quote]" - [why it's significant]
   5. "[exact quote]" - [why it's significant]

7. ENGAGEMENT PATTERNS
   - Question count: [number]
   - Call-to-action responses: [number]
   - Community building interactions: [number]

8. CONTENT STRATEGY RECOMMENDATIONS
   Based on this analysis, provide 3-5 actionable recommendations:
   - Recommendation 1: [specific action]
   - Recommendation 2: [specific action]
   - Recommendation 3: [specific action]

Please be thorough, specific, and use data-driven insights."""

        return prompt
    
    def process_batch(self, batch_file: str, batch_num: int) -> Dict:
        """
        Process a single batch file with Gemini API.
        Includes retry logic and error handling.
        """
        print(f"\n{'='*60}")
        print(f"Processing Batch {batch_num}")
        print(f"{'='*60}")
        
        # Read batch file
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                comments_text = f.read()
        except FileNotFoundError:
            error_msg = f"Batch file not found: {batch_file}"
            print(f"❌ {error_msg}")
            self.batch_status[batch_num] = {'status': 'failed', 'error': error_msg}
            return None
        
        # Generate prompt
        prompt = self.enhanced_prompt(comments_text)
        
        # Call Gemini API with retry logic
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                print(f"Sending request to Gemini API (attempt {attempt + 1}/{max_retries})...")
                
                response = self.model.generate_content(prompt)
                analysis = response.text
                
                # Save analysis
                output_file = os.path.join(
                    self.output_dir, 
                    f"analyzed_comments_batch_{batch_num}.txt"
                )
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"BATCH {batch_num} ANALYSIS\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(analysis)
                
                # Update status
                self.batch_status[batch_num] = {
                    'status': 'completed',
                    'output_file': output_file,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                print(f"✓ Batch {batch_num} processed successfully")
                print(f"  Output: {output_file}")
                
                return {
                    'batch_num': batch_num,
                    'analysis': analysis,
                    'output_file': output_file
                }
                
            except Exception as e:
                error_msg = f"Error processing batch {batch_num}: {str(e)}"
                print(f"❌ {error_msg}")
                
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.batch_status[batch_num] = {
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return None
        
        return None
    
    def process_all_batches(self, batch_dir: str = "data/batches") -> List[Dict]:
        """
        Process all batch files in the specified directory.
        """
        batch_files = sorted(Path(batch_dir).glob("comments_batch_*.txt"))
        
        if not batch_files:
            print(f"No batch files found in {batch_dir}")
            return []
        
        print(f"\nFound {len(batch_files)} batches to process")
        results = []
        
        for idx, batch_file in enumerate(batch_files, 1):
            result = self.process_batch(str(batch_file), idx)
            if result:
                results.append(result)
            
            # Rate limiting - be respectful to API
            if idx < len(batch_files):
                time.sleep(2)
        
        # Save batch processing summary
        self.save_batch_summary()
        
        return results
    
    def save_batch_summary(self, filename: str = "batch_processing_summary.json"):
        """Save summary of all batch processing results."""
        filepath = os.path.join(self.output_dir, filename)
        
        summary = {
            'total_batches': len(self.batch_status),
            'completed': sum(1 for s in self.batch_status.values() if s['status'] == 'completed'),
            'failed': sum(1 for s in self.batch_status.values() if s['status'] == 'failed'),
            'batch_details': self.batch_status,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Batch summary saved to {filepath}")
        return filepath
    
    def get_batch_status(self) -> Dict:
        """Get current status of all batch processing."""
        return {
            'total_batches': len(self.batch_status),
            'completed': sum(1 for s in self.batch_status.values() if s['status'] == 'completed'),
            'failed': sum(1 for s in self.batch_status.values() if s['status'] == 'failed'),
            'in_progress': sum(1 for s in self.batch_status.values() if s['status'] == 'in_progress'),
            'details': self.batch_status
        }
    
    def extract_themes_from_analysis(self, analysis_file: str) -> List[str]:
        """Extract key themes from an analysis file."""
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple extraction - look for theme section
            themes = []
            if "KEY THEMES" in content:
                lines = content.split('\n')
                in_themes = False
                for line in lines:
                    if "KEY THEMES" in line:
                        in_themes = True
                        continue
                    if in_themes:
                        if line.strip().startswith('-') or line.strip().startswith('Theme'):
                            themes.append(line.strip())
                        elif line.strip() and not line.strip().startswith(' ') and len(themes) > 0:
                            break
            
            return themes[:5]  # Top 5 themes
            
        except Exception as e:
            print(f"Error extracting themes: {e}")
            return []
    
    def consolidate_all_analyses(self, output_file: str = "comprehensive_analysis.txt") -> str:
        """
        Consolidate all batch analyses into a single comprehensive report.
        """
        filepath = os.path.join(self.output_dir, output_file)
        
        completed_batches = [
            (num, status['output_file']) 
            for num, status in self.batch_status.items() 
            if status['status'] == 'completed'
        ]
        
        if not completed_batches:
            print("No completed batches to consolidate")
            return None
        
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write("COMPREHENSIVE YOUTUBE COMMENT ANALYSIS REPORT\n")
            outfile.write("=" * 80 + "\n\n")
            outfile.write(f"Total Batches Analyzed: {len(completed_batches)}\n")
            outfile.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            outfile.write("=" * 80 + "\n\n\n")
            
            for batch_num, analysis_file in sorted(completed_batches):
                with open(analysis_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n" + "=" * 80 + "\n\n")
        
        print(f"✓ Comprehensive analysis saved to {filepath}")
        return filepath


def main():
    """Example usage of BatchProcessor."""
    # Replace with your Gemini API key
    gemini_api_key = "YOUR_GEMINI_API_KEY"
    
    processor = BatchProcessor(gemini_api_key, output_dir='data/outputs')
    
    # Process all batches
    results = processor.process_all_batches(batch_dir='data/batches')
    
    # Get status
    status = processor.get_batch_status()
    print(f"\n{'='*60}")
    print(f"Processing Summary")
    print(f"{'='*60}")
    print(f"Total batches: {status['total_batches']}")
    print(f"Completed: {status['completed']}")
    print(f"Failed: {status['failed']}")
    
    # Consolidate analyses
    if status['completed'] > 0:
        processor.consolidate_all_analyses()


if __name__ == "__main__":
    main()
