"""
Web search tool for information retrieval
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
import json

from .base import BaseTool, ToolResult, PermissionLevel


class WebSearchTool(BaseTool):
    """Tool for web search and content retrieval"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information and documentation",
            permission_level=PermissionLevel.SAFE_OPERATIONS
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "search_web",
            "fetch_url_content",
            "parse_documentation",
            "get_api_docs"
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information and documentation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": self.get_capabilities()
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL to fetch or parse"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 10)"
                        },
                        "extract_text": {
                            "type": "boolean",
                            "description": "Whether to extract plain text from HTML"
                        },
                        "api_name": {
                            "type": "string",
                            "description": "Name of the API to get documentation for"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute web search operation"""
        operation = kwargs.pop('operation', None)
        
        operations = {
            'search_web': self._search_web,
            'fetch_url_content': self._fetch_url_content,
            'parse_documentation': self._parse_documentation,
            'get_api_docs': self._get_api_docs
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation: {operation}"
            )
        
        try:
            result = await operations[operation](**kwargs)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _search_web(
        self,
        query: str,
        num_results: int = 10,
        search_engine: str = "duckduckgo"
    ) -> List[Dict[str, Any]]:
        """Search the web for information"""
        
        if search_engine == "duckduckgo":
            return await self._search_duckduckgo(query, num_results)
        else:
            raise ValueError(f"Unsupported search engine: {search_engine}")
    
    async def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo"""
        
        # DuckDuckGo Instant Answer API
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        results = []
                        
                        # Add abstract if available
                        if data.get('Abstract'):
                            results.append({
                                'title': data.get('Heading', 'Abstract'),
                                'snippet': data.get('Abstract'),
                                'url': data.get('AbstractURL', ''),
                                'source': data.get('AbstractSource', 'DuckDuckGo')
                            })
                        
                        # Add related topics
                        for topic in data.get('RelatedTopics', [])[:num_results-1]:
                            if isinstance(topic, dict) and 'Text' in topic:
                                results.append({
                                    'title': topic.get('Text', '').split(' - ')[0],
                                    'snippet': topic.get('Text', ''),
                                    'url': topic.get('FirstURL', ''),
                                    'source': 'DuckDuckGo'
                                })
                        
                        # If no results, try web scraping approach
                        if not results:
                            return await self._scrape_search_results(query, num_results)
                        
                        return results[:num_results]
                    else:
                        raise Exception(f"Search API returned status {response.status}")
                        
            except Exception as e:
                # Fallback to web scraping
                return await self._scrape_search_results(query, num_results)
    
    async def _scrape_search_results(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Scrape search results as fallback"""
        
        # Use DuckDuckGo HTML search as fallback
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        results = []
                        result_divs = soup.find_all('div', class_='result')
                        
                        for div in result_divs[:num_results]:
                            title_elem = div.find('a', class_='result__a')
                            snippet_elem = div.find('a', class_='result__snippet')
                            
                            if title_elem:
                                results.append({
                                    'title': title_elem.get_text(strip=True),
                                    'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                                    'url': title_elem.get('href', ''),
                                    'source': 'Web Search'
                                })
                        
                        return results
                    else:
                        raise Exception(f"Search scraping returned status {response.status}")
                        
            except Exception as e:
                # Return empty results if all methods fail
                return [{
                    'title': 'Search Failed',
                    'snippet': f'Unable to perform web search: {str(e)}',
                    'url': '',
                    'source': 'Error'
                }]
    
    async def _fetch_url_content(
        self,
        url: str,
        extract_text: bool = True,
        max_length: int = 10000
    ) -> Dict[str, Any]:
        """Fetch content from a URL"""
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'text/html' in content_type:
                            html = await response.text()
                            
                            if extract_text:
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Remove script and style elements
                                for script in soup(["script", "style"]):
                                    script.decompose()
                                
                                # Get text content
                                text = soup.get_text()
                                
                                # Clean up text
                                lines = (line.strip() for line in text.splitlines())
                                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                                text = ' '.join(chunk for chunk in chunks if chunk)
                                
                                # Truncate if too long
                                if len(text) > max_length:
                                    text = text[:max_length] + "..."
                                
                                return {
                                    'url': url,
                                    'title': soup.title.string if soup.title else '',
                                    'content': text,
                                    'content_type': 'text',
                                    'length': len(text)
                                }
                            else:
                                return {
                                    'url': url,
                                    'content': html,
                                    'content_type': 'html',
                                    'length': len(html)
                                }
                        
                        elif 'application/json' in content_type:
                            json_data = await response.json()
                            return {
                                'url': url,
                                'content': json_data,
                                'content_type': 'json',
                                'length': len(str(json_data))
                            }
                        
                        else:
                            text = await response.text()
                            return {
                                'url': url,
                                'content': text,
                                'content_type': 'text',
                                'length': len(text)
                            }
                    
                    else:
                        raise Exception(f"HTTP {response.status}: {response.reason}")
                        
            except Exception as e:
                raise Exception(f"Failed to fetch URL content: {str(e)}")
    
    async def _parse_documentation(
        self,
        url: str,
        doc_type: str = "auto"
    ) -> Dict[str, Any]:
        """Parse documentation from a URL"""
        
        content_data = await self._fetch_url_content(url, extract_text=True)
        
        if doc_type == "auto":
            # Try to detect documentation type
            url_lower = url.lower()
            if 'github.com' in url_lower and 'readme' in url_lower:
                doc_type = "readme"
            elif 'docs.' in url_lower or '/docs/' in url_lower:
                doc_type = "api_docs"
            else:
                doc_type = "general"
        
        # Parse based on type
        parsed_content = {
            'url': url,
            'doc_type': doc_type,
            'title': content_data.get('title', ''),
            'content': content_data.get('content', ''),
            'sections': []
        }
        
        # Try to extract sections (simplified)
        content = content_data.get('content', '')
        sections = []
        current_section = {'title': 'Introduction', 'content': ''}
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('#') or line.isupper() and len(line) < 100:
                # Likely a heading
                if current_section['content']:
                    sections.append(current_section)
                current_section = {'title': line.lstrip('#').strip(), 'content': ''}
            else:
                current_section['content'] += line + '\n'
        
        if current_section['content']:
            sections.append(current_section)
        
        parsed_content['sections'] = sections
        return parsed_content
    
    async def _get_api_docs(
        self,
        api_name: str,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """Get API documentation for popular APIs"""
        
        # Common API documentation URLs
        api_docs = {
            'openai': 'https://platform.openai.com/docs/api-reference',
            'anthropic': 'https://docs.anthropic.com/claude/reference',
            'github': 'https://docs.github.com/en/rest',
            'stripe': 'https://stripe.com/docs/api',
            'twilio': 'https://www.twilio.com/docs/usage/api',
            'aws': 'https://docs.aws.amazon.com/',
            'google': 'https://developers.google.com/apis-explorer',
            'microsoft': 'https://docs.microsoft.com/en-us/rest/api/'
        }
        
        api_name_lower = api_name.lower()
        
        if api_name_lower in api_docs:
            url = api_docs[api_name_lower]
            return await self._parse_documentation(url, doc_type="api_docs")
        else:
            # Search for API documentation
            search_query = f"{api_name} API documentation {version}"
            search_results = await self._search_web(search_query, num_results=5)
            
            if search_results:
                # Try to fetch the first result
                first_result = search_results[0]
                if first_result['url']:
                    try:
                        return await self._parse_documentation(first_result['url'], doc_type="api_docs")
                    except Exception:
                        pass
            
            return {
                'api_name': api_name,
                'version': version,
                'found': False,
                'search_results': search_results,
                'message': f'Could not find API documentation for {api_name}'
            }
