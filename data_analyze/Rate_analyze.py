import requests
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt

class SuggestionAnalyzer:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'Mozilla/5.0'}
        self.rating_map = {
            "非常不满意": 1,  # "Very Dissatisfied"
            "比较不满意": 2,  # "Somewhat Dissatisfied"
            "一般": 3,       # "Neutral"
            "比较满意": 4,   # "Somewhat Satisfied"
            "非常满意": 5    # "Very Satisfied"
        }
        self.rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.total_rating = 0
        self.total_count = 0

    def get_folders(self):
        """Get all folder names"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            folders = re.findall(r'href="([^"/]+/)"', response.text)
            return [f.strip('/') for f in folders if not f.startswith(('?', '.'))]
        except Exception as e:
            print(f"Failed to get folder list: {str(e)}")
            return []

    def process_suggestion_file(self, folder):
        """Process suggestion.txt in each folder"""
        file_url = urljoin(self.base_url, f"{folder}/suggestion.txt")
        try:
            response = self.session.get(file_url, timeout=10)
            response.raise_for_status()
            
            # Parse a;b format
            match = re.search(r'^(.+?);', response.text)
            if not match:
                print(f"⚠️ Format error: {folder}/suggestion.txt")
                return
            
            feedback = match.group(1).strip()
            rating = self.rating_map.get(feedback, None)
            
            if rating is None:
                print(f"⚠️ Unknown rating: '{feedback}' in {folder}")
                return
            
            self.rating_counts[rating] += 1
            self.total_rating += rating
            self.total_count += 1
            
            print(f"✔ {folder}: {feedback} → Rating {rating}")
            
        except Exception as e:
            print(f"❌ Processing failed {folder}: {str(e)}")

    def generate_chart(self):
        """Generate rating distribution chart (English version)"""
        ratings = sorted(self.rating_counts.keys())
        counts = [self.rating_counts[r] for r in ratings]
        labels = [f"Rating {r}" for r in ratings]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, counts, color=['#ff6b6b', '#ffa502', '#feca57', '#2ecc71', '#1dd1a1'])
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.title('User Rating Distribution', fontsize=15, pad=20)
        plt.xlabel('Rating Level', labelpad=10)
        plt.ylabel('Count', labelpad=10)
        plt.grid(axis='y', alpha=0.4)
        plt.tight_layout()
        
        # Save chart
        plt.show()
        print("\n📈 Chart generated: rating_distribution.png")


    def analyze(self):
        """Run analysis"""
        print(f"🔍 Analyzing {self.base_url}")
        
        folders = self.get_folders()
        if not folders:
            print("⚠️ No folders found")
            return
        
        print(f"Found {len(folders)} folders")
        
        # Multi-thread processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.process_suggestion_file, folders)
        
        if self.total_count == 0:
            print("⚠️ No valid rating data found")
            return
        
        average = round(self.total_rating / self.total_count, 2)
        print(f"\n📊 Analysis Results:")
        print(f"- Valid responses: {self.total_count}")
        print(f"- Total rating: {self.total_rating}")
        print(f"- Average rating: {average}")
        
        print("\n📋 Rating Distribution:")
        for rating, count in sorted(self.rating_counts.items()):
            print(f"- Rating {rating}: {count} counts")
        
        # Generate chart
        self.generate_chart()

if __name__ == "__main__":
    analyzer = SuggestionAnalyzer(
        base_url="https://sandtray.qdzx.net.cn/user_data/"
    )
    analyzer.analyze()