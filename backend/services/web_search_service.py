import httpx
import json
import re
import asyncio
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class WebSearchService:
    """Service for web searching and information retrieval"""
    
    def __init__(self):
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.max_results = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
        self.timeout = int(os.getenv("SEARCH_TIMEOUT", "10"))
        
    async def search_duckduckgo(self, query: str, num_results: int = None) -> List[Dict]:
        """Search using DuckDuckGo (no API key required)"""
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Referer': 'https://duckduckgo.com/',
            }
            
            if num_results is None:
                num_results = self.max_results
            
            # First get the token
            async with httpx.AsyncClient(headers=headers, timeout=float(self.timeout)) as client:
                # DuckDuckGo search
                search_url = "https://html.duckduckgo.com/html/"
                params = {
                    'q': query,
                    'b': '',
                    'kl': 'us-en',
                    'df': ''
                }
                
                response = await client.get(search_url, params=params)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = []
                    
                    # Find search result elements
                    result_elements = soup.find_all('div', class_='result')[:num_results]
                    
                    for element in result_elements:
                        title_elem = element.find('a', class_='result__a')
                        snippet_elem = element.find('a', class_='result__snippet')
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            url = title_elem.get('href', '')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                            
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet
                            })
                    
                    return results
                return []
                
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []

    async def get_weather_info(self, city: str, country: str = "") -> Optional[Dict]:
        """Get weather information for a specific city"""
        try:
            query = f"weather {city} {country} current temperature"
            search_results = await self.search_duckduckgo(query, 3)
            
            # Try to extract weather info from search results
            weather_info = {
                'city': city,
                'country': country,
                'temperature': 'N/A',
                'condition': 'N/A',
                'source': 'Search results',
                'results': search_results[:2]  # Top 2 results
            }
            
            # Look for temperature patterns in snippets
            temp_patterns = [
                r'(\d+)°[CF]',
                r'(\d+) degrees',
                r'temperature.*?(\d+)',
                r'(\d+)°'
            ]
            
            for result in search_results:
                snippet = result.get('snippet', '').lower()
                for pattern in temp_patterns:
                    match = re.search(pattern, snippet, re.IGNORECASE)
                    if match:
                        weather_info['temperature'] = match.group(1) + '°C'
                        break
                if weather_info['temperature'] != 'N/A':
                    break
            
            return weather_info
            
        except Exception as e:
            print(f"Weather search error: {e}")
            return None

    async def search_general_info(self, query: str) -> Dict:
        """Search for general information"""
        try:
            search_results = await self.search_duckduckgo(query, 5)
            
            return {
                'query': query,
                'results': search_results,
                'summary': self._create_summary(search_results)
            }
            
        except Exception as e:
            print(f"General search error: {e}")
            return {
                'query': query,
                'results': [],
                'summary': f'Search failed: {str(e)}'
            }

    def _create_summary(self, results: List[Dict]) -> str:
        """Create a summary from search results"""
        if not results:
            return "No results found."
        
        summary_parts = []
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            if title and snippet:
                summary_parts.append(f"{i}. {title}: {snippet}")
        
        return '\n'.join(summary_parts) if summary_parts else "No detailed information found."

    async def fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch and extract text content from a webpage"""
        try:
            headers = {'User-Agent': self.user_agent}
            
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Get text and clean it
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # Return first 1000 characters
                    return text[:1000] + "..." if len(text) > 1000 else text
                return None
                
        except Exception as e:
            print(f"Page fetch error: {e}")
            return None