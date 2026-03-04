import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
from urllib.parse import urljoin, urlparse

class WebSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.proxies = {}
        self.visited_urls = set()
        self.max_depth = 2
    
    def set_proxies(self, proxies):
        self.proxies = proxies
    
    def set_max_depth(self, depth):
        self.max_depth = depth
    
    def crawl(self, start_url, rules=None, depth=0):
        if depth > self.max_depth or start_url in self.visited_urls:
            return []
        
        self.visited_urls.add(start_url)
        print(f'Crawling: {start_url}')
        
        try:
            time.sleep(random.uniform(1, 3))  # 反爬机制
            response = requests.get(start_url, headers=self.headers, proxies=self.proxies, timeout=10, verify=False)  # 禁用SSL验证
            response.raise_for_status()
        except Exception as e:
            print(f'Error crawling {start_url}: {e}')
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        data = []
        
        if rules:
            for rule in rules:
                elements = soup.select(rule['selector'])
                for element in elements:
                    item = {}
                    if 'extract' in rule:
                        for key, extractor in rule['extract'].items():
                            if extractor == 'text':
                                item[key] = element.get_text(strip=True)
                            elif extractor.startswith('attr:'):
                                attr = extractor.split(':', 1)[1]
                                item[key] = element.get(attr, '')
                    data.append(item)
        
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            absolute_url = urljoin(start_url, href)
            parsed_url = urlparse(absolute_url)
            if parsed_url.scheme in ['http', 'https']:
                links.append(absolute_url)
        
        for link in links[:10]:  # 限制爬取链接数量
            data.extend(self.crawl(link, rules, depth + 1))
        
        return data
    
    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_to_csv(self, data, filename):
        if not data:
            return
        
        keys = data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
