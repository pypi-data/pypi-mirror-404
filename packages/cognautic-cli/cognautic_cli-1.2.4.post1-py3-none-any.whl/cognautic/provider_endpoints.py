"""
API Endpoints and configurations for all AI providers
"""

# Provider API Endpoints and Model Information
PROVIDER_ENDPOINTS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "chat_endpoint": "/chat/completions",
        "models_endpoint": "/models",
        "embeddings_endpoint": "/embeddings",
        "audio_endpoint": "/audio",
        "images_endpoint": "/images",
        "files_endpoint": "/files",
        "fine_tuning_endpoint": "/fine_tuning",
        "moderations_endpoint": "/moderations",
        "assistants_endpoint": "/assistants",
        "threads_endpoint": "/threads",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "chat_endpoint": "/v1/messages",
        "models_endpoint": "/v1/models",
        "headers": {
            "x-api-key": "{api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    },
    
    "google": {
        "base_url": "https://generativelanguage.googleapis.com",
        "chat_endpoint": "/v1beta/models/{model}:generateContent",
        "models_endpoint": "/v1beta/models",
        "embeddings_endpoint": "/v1beta/models/{model}:embedContent",
        "count_tokens_endpoint": "/v1beta/models/{model}:countTokens",
        "headers": {
            "Content-Type": "application/json"
        },
        "auth_param": "key={api_key}"
    },
    
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "chat_endpoint": "/chat/completions",
        "models_endpoint": "/models",
        "completions_endpoint": "/completions",
        "embeddings_endpoint": "/embeddings",
        "images_endpoint": "/images/generations",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "chat_endpoint": "/chat/completions",
        "models_endpoint": "/models",
        "auth_endpoint": "/auth/key",
        "generation_endpoint": "/generation",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cognautic-cli.local",
            "X-Title": "Cognautic CLI"
        }
    },
    
    "huggingface": {
        "base_url": "https://api-inference.huggingface.co",
        "models_endpoint": "/models",
        "inference_endpoint": "/models/{model}",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "cohere": {
        "base_url": "https://api.cohere.ai/v1",
        "chat_endpoint": "/chat",
        "generate_endpoint": "/generate",
        "embed_endpoint": "/embed",
        "classify_endpoint": "/classify",
        "summarize_endpoint": "/summarize",
        "rerank_endpoint": "/rerank",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "replicate": {
        "base_url": "https://api.replicate.com/v1",
        "predictions_endpoint": "/predictions",
        "models_endpoint": "/models",
        "collections_endpoint": "/collections",
        "headers": {
            "Authorization": "Token {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "perplexity": {
        "base_url": "https://api.perplexity.ai",
        "chat_endpoint": "/chat/completions",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "chat_endpoint": "/chat/completions",
        "models_endpoint": "/models",
        "embeddings_endpoint": "/embeddings",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "chat_endpoint": "/chat/completions",
        "models_endpoint": "/models",
        "audio_endpoint": "/audio",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "chat_endpoint": "/chat/completions",
        "models_endpoint": "/models",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "fireworks": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "chat_endpoint": "/chat/completions",
        "completions_endpoint": "/completions",
        "embeddings_endpoint": "/embeddings",
        "models_endpoint": "/models",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "anyscale": {
        "base_url": "https://api.endpoints.anyscale.com/v1",
        "chat_endpoint": "/chat/completions",
        "models_endpoint": "/models",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "ai21": {
        "base_url": "https://api.ai21.com/studio/v1",
        "complete_endpoint": "/complete",
        "chat_endpoint": "/chat/completions",
        "tokenize_endpoint": "/tokenize",
        "headers": {
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json"
        }
    },
    
    "ollama": {
        "base_url": "http://localhost:11434/api",
        "chat_endpoint": "/chat",
        "models_endpoint": "/tags",
        "headers": {
            "Content-Type": "application/json"
        },
        "no_auth": True
    },
    
    "palm": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "generate_endpoint": "/models/{model}:generateText",
        "chat_endpoint": "/models/{model}:generateMessage",
        "embed_endpoint": "/models/{model}:embedText",
        "models_endpoint": "/models",
        "headers": {
            "Content-Type": "application/json"
        },
        "auth_param": "key={api_key}"
    },
    
    "claude": {
        "base_url": "https://api.anthropic.com/v1",
        "messages_endpoint": "/messages",
        "complete_endpoint": "/complete",
        "headers": {
            "x-api-key": "{api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    }
}

# Generic HTTP client for making API requests
import aiohttp
import json
import os
from typing import Dict, Any, Optional

class GenericAPIClient:
    """Generic API client that can work with any provider"""
    
    def __init__(self, provider_name: str, api_key: str, base_url: Optional[str] = None):
        self.provider_name = provider_name
        self.api_key = api_key
        self.config = PROVIDER_ENDPOINTS.get(provider_name, {})
        self.base_url_override = base_url
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers with API key substituted"""
        headers = self.config.get("headers", {}).copy()
        for key, value in headers.items():
            if isinstance(value, str) and "{api_key}" in value:
                headers[key] = value.format(api_key=self.api_key)
        return headers
    
    def get_url(self, endpoint_key: str, **kwargs) -> str:
        """Get full URL for an endpoint"""
        # Determine base URL with override precedence: explicit override > env var > config
        base_url = self.base_url_override or \
                   os.environ.get(f"{self.provider_name.upper()}_BASE_URL") or \
                   self.config.get("base_url", "")
        endpoint = self.config.get(endpoint_key, "")
        
        # Format endpoint with any parameters (like model name)
        if kwargs:
            endpoint = endpoint.format(**kwargs)
            
        url = base_url + endpoint
        
        # Add auth parameter if needed (for Google/Palm)
        if "auth_param" in self.config:
            auth_param = self.config["auth_param"].format(api_key=self.api_key)
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{auth_param}"
            
        return url
    
    async def make_request(self, endpoint_key: str, method: str = "POST", 
                          data: Optional[Dict] = None, **url_kwargs) -> Dict[str, Any]:
        """Make an API request to any endpoint"""
        url = self.get_url(endpoint_key, **url_kwargs)
        headers = self.get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None
            ) as response:
                if response.content_type == 'application/json':
                    return await response.json()
                else:
                    text = await response.text()
                    return {"text": text, "status": response.status}
    
    async def stream_chat_completion(self, messages: list, model: str, **kwargs):
        """Stream chat completion chunks. Currently implemented for Ollama."""
        if self.provider_name != "ollama":
            raise NotImplementedError("Streaming not implemented for this provider")
        
        url = self.get_url("chat_endpoint")
        headers = self.get_headers()
        options: Dict[str, Any] = {
            "temperature": kwargs.get("temperature", 0.7)
        }
        if kwargs.get("max_tokens") is not None:
            options["num_predict"] = kwargs.get("max_tokens")
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                buffer = ""
                async for raw in response.content.iter_any():
                    try:
                        text = raw.decode("utf-8")
                    except Exception:
                        continue
                    if not text:
                        continue
                    buffer += text
                    # Normalize to lines
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("data:"):
                            line = line[5:].strip()
                            if not line:
                                continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            # Not a full JSON line yet; prepend back to buffer head
                            buffer = line + "\n" + buffer
                            break
                        # Yield content
                        chunk = None
                        msg = obj.get("message") or {}
                        if isinstance(msg, dict):
                            chunk = msg.get("content")
                        if not chunk:
                            chunk = obj.get("response")
                        if chunk:
                            yield chunk
                        # Stop early if Ollama signals completion
                        if obj.get("done") is True:
                            return
    
    async def chat_completion(self, messages: list, model: str, **kwargs) -> Dict[str, Any]:
        """Generic chat completion that works with most providers"""
        
        # Format messages based on provider
        if self.provider_name == "google":
            # Google Gemini format
            data = {
                "contents": [
                    {
                        "parts": [{"text": msg["content"]}],
                        "role": "user" if msg["role"] == "user" else "model"
                    }
                    for msg in messages
                ],
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "maxOutputTokens": kwargs.get("max_tokens", 8192)
                }
            }
            return await self.make_request("chat_endpoint", data=data, model=model)
            
        elif self.provider_name == "anthropic":
            # Anthropic Claude format
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "temperature": kwargs.get("temperature", 0.7)
            }
            return await self.make_request("chat_endpoint", data=data)
        
        elif self.provider_name == "ollama":
            # Ollama chat format
            options: Dict[str, Any] = {
                "temperature": kwargs.get("temperature", 0.7)
            }
            if kwargs.get("max_tokens") is not None:
                # Ollama uses num_predict for max new tokens
                options["num_predict"] = kwargs.get("max_tokens")
            data = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": options
            }
            return await self.make_request("chat_endpoint", data=data)
            
        else:
            # OpenAI-compatible format (works with most providers)
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": kwargs.get("stream", False)
            }
            return await self.make_request("chat_endpoint", data=data)
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models for the provider"""
        return await self.make_request("models_endpoint", method="GET")

def get_provider_config(provider_name: str) -> Dict[str, Any]:
    """Get configuration for a specific provider"""
    return PROVIDER_ENDPOINTS.get(provider_name, {})

def get_all_providers() -> list:
    """Get list of all supported providers"""
    return list(PROVIDER_ENDPOINTS.keys())

def get_provider_endpoints(provider_name: str) -> Dict[str, str]:
    """Get all endpoints for a specific provider"""
    config = PROVIDER_ENDPOINTS.get(provider_name, {})
    return {k: v for k, v in config.items() if k.endswith("_endpoint")}

# Popular models for each provider
PROVIDER_MODELS = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k"
    ],
    "anthropic": [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ],
    "google": [
        "gemini-2.0-flash-exp",
        "gemini-exp-1206",
        "gemini-2.0-flash-thinking-exp-1219",
        "gemini-exp-1121",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b"
    ],
    "together": [
        "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "deepseek-ai/deepseek-llm-67b-chat"
    ],
    "openrouter": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "google/gemini-pro-1.5",
        "meta-llama/llama-3.1-405b-instruct",
        "mistralai/mixtral-8x22b-instruct"
    ],
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ],
    "mistral": [
        "mistral-large-latest",
        "mistral-medium-latest",
        "mistral-small-latest",
        "open-mistral-7b",
        "open-mixtral-8x7b",
        "open-mixtral-8x22b"
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-coder"
    ],
    "perplexity": [
        "llama-3.1-sonar-small-128k-online",
        "llama-3.1-sonar-large-128k-online",
        "llama-3.1-sonar-huge-128k-online"
    ],
    "cohere": [
        "command-r-plus",
        "command-r",
        "command",
        "command-light"
    ],
    "fireworks": [
        "accounts/fireworks/models/llama-v3p1-405b-instruct",
        "accounts/fireworks/models/llama-v3p1-70b-instruct",
        "accounts/fireworks/models/mixtral-8x7b-instruct"
    ],
    "huggingface": [
        "meta-llama/Meta-Llama-3-70B-Instruct",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "google/gemma-7b-it"
    ],
    "replicate": [
        "meta/llama-2-70b-chat",
        "mistralai/mixtral-8x7b-instruct-v0.1"
    ],
    "anyscale": [
        "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "mistralai/Mixtral-8x7B-Instruct-v0.1"
    ],
    "ai21": [
        "jamba-1.5-large",
        "jamba-1.5-mini"
    ]
}

def get_provider_models(provider_name: str) -> list:
    """Get list of popular models for a provider"""
    return PROVIDER_MODELS.get(provider_name, [])
