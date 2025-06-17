import requests
import re
import json
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import numpy as np

class EnhancedAnalyzer:
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
        self.element_stats = {1: [], 2: [], 3: [], 4: [], 5: []}
        self.total_rating = 0
        self.total_count = 0

    def get_trimmed_mean(self, values):
        """Calculate mean after removing max and min values"""
        if len(values) <= 2:
            return np.mean(values) if values else 0
        sorted_values = sorted(values)
        return np.mean(sorted_values[1:-1])  # Exclude first and last

    def get_folders(self):
        """Get all folder names from the base URL"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            folders = re.findall(r'href="([^"/]+/)"', response.text)
            return [f.strip('/') for f in folders if not f.startswith(('?', '.'))]
        except Exception as e:
            print(f"Failed to get folder list: {str(e)}")
            return []

    def process_folder(self, folder):
        """Process both suggestion.txt and elements.json in a folder"""
        rating = self.get_folder_rating(folder)
        if rating is not None:
            self.process_element_file(folder, rating)

    def get_folder_rating(self, folder):
        """Extract rating from suggestion.txt"""
        file_url = urljoin(self.base_url, f"{folder}/suggestion.txt")
        try:
            response = self.session.get(file_url, timeout=10)
            response.raise_for_status()
            
            match = re.search(r'^(.+?);', response.text)
            if not match:
                print(f"⚠️ Format error: {folder}/suggestion.txt")
                return None
            
            feedback = match.group(1).strip()
            rating = self.rating_map.get(feedback)
            
            if rating is None:
                print(f"⚠️ Unknown rating: '{feedback}' in {folder}")
                return None
            
            self.rating_counts[rating] += 1
            self.total_rating += rating
            self.total_count += 1
            
            print(f"✔ {folder}: {feedback} → Rating {rating}")
            return rating
            
        except Exception as e:
            print(f"❌ Failed to process rating for {folder}: {str(e)}")
            return None

    def process_element_file(self, folder, rating):
        """Count dictionaries in elements.json"""
        file_url = urljoin(self.base_url, f"{folder}/elements.json")
        try:
            response = self.session.get(file_url, timeout=10)
            response.raise_for_status()
            
            data = json.loads(response.text)
            if isinstance(data, list):
                dict_count = sum(1 for item in data if isinstance(item, dict))
                self.element_stats[rating].append(dict_count)
                print(f"📊 {folder}: Found {dict_count} dictionaries")
            else:
                print(f"⚠️ elements.json in {folder} is not a list")
            
        except Exception as e:
            print(f"❌ Failed to process elements.json in {folder}: {str(e)}")

    def generate_combined_chart(self):
        """Create visualization with rating distribution and trimmed averages"""
        plt.figure(figsize=(12, 7))
        
        ratings = sorted(self.rating_counts.keys())
        bar_counts = [self.rating_counts[r] for r in ratings]
        line_avgs = [self.get_trimmed_mean(self.element_stats[r]) for r in ratings]
        
        # Bar chart (rating distribution)
        bars = plt.bar(
            [f"Rating {r}" for r in ratings], 
            bar_counts, 
            color=['#ff6b6b', '#ffa502', '#feca57', '#2ecc71', '#1dd1a1'],
            alpha=0.7,
            label='Rating Count'
        )
        
        # Line chart (trimmed averages)
        ax2 = plt.gca().twinx()
        line, = ax2.plot(
            [f"Rating {r}" for r in ratings], 
            line_avgs, 
            color='#3498db', 
            marker='o', 
            markersize=8,
            linewidth=3,
            label='Trimmed Avg Elements'
        )
        
        # Add data labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        for x, y in zip(ratings, line_avgs):
            ax2.text(x-1, y, f'{y:.1f}', ha='center', va='bottom', color='#3498db')
        
        # Chart styling
        plt.title('Rating Distribution & Trimmed Average Elements', fontsize=16)
        plt.xlabel('Rating Level', fontsize=12)
        ax2.set_ylabel('Average Dictionaries (trimmed)', fontsize=12)
        plt.ylabel('Rating Count', fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        plt.legend([bars[0], line], ['Rating Count', 'Trimmed Avg'])
        plt.tight_layout()
        plt.show()

    def analyze(self):
        """Run complete analysis"""
        print(f"🔍 Analyzing {self.base_url}")
        
        folders = self.get_folders()
        if not folders:
            print("⚠️ No folders found")
            return
        
        print(f"Found {len(folders)} folders")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(self.process_folder, folders))
        
        if self.total_count == 0:
            print("⚠️ No valid rating data found")
            return
        
        # Calculate statistics
        average_rating = round(self.total_rating / self.total_count, 2)
        
        print(f"\n📊 Analysis Results:")
        print(f"- Total responses: {self.total_count}")
        print(f"- Average rating: {average_rating}")
        
        print("\n📋 Rating Distribution:")
        for rating, count in sorted(self.rating_counts.items()):
            print(f"- Rating {rating}: {count} responses")
        
        print("\n📦 Elements Analysis (trimmed means):")
        for rating in sorted(self.element_stats.keys()):
            counts = self.element_stats[rating]
            if counts:
                original = np.mean(counts)
                trimmed = self.get_trimmed_mean(counts)
                print(f"- Rating {rating}:")
                print(f"  • Original mean: {original:.1f} dicts")
                print(f"  • Trimmed mean:  {trimmed:.1f} dicts")
                print(f"  • Sample size:  {len(counts)} folders")
            else:
                print(f"- Rating {rating}: No elements data")
        
        self.generate_combined_chart()
        print("\n✅ Analysis complete. Chart saved as rating_analysis.png")

if __name__ == "__main__":
    analyzer = EnhancedAnalyzer(
        base_url="https://sandtray.qdzx.net.cn/user_data/"
    )
    analyzer.analyze()