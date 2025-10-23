# rag/loaders/api_loader.py

import requests
import json
from typing import List, Dict, Any

def load_from_api(url: str, headers: Dict[str, str] = None, params: Dict[str, Any] = None) -> str:
    """
    Load text content from an API endpoint.
    
    Args:
        url: API endpoint URL
        headers: Optional headers for the request
        params: Optional query parameters
        
    Returns:
        String content from the API response
        
    Raises:
        requests.RequestException: If API request fails
        ValueError: If response is not valid JSON or text
    """
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        # Try to parse as JSON first
        try:
            data = response.json()
            # If it's a list, join the items
            if isinstance(data, list):
                return "\n".join(str(item) for item in data)
            # If it's a dict, convert to string
            elif isinstance(data, dict):
                return json.dumps(data, indent=2)
            else:
                return str(data)
        except json.JSONDecodeError:
            # If not JSON, return as text
            return response.text
    
    except requests.RequestException as e:
        raise requests.RequestException(f"API request failed: {str(e)}")

def load_from_multiple_apis(api_configs: List[Dict[str, Any]]) -> List[str]:
    """
    Load content from multiple API endpoints.
    
    Args:
        api_configs: List of dictionaries with 'url', 'headers', and 'params' keys
        
    Returns:
        List of text contents from all API endpoints
    """
    contents = []
    
    for i, config in enumerate(api_configs):
        try:
            url = config.get('url')
            headers = config.get('headers', {})
            params = config.get('params', {})
            
            content = load_from_api(url, headers, params)
            contents.append(content)
            print(f"✅ Loaded from API {i+1}: {url}")
            
        except Exception as e:
            print(f"❌ Error loading from API {i+1}: {e}")
    
    return contents

def load_law_api_data(api_key: str = None) -> List[str]:
    """
    Load data from common law-related APIs.
    This is a template function - you'll need to customize based on your specific law data sources.
    
    Args:
        api_key: Optional API key for authenticated endpoints
        
    Returns:
        List of text contents from law APIs
    """
    # Example law API configurations
    law_apis = [
        {
            'url': 'https://api.law.example.com/cases',
            'headers': {'Authorization': f'Bearer {api_key}'} if api_key else {},
            'params': {'limit': 100}
        },
        {
            'url': 'https://api.legal.example.com/statutes',
            'headers': {'X-API-Key': api_key} if api_key else {},
            'params': {'format': 'text'}
        }
    ]
    
    return load_from_multiple_apis(law_apis)

