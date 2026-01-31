"""
AI Engine for multi-provider AI interactions
"""

import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from .auto_continuation import AutoContinuationManager
from .config import ConfigManager
from .provider_endpoints import GenericAPIClient, get_all_providers, get_provider_config
from .tools import ToolRegistry


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict],
        model: str = None,
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Any:  # Can return string or ToolCalls
        """Generate response from the AI provider"""
        pass

    @abstractmethod
    async def generate_response_stream(
        self,
        messages: List[Dict],
        model: str = None,
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ) -> AsyncGenerator[Any, None]:
        """Stream response from the AI provider"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass


class GenericProvider(AIProvider):
    """Generic provider that can work with any API endpoint"""

    def __init__(self, api_key: str, provider_name: str, base_url: Optional[str] = None):
        super().__init__(api_key)
        self.provider_name = provider_name
        self.client = GenericAPIClient(provider_name, api_key, base_url)

    async def generate_response(
        self, messages: List[Dict], model: str = None, **kwargs
    ) -> str:
        try:
            response = await self.client.chat_completion(messages, model, **kwargs)

            # Extract text from different response formats
            if self.provider_name == "google":
                if "candidates" in response and response["candidates"]:
                    candidate = response["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        full_text = ""
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                full_text += part["text"]
                            elif "thought" in part:
                                full_text += f"<thought>\n{part['thought']}\n</thought>\n"
                        return full_text or "No response generated"
                return "No response generated"

            elif self.provider_name == "anthropic":
                if "content" in response and response["content"]:
                    return response["content"][0]["text"]
                return "No response generated"

            elif self.provider_name == "ollama":
                # Ollama returns { message: { content: ... } }
                if isinstance(response, dict):
                    msg = response.get("message") or {}
                    if isinstance(msg, dict):
                        content = msg.get("content")
                        if content:
                            return content
                return "No response generated"

            else:
                # OpenAI-compatible format
                if "choices" in response and response["choices"]:
                    return response["choices"][0]["message"]["content"]
                return "No response generated"

        except Exception as e:
            raise Exception(f"{self.provider_name.title()} API error: {str(e)}")

    def get_available_models(self) -> List[str]:
        """Get list of available models - returns generic list since we support any model"""
        if self.provider_name == "ollama":
            # Avoid invalid placeholders; require explicit model selection for Ollama
            return []
        return [f"{self.provider_name}-model-1", f"{self.provider_name}-model-2"]

    async def generate_response_stream(
        self, messages: List[Dict], model: str = None, **kwargs
    ):
        """Stream responses for providers that support it (Ollama)."""
        try:
            if self.provider_name == "ollama":
                async for chunk in self.client.stream_chat_completion(
                    messages, model, **kwargs
                ):
                    if chunk:
                        yield chunk
                return
            # For other generic providers, no streaming implemented
            # Fall back to non-streaming
            text = await self.generate_response(messages, model, **kwargs)
            yield text
        except Exception as e:
            raise Exception(f"{self.provider_name.title()} API streaming error: {str(e)}")


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import openai

            self.client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")

    async def generate_response(
        self,
        messages: List[Dict],
        model: str = "gpt-4o",
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Any:
        try:
            # Map tools to OpenAI format
            openai_tools = None
            if tools:
                openai_tools = tools

            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=openai_tools,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
            )
            
            message = response.choices[0].message
            if message.tool_calls:
                return {
                    "content": message.content,
                    "tool_calls": [
                        {
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                }
            return message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def generate_response_stream(
        self,
        messages: List[Dict],
        model: str = "gpt-4o",
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ):
        """Generate streaming response with tool support"""
        try:
            openai_tools = None
            if tools:
                openai_tools = tools

            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=openai_tools,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
                stream=True,
            )
            
            # Map to accumulate tool calls by index
            accumulated_tool_calls = {}
            
            async for chunk in stream:
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # Handle text content
                if delta.content:
                    yield delta.content
                
                # Handle tool calls
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": tc_delta.id,
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            }
                        
                        if tc_delta.id:
                            accumulated_tool_calls[idx]["id"] = tc_delta.id
                            
                        if tc_delta.function:
                            if tc_delta.function.name:
                                accumulated_tool_calls[idx]["function"]["name"] += tc_delta.function.name
                            if tc_delta.function.arguments:
                                accumulated_tool_calls[idx]["function"]["arguments"] += tc_delta.function.arguments
            
            # Yield accumulated tool calls at the end
            if accumulated_tool_calls:
                yield {"tool_calls": list(accumulated_tool_calls.values())}
                
        except Exception as e:
            raise Exception(f"OpenAI API streaming error: {str(e)}")

    def get_available_models(self) -> List[str]:
        return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]


class GoogleProvider(AIProvider):
    """Google provider implementation"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
            self.genai = genai # Keep reference for types if needed
        except ImportError:
            raise ImportError(
                "Google GenAI library not installed. Run: pip install google-genai"
            )

    async def generate_response(
        self,
        messages: List[Dict],
        model: str = "gemini-1.5-pro",
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ) -> str:
        try:
            from google.genai import types
            
            # Convert tools to Google format
            google_tools = None
            if tools:
                google_tools = [types.Tool(function_declarations=[
                    types.FunctionDeclaration(
                        name=t["function"]["name"],
                        description=t["function"].get("description", ""),
                        parameters=t["function"].get("parameters")
                    ) for t in tools
                ])]

            # Convert messages format for Google
            contents = []
            system_instruction = None
            
            # Merge consecutive tool messages for Gemini
            merged_messages = []
            current_tool_parts = []
            for msg in messages:
                if msg.get("role") == "tool":
                    current_tool_parts.append(types.Part(
                        function_response=types.FunctionResponse(
                            name=msg.get("name", "unknown"),
                            response={"result": msg.get("content", "")},
                            id=msg.get("tool_call_id")
                        )
                    ))
                else:
                    if current_tool_parts:
                        merged_messages.append({"role": "user", "parts": current_tool_parts})
                        current_tool_parts = []
                    merged_messages.append(msg)
            if current_tool_parts:
                merged_messages.append({"role": "user", "parts": current_tool_parts})

            for msg in merged_messages:
                if "parts" in msg and msg.get("role") == "user" and msg["parts"] and hasattr(msg["parts"][0], "function_response"):
                    contents.append(types.Content(role="user", parts=msg["parts"]))
                    continue

                role = msg["role"]
                content = msg.get("content", "")
                if role == "system":
                    system_instruction = content
                    continue
                
                role_map = {"user": "user", "assistant": "model", "model": "model"}
                gemini_role = role_map.get(role, "user")
                
                if role in ["assistant", "model"] and msg.get("tool_calls"):
                    parts = []
                    if content:
                        parts.extend(self._parse_content_to_parts_new_sdk(content))
                    
                    sig = msg.get("thought_signature")
                    if not sig:
                        for t in msg["tool_calls"]:
                            if t.get("thought_signature"):
                                sig = t.get("thought_signature")
                                break
                    
                    # Convert signature to bytes if it's a string (e.g. from history)
                    if sig and isinstance(sig, str):
                        try:
                            import base64
                            # Try base64 decoding if it looks like encoded data
                            if len(sig) % 4 == 0 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in sig):
                                try:
                                    sig = base64.b64decode(sig)
                                except:
                                    sig = sig.encode('utf-8')
                            else:
                                sig = sig.encode('utf-8')
                        except:
                            pass

                    for tc in msg["tool_calls"]:
                        fn = tc["function"]
                        try:
                            # Arguments can be dict or JSON string
                            args = fn.get("arguments", {})
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except:
                                    pass
                            
                            part = types.Part(
                                function_call=types.FunctionCall(name=fn["name"], args=args),
                                thought_signature=sig if sig else None
                            )
                            parts.append(part)
                        except Exception:
                            continue
                else:
                    parts = self._parse_content_to_parts_new_sdk(content)
                
                # Filter out messages with no parts to satisfy Gemini API requirements
                if parts:
                    contents.append(types.Content(role=gemini_role, parts=parts))
                elif not msg.get("tool_calls"):
                    # Fallback for empty messages (except those intended to have tool calls)
                    contents.append(types.Content(role=gemini_role, parts=[types.Part.from_text(text=" ")]))

            # Final pass to ensure role alternation and no empty parts
            final_contents = []
            for c in contents:
                if not c.parts:
                    continue
                if final_contents and final_contents[-1].role == c.role:
                    # Merge consecutive turns of same role
                    final_contents[-1].parts.extend(c.parts)
                else:
                    final_contents.append(c)
            contents = final_contents

            response = await self.client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=google_tools,
                    system_instruction=system_instruction,
                    max_output_tokens=kwargs.get("max_tokens", 4096),
                    temperature=kwargs.get("temperature", 0.7),
                )
            )

            # Process response for tool calls
            if response.candidates and response.candidates[0].content.parts:
                parts = response.candidates[0].content.parts
                tool_calls = []
                text_content = ""
                
                for part in parts:
                    if part.function_call:
                        # Native function call
                        fc = part.function_call
                        tc = {
                            "type": "function",
                            "function": {
                                "name": fc.name,
                                "arguments": json.dumps(fc.args) if fc.args else "{}"
                            }
                        }
                        # Capture signature
                        if part.thought_signature:
                            tc["thought_signature"] = part.thought_signature
                        tool_calls.append(tc)
                    elif part.thought:
                        # Capture thinking process
                        text_content += f"<thought>\n{part.thought}\n</thought>\n"
                    elif part.text:
                        text_content += part.text
                
                if tool_calls:
                    res = {"content": text_content or None, "tool_calls": tool_calls}
                    # Also attach signature to the response dict if found
                    for part in parts:
                        if part.thought_signature:
                            res["thought_signature"] = part.thought_signature
                            break
                    return res
                return text_content or "No response generated"

            return "No response generated"

        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")

    async def generate_response_stream(
        self,
        messages: List[Dict],
        model: str = "gemini-1.5-pro",
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ):
        """Generate streaming response with tool support"""
        try:
            from google.genai import types
            
            # Convert tools to Google format
            google_tools = None
            if tools:
                google_tools = [types.Tool(function_declarations=[
                    types.FunctionDeclaration(
                        name=t["function"]["name"],
                        description=t["function"].get("description", ""),
                        parameters=t["function"].get("parameters")
                    ) for t in tools
                ])]

            # Convert messages to Google format
            contents = []
            system_instruction = None
            
            # Pre-process messages to merge consecutive tool turns
            # Gemini requires all function responses for a turn to be in a single message
            merged_messages = []
            current_tool_parts = []
            
            for msg in messages:
                if msg["role"] == "tool":
                    current_tool_parts.append(types.Part(
                        function_response=types.FunctionResponse(
                            name=msg.get("name", "unknown"),
                            response={"result": msg.get("content", "")},
                            id=msg.get("tool_call_id")
                        )
                    ))
                else:
                    # If we have pending tool parts, push them first as a single user message
                    if current_tool_parts:
                        merged_messages.append({"role": "user", "parts": current_tool_parts})
                        current_tool_parts = []
                    merged_messages.append(msg)
            
            # Flush any remaining tool parts
            if current_tool_parts:
                merged_messages.append({"role": "user", "parts": current_tool_parts})

            for msg in merged_messages:
                # Handle actual Gemini message construction
                # If it's our pre-merged tool message, use it directly
                if "parts" in msg and msg.get("role") == "user" and msg["parts"] and hasattr(msg["parts"][0], "function_response"):
                    contents.append(types.Content(role="user", parts=msg["parts"]))
                    continue

                role = msg["role"]
                content = msg.get("content", "")
                
                if role == "system":
                    system_instruction = content
                    continue
                
                role_map = {"user": "user", "assistant": "model", "model": "model"}
                gemini_role = role_map.get(role, "user")
                
                if role in ["assistant", "model"] and "tool_calls" in msg:
                    # Model's previous tool calls
                    parts = []
                    
                    # Add content (thoughts/text)
                    if content:
                        parts.extend(self._parse_content_to_parts_new_sdk(content))
                        
                    # Capture signature for ALL function calls in this turn
                    sig = msg.get("thought_signature")
                    if not sig:
                        for t in msg["tool_calls"]:
                            if t.get("thought_signature"):
                                sig = t.get("thought_signature")
                                break
                    
                    # Convert signature to bytes if it's a string (e.g. from history)
                    if sig and isinstance(sig, str):
                        try:
                            import base64
                            if len(sig) % 4 == 0 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in sig):
                                try:
                                    sig = base64.b64decode(sig)
                                except:
                                    sig = sig.encode('utf-8')
                            else:
                                sig = sig.encode('utf-8')
                        except:
                            pass

                    for tc in msg["tool_calls"]:
                        fn = tc["function"]
                        try:
                            args = fn.get("arguments", {})
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except:
                                    pass
                            
                            part = types.Part(
                                function_call=types.FunctionCall(name=fn["name"], args=args),
                                thought_signature=sig if sig else None
                            )
                            parts.append(part)
                        except Exception:
                            continue
                else:
                    parts = self._parse_content_to_parts_new_sdk(content)
                
                # Filter out messages with no parts
                if parts:
                    contents.append(types.Content(role=gemini_role, parts=parts))
                elif "tool_calls" not in msg:
                    contents.append(types.Content(role=gemini_role, parts=[types.Part.from_text(text=" ")]))

            # Final validation: alternating roles and no empty turns
            final_contents = []
            for c in contents:
                if not c.parts:
                    continue
                if final_contents and final_contents[-1].role == c.role:
                    # Merge consecutive turns
                    final_contents[-1].parts.extend(c.parts)
                else:
                    final_contents.append(c)
            contents = final_contents

            response_stream = await self.client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=google_tools,
                    system_instruction=system_instruction,
                    max_output_tokens=kwargs.get("max_tokens", 4096),
                    temperature=kwargs.get("temperature", 0.7),
                )
            )

            async for chunk in response_stream:
                try:
                    if not chunk.candidates:
                        continue
                        
                    parts = chunk.candidates[0].content.parts
                    
                    # Scan for signature in this chunk first
                    chunk_signature = None
                    for part in parts:
                         if part.thought_signature:
                             chunk_signature = part.thought_signature
                             break
                    
                    for part in parts:
                        if part.thought:
                            # Stream back thinking process wrapped in tags
                            yield f"<thought>\n{part.thought}\n</thought>\n"
                        elif part.text:
                            yield part.text
                        elif part.function_call:
                            # Yield tool call as a special object/dict
                            fc = part.function_call
                            tc = {
                                "type": "function",
                                "function": {
                                    "name": fc.name,
                                    "arguments": json.dumps(fc.args) if fc.args else "{}"
                                }
                            }
                            # Capture and yield signature
                            if chunk_signature:
                                tc["thought_signature"] = chunk_signature
                            elif part.thought_signature:
                                tc["thought_signature"] = part.thought_signature
                                
                            yield {
                                "tool_calls": [tc]
                            }
                        
                except Exception as e:
                    continue
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")

    def _parse_content_to_parts_new_sdk(self, content: str) -> List:
        """Convert string content with <thought> tags into Gemini parts using new SDK types"""
        if not content:
            return []
        
        from google.genai import types
        import re
        parts = []
        
        # Find all thought blocks
        pattern = r"<thought>(.*?)</thought>"
        
        # Find thoughts and extract them from the main content to avoid duplicates/confusion
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if matches:
            last_pos = 0
            for match in matches:
                # Text before this thought
                before = content[last_pos:match.start()].strip()
                if before:
                    parts.append(types.Part.from_text(text=before))
                
                # The thought
                thought_val = match.group(1).strip()
                if thought_val:
                    # New SDK might handle thought parts differently, but usually as a 'thought' field in Part
                    # In many cases it might just be text if not using specialized thinking model
                    # But if the SDK supports 'thought' attribute on Part:
                    part = types.Part(thought=thought_val)
                    parts.append(part)
                
                last_pos = match.end()
            
            # Text after last thought
            after = content[last_pos:].strip()
            if after:
                parts.append(types.Part.from_text(text=after))
        else:
            if content.strip():
                parts = [types.Part.from_text(text=content)]
            
        return parts

    def _parse_content_to_parts(self, content: str) -> List[Dict]:
        """Convert string content with <thought> tags into Gemini parts"""
        if not content:
            return []
        
        import re
        parts = []
        
        # Find all thought blocks
        pattern = r"<thought>(.*?)</thought>"
        last_end = 0
        
        # Priority: Process thoughts first if they exist
        # Note: Gemini 2.0 Thinking usually wants thoughts at the beginning
        thought_parts = []
        text_content = content
        
        # Find thoughts and extract them from the main content to avoid duplicates/confusion
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if matches:
            # We'll build a clean text content by removing thought blocks
            clean_parts = []
            last_pos = 0
            for match in matches:
                # Text before this thought
                before = content[last_pos:match.start()].strip()
                if before:
                    clean_parts.append({"text": before})
                
                # The thought
                thought_val = match.group(1).strip()
                if thought_val:
                    thought_parts.append({"thought": thought_val})
                
                last_pos = match.end()
            
            # Text after last thought
            after = content[last_pos:].strip()
            if after:
                clean_parts.append({"text": after})
            
            # Combine: Thought(s) first, then text
            parts = thought_parts + clean_parts
        else:
            if content.strip():
                parts = [{"text": content}]
            
        return parts

    def _proto_to_dict(self, obj):
        """Recursively convert Google proto/MapComposite objects to standard Python dicts/lists"""
        if hasattr(obj, "items"):
            return {k: self._proto_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._proto_to_dict(x) for x in obj]
        elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            try:
                return [self._proto_to_dict(x) for x in obj]
            except:
                return obj
        return obj

    def get_available_models(self) -> List[str]:
        return [
            "gemini-2.0-flash-thinking-exp-1219",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash", 
            "gemini-1.5-pro", 
            "gemini-pro", 
            "gemini-pro-vision"
        ]



class AnthropicProvider(AIProvider):
    """Anthropic provider implementation"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise ImportError(
                "Anthropic library not installed. Run: pip install anthropic"
            )

    async def generate_response(
        self, messages: List[Dict], model: str = "claude-3-sonnet-20240229", **kwargs
    ) -> str:
        try:
            system_message = ""
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)

            response = await self.client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
                system=system_message,
                messages=user_messages,
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    async def generate_response_stream(
        self, messages: List[Dict], model: str = "claude-3-sonnet-20240229", **kwargs
    ):
        """Generate streaming response"""
        try:
            system_message = ""
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)

            async with self.client.messages.stream(
                model=model,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
                system=system_message,
                messages=user_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise Exception(f"Anthropic API streaming error: {str(e)}")

    def get_available_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]


class TogetherProvider(AIProvider):
    """Together AI provider implementation"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import together

            self.client = together.AsyncTogether(api_key=api_key)
        except ImportError:
            raise ImportError(
                "Together library not installed. Run: pip install together"
            )

    async def generate_response(
        self,
        messages: List[Dict],
        model: str = "meta-llama/Llama-2-70b-chat-hf",
        **kwargs,
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Together API error: {str(e)}")

    async def generate_response_stream(
        self,
        messages: List[Dict],
        model: str = "meta-llama/Llama-2-70b-chat-hf",
        **kwargs,
    ):
        """Generate streaming response"""
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"Together API streaming error: {str(e)}")

    def get_available_models(self) -> List[str]:
        return [
            "meta-llama/Llama-2-70b-chat-hf",
            "meta-llama/Llama-2-13b-chat-hf",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
        ]


class OpenRouterProvider(AIProvider):
    """OpenRouter provider implementation"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import openai

            self.client = openai.AsyncOpenAI(
                api_key=api_key, base_url="https://openrouter.ai/api/v1"
            )
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")

    async def generate_response(
        self, messages: List[Dict], model: str = "anthropic/claude-3-sonnet", **kwargs
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenRouter API error: {str(e)}")

    async def generate_response_stream(
        self, messages: List[Dict], model: str = "anthropic/claude-3-sonnet", **kwargs
    ):
        """Generate streaming response"""
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"OpenRouter API streaming error: {str(e)}")

    def get_available_models(self) -> List[str]:
        return [
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "openai/gpt-4-turbo",
            "meta-llama/llama-3-70b-instruct",
        ]


class LocalModelProvider(AIProvider):
    """Local model provider for both Hugging Face and GGUF models"""

    def __init__(self, model_path: str):
        super().__init__(api_key="local")  # No API key needed for local models
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = None
        self.is_gguf = model_path.endswith(".gguf")
        self.n_ctx = 2048  # Will be set during model loading
        self._load_model()

    def _load_model(self):
        """Load the local model (Hugging Face or GGUF)"""
        if self.is_gguf:
            self._load_gguf_model()
        else:
            self._load_hf_model()

    def _load_gguf_model(self):
        """Load a GGUF quantized model using llama-cpp-python"""
        try:
            import os

            from llama_cpp import Llama

            print(f"Loading GGUF model from {self.model_path}...")

            # Get optimal thread count (use all available cores)
            n_threads = os.cpu_count() or 4

            # Try to load model metadata to get optimal context size
            try:
                # Load with minimal context first to read metadata
                temp_model = Llama(model_path=self.model_path, n_ctx=512, verbose=False)
                # Get model's training context (if available)
                model_metadata = temp_model.metadata
                n_ctx_train = (
                    model_metadata.get("n_ctx_train", 2048)
                    if hasattr(temp_model, "metadata")
                    else 2048
                )
                del temp_model

                # Use smaller of: training context or 4096 (for performance)
                self.n_ctx = min(n_ctx_train, 4096) if n_ctx_train > 0 else 2048
            except:
                # Fallback to 2048 if metadata reading fails
                self.n_ctx = 2048

            print(f"Using context window: {self.n_ctx} tokens")

            # Load model with optimal context
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,  # Auto-detected context window
                n_threads=n_threads,  # Use all CPU threads
                n_gpu_layers=0,  # 0 for CPU, increase for GPU
                n_batch=512,  # Batch size for prompt processing
                verbose=False,
            )
            self.device = "cpu"
            print(
                f"SUCCESS: GGUF model loaded successfully on {self.device} ({n_threads} threads)"
            )

        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed. For GGUF models, run:\n"
                "  pip install llama-cpp-python\n"
                "Or for GPU support:\n"
                '  CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python'
            )
        except Exception as e:
            raise Exception(f"Failed to load GGUF model: {str(e)}")

    def _load_hf_model(self):
        """Load a Hugging Face transformers model"""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Determine device
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"

            print(f"Loading local model from {self.model_path} on {self.device}...")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

            # Load model with appropriate settings
            if self.device == "cuda":
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True,
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path, torch_dtype=torch.float32
                )
                self.model.to(self.device)

            print(f"SUCCESS: Model loaded successfully on {self.device}")

        except ImportError:
            raise ImportError(
                "Transformers and PyTorch not installed. Run: pip install transformers torch accelerate"
            )
        except Exception as e:
            raise Exception(f"Failed to load local model: {str(e)}")

    async def generate_response(
        self, messages: List[Dict], model: str = None, **kwargs
    ) -> str:
        """Generate response from the local model"""
        if self.is_gguf:
            return await self._generate_gguf_response(messages, **kwargs)
        else:
            return await self._generate_hf_response(messages, **kwargs)

    async def _generate_gguf_response(self, messages: List[Dict], **kwargs) -> str:
        """Generate response using GGUF model"""
        try:
            # Truncate messages if needed to fit context window
            max_tokens = kwargs.get("max_tokens", 256)  # Reduced for faster response
            temperature = kwargs.get("temperature", 0.7)

            # Use actual context window size with safety margin
            # Reserve space for: response (max_tokens) + safety buffer (200)
            available_context = self.n_ctx - max_tokens - 200

            # Estimate tokens more conservatively (1 token ≈ 3 characters for safety)
            max_prompt_chars = available_context * 3

            # Truncate messages to fit
            truncated_messages = self._truncate_messages(messages, max_prompt_chars)

            # Convert messages to prompt
            prompt = self._messages_to_prompt(truncated_messages)

            # Double-check prompt length (rough token estimate)
            estimated_prompt_tokens = len(prompt) // 3
            if estimated_prompt_tokens + max_tokens > self.n_ctx:
                # Emergency truncation - keep only last message
                truncated_messages = messages[-1:] if messages else []
                prompt = self._messages_to_prompt(truncated_messages)

            # Generate response with optimized settings
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
                top_k=40,
                repeat_penalty=1.1,
                echo=False,  # Don't echo the prompt
                stop=["User:", "System:", "\n\n"],  # Stop tokens
            )

            # Extract text from response
            if isinstance(response, dict) and "choices" in response:
                return response["choices"][0]["text"].strip()
            return str(response).strip()

        except Exception as e:
            raise Exception(f"GGUF model generation error: {str(e)}")

    async def _generate_hf_response(self, messages: List[Dict], **kwargs) -> str:
        """Generate response using Hugging Face model"""
        try:
            import torch

            # Convert messages to a single prompt
            prompt = self._messages_to_prompt(messages)

            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            # Generate response
            max_tokens = kwargs.get("max_tokens", 2048)
            temperature = kwargs.get("temperature", 0.7)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Remove the prompt from the response
            if response.startswith(prompt):
                response = response[len(prompt) :].strip()

            return response

        except Exception as e:
            raise Exception(f"Local model generation error: {str(e)}")

    def _truncate_messages(self, messages: List[Dict], max_chars: int) -> List[Dict]:
        """Truncate messages to fit within character limit"""
        # Always keep system message if present
        system_msgs = [m for m in messages if m["role"] == "system"]
        other_msgs = [m for m in messages if m["role"] != "system"]

        # Estimate current size
        total_chars = sum(len(m["content"]) for m in messages)

        if total_chars <= max_chars:
            return messages

        # Keep system message and recent messages
        result = system_msgs.copy()
        current_chars = sum(len(m["content"]) for m in system_msgs)

        # Add messages from most recent backwards
        for msg in reversed(other_msgs):
            msg_chars = len(msg["content"])
            if current_chars + msg_chars <= max_chars:
                result.insert(len(system_msgs), msg)
                current_chars += msg_chars
            else:
                break

        return result

    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert message format to a prompt string"""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"

        # Add final assistant prompt
        prompt += "Assistant: "
        return prompt

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return [self.model_path]


class AIEngine:
    """Main AI engine that manages providers and handles requests"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.tool_registry = ToolRegistry()
        self.providers = {}
        self.local_model_provider = None  # Track local model separately
        self.auto_continuation = AutoContinuationManager(max_iterations=50)
        # Give AI engine unrestricted permissions
        from .tools.base import PermissionLevel

        self.tool_registry.set_permission_level(
            "ai_engine", PermissionLevel.UNRESTRICTED
        )
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available AI providers"""
        # Get all supported providers from endpoints
        all_providers = get_all_providers()

        # Legacy provider classes for backward compatibility
        legacy_provider_classes = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "google": GoogleProvider,
            "together": TogetherProvider,
            "openrouter": OpenRouterProvider,
        }

        for provider_name in all_providers:
            provider_cfg = get_provider_config(provider_name)
            requires_key = not provider_cfg.get("no_auth", False)
            api_key = self.config_manager.get_api_key(provider_name)
            base_url_override = self.config_manager.get_provider_endpoint(provider_name)

            if requires_key and not api_key:
                continue

            try:
                # Use legacy provider if available, otherwise use generic provider
                if provider_name in legacy_provider_classes:
                    self.providers[provider_name] = legacy_provider_classes[
                        provider_name
                    ](api_key)
                else:
                    self.providers[provider_name] = GenericProvider(
                        api_key or "", provider_name, base_url_override
                    )
            except Exception as e:
                print(f"Warning: Could not initialize {provider_name}: {e}")

        # Don't auto-load local model at startup - only load when explicitly requested
        # This prevents unnecessary loading and error messages when not using local provider

    def load_local_model(self, model_path: str):
        """Load a local Hugging Face model"""
        try:
            self.local_model_provider = LocalModelProvider(model_path)
            self.providers["local"] = self.local_model_provider
            self.config_manager.set_config("local_model_path", model_path)
            return True
        except Exception as e:
            raise Exception(f"Failed to load local model: {str(e)}")

    def unload_local_model(self):
        """Unload the local model and free memory"""
        if "local" in self.providers:
            del self.providers["local"]
        self.local_model_provider = None
        self.config_manager.delete_config("local_model_path")

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())

    def get_all_tool_schemas(self) -> List[Dict]:
        """Get schemas for all registered tools"""
        # Return only the 'schema' part for each tool
        return [tool.get_schema() for tool in self.tool_registry.tools.values()]

    def get_provider_models(self, provider: str) -> List[str]:
        """Get available models for a provider"""
        if provider in self.providers:
            return self.providers[provider].get_available_models()
        return []

    async def process_message(
        self,
        message: str,
        provider: str = None,
        model: str = None,
        project_path: str = None,
        context: List[Dict] = None,
        conversation_history: List[Dict] = None,
    ) -> str:
        """Process a user message and generate AI response"""

        # Use default provider if not specified
        if not provider:
            provider = self.config_manager.get_config_value("default_provider")

        if provider not in self.providers:
            raise Exception(
                f"Provider '{provider}' not available. Available: {list(self.providers.keys())}"
            )

        # Build message context
        messages = []

        # Add system message (full system prompt for all providers)
        system_prompt = self._build_system_prompt(project_path)
        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history if provided (no trimming specific to Ollama)
        if conversation_history:
            messages.extend(conversation_history)

        # Add context if provided (include for all providers)
        if context:
            messages.extend(context)

        # Add current user message
        messages.append({"role": "user", "content": message})

        # Get AI response
        ai_provider = self.providers[provider]

        # Use default model if not specified
        if not model:
            available_models = ai_provider.get_available_models()
            if provider == "google":
                model = (
                    available_models[0] if available_models else "gemini-1.5-flash"
                )  # Use newer model
            else:
                model = available_models[0] if available_models else None

        # Get all tool schemas for native tool calling
        tools = self.get_all_tool_schemas()

        config = self.config_manager.get_config()
        # Use unlimited tokens (or max available for the model)
        max_tokens = config.get("max_tokens", None)  # None = unlimited
        if max_tokens == 0 or max_tokens == -1:
            max_tokens = None  # Treat 0 or -1 as unlimited

        response = await ai_provider.generate_response(
            messages=messages,
            model=model,
            tools=tools,
            max_tokens=max_tokens or 16384,  # Use large default if None
            temperature=config.get("temperature", 0.7),
        )

        # Check if response contains tool calls (either string or dict)
        has_tools = False
        if isinstance(response, dict) and "tool_calls" in response:
            has_tools = True
        elif isinstance(response, str):
            has_tools = self._contains_tool_calls(response)

        if has_tools:
            # Recursion logic handled inside _process_response_with_tools
            # We convert generator to string for non-streaming process_message
            full_response = ""
            async for chunk in self._process_response_with_tools(
                response, project_path, messages, ai_provider, model, config
            ):
                if isinstance(chunk, str):
                    full_response += chunk
            return full_response

        return response if isinstance(response, str) else response.get("content", "")

    async def process_message_stream(
        self,
        message: str,
        provider: str = None,
        model: str = None,
        project_path: str = None,
        context: List[Dict] = None,
        conversation_history: List[Dict] = None,
        confirmation_manager = None,
        memory_manager = None,
    ):
        """Process a user message and generate streaming AI response"""

        # Reset auto-continuation counter for new message
        self.auto_continuation.reset()

        # Use default provider if not specified
        if not provider:
            provider = self.config_manager.get_config_value("default_provider")

        if provider not in self.providers:
            raise Exception(
                f"Provider '{provider}' not available. Available: {list(self.providers.keys())}"
            )

        # No file tagging - use message as-is
        processed_message = message

        # Build message context
        messages = []

        # Add system message (full prompt for all providers)
        system_prompt = self._build_system_prompt(project_path)
        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history if provided (no special trimming)
        if conversation_history:
            messages.extend(conversation_history)

        # Add context if provided (include for all providers)
        if context:
            messages.extend(context)

        # Add current user message
        messages.append({"role": "user", "content": processed_message})

        # Get AI response
        ai_provider = self.providers[provider]

        # Use default model if not specified
        if not model:
            available_models = ai_provider.get_available_models()
            if provider == "google":
                model = (
                    available_models[0] if available_models else "gemini-1.5-flash"
                )  # Use newer model
            else:
                model = available_models[0] if available_models else None

        config = self.config_manager.get_config()

        # Use unlimited tokens (or max available for the model)
        max_tokens = config.get("max_tokens", None)  # None = unlimited
        if max_tokens == 0 or max_tokens == -1:
            max_tokens = None  # Treat 0 or -1 as unlimited

        async for chunk in self._stream_with_live_tools(
            ai_provider=ai_provider,
            messages=messages,
            model=model,
            max_tokens=max_tokens or 16384,
            config=config,
            project_path=project_path,
            confirmation_manager=confirmation_manager,
            memory_manager=memory_manager,
            recursion_depth=0,
        ):
            yield chunk

    async def _stream_with_live_tools(
        self,
        ai_provider,
        messages: list,
        model: str,
        max_tokens: int,
        config: dict,
        project_path: str,
        confirmation_manager = None,
        memory_manager = None,
        recursion_depth: int = 0,
    ):
        """Stream AI response with native tool support and automatic continuation"""
        import json
        import re

        # Prevent infinite recursion
        MAX_RECURSION_DEPTH = 50
        if recursion_depth >= MAX_RECURSION_DEPTH:
            yield "\n**WARNING:** Maximum continuation depth reached.\n"
            return

        # Get all tool schemas for native tool calling
        tools = self.get_all_tool_schemas()
        
        # Buffer to accumulate text and tool calls
        text_buffer = ""
        current_tool_calls = []
        has_executed_tools = False
        tool_results = []
        # Total response for this turn (excluding previous turns in recursion)
        turn_response = ""
        # Buffers for streaming tool call suppression
        json_mode = False
        json_buffer = ""
        already_executed_calls = [] # List of (name, args_json) to avoid duplicates

        # Stream the response
        try:
            async for chunk in ai_provider.generate_response_stream(
                messages=messages,
                model=model,
                tools=tools,
                max_tokens=max_tokens or 16384,
                temperature=config.get("temperature", 0.7),
            ):
                if not chunk:
                    continue

                if isinstance(chunk, dict) and "tool_calls" in chunk:
                    # Native tool call detected in stream
                    for tc in chunk["tool_calls"]:
                        current_tool_calls.append(tc)
                elif isinstance(chunk, str):
                    # Robust streaming suppression for manual JSON tool calls
                    text_buffer += chunk
                    turn_response += chunk
                    
                    if not json_mode:
                        if "```json" in chunk:
                            # Start of a potential tool call
                            start_idx = chunk.find("```json")
                            # Yield text before the block
                            if start_idx > 0:
                                yield chunk[:start_idx]
                            
                            json_mode = True
                            json_buffer = chunk[start_idx:]
                        else:
                            # Normal text, just yield
                            yield chunk
                    else:
                        # We are currently buffering a potential tool call
                        json_buffer += chunk
                        
                        if "```" in chunk[chunk.find("```") + 3:] or (chunk.strip().endswith("```") and "```json" not in chunk):
                            # End of the block
                            end_idx = json_buffer.rfind("```")
                            full_block = json_buffer
                            
                            # Check if the closed block looks like a tool call
                            if "\"tool_code\"" in full_block:
                                # It's a tool call! Suppress it from UI output.
                                # Execute it ASAP to improve user experience
                                try:
                                    # Extract JSON from inside the block
                                    json_text_match = re.search(r"```json\s*\n?(.*?)\n?```", full_block, re.DOTALL)
                                    if json_text_match:
                                        tc_data = json.loads(json_text_match.group(1).strip())
                                        tc_name = tc_data.get("tool_code")
                                        tc_args_dict = tc_data.get("args", {})
                                        tc_args_json = json.dumps(tc_args_dict)
                                        
                                        # Execute if not already done
                                        if (tc_name, tc_args_json) not in already_executed_calls:
                                            # Yield some status and execute
                                            yield f"\n[Executing {tc_name}...]\n"
                                            
                                            async for tool_ui_output in self._execute_single_tool_live(
                                                {"tool_code": tc_name, "args": tc_args_dict}, 
                                                project_path, 
                                                tool_results, 
                                                confirmation_manager
                                            ):
                                                yield tool_ui_output
                                            
                                            already_executed_calls.append((tc_name, tc_args_json))
                                            has_executed_tools = True
                                            
                                            # Special handling: if it was response_control end_response,
                                            # we might want to flag it here.
                                            if tc_name == "response_control" and tc_args_dict.get("operation") == "end_response":
                                                has_end_response = True
                                except Exception as e:
                                    # If parsing/execution fails mid-stream, we'll let the final loop try again
                                    pass
                            else:
                                # Not a tool call, flush the buffer to user
                                yield full_block
                            
                            json_mode = False
                            json_buffer = ""
                            
                            # Handle any text after the closing backticks in the same chunk
                            # (Though usually chunks end at boundaries, let's be safe)
                            closing_match = re.search(r"```(?!json)(.*)", chunk, re.DOTALL)
                            if closing_match:
                                remaining = closing_match.group(1)
                                if remaining.strip():
                                    yield remaining
                else:
                    # Generic chunk handling
                    yield str(chunk)

            # After stream ends, check if we have tool calls to execute
            # Combine native tool calls and manual ones from the text buffer
            final_tool_calls = current_tool_calls.copy()
            
            # Extract manual tool calls from text_buffer
            manual_matches = []
            manual_matches.extend(re.findall(r"```json\s*\n?(.*?)\n?```", text_buffer, re.DOTALL))
            if not manual_matches:
                 manual_matches.extend(re.findall(r"({[^{]*\"tool_code\"[^{]*})", text_buffer, re.DOTALL))

            for match in manual_matches:
                try:
                    tc_data = json.loads(match.strip())
                    if "tool_code" in tc_data:
                        # Normalize to native format
                        tc_name = tc_data.get("tool_code")
                        tc_args = json.dumps(tc_data.get("args", {}))
                        
                        # Avoid duplicates if it's already in current_tool_calls
                        is_dup = any(c.get("function", {}).get("name") == tc_name and 
                                     c.get("function", {}).get("arguments") == tc_args 
                                     for c in current_tool_calls)
                        
                        if not is_dup:
                            final_tool_calls.append({
                                "type": "function",
                                "function": {
                                    "name": tc_name,
                                    "arguments": tc_args
                                }
                            })
                except: continue

            if final_tool_calls:
                # CRITICAL: Record the assistant's intent. 
                # For Gemini, the next message MUST respond to EVERY tool_call listed here.
                assistant_msg = {"role": "assistant", "content": text_buffer}
                assistant_msg["tool_calls"] = final_tool_calls
                
                # Propagate thought_signature if available
                thought_sig = None
                for tc in final_tool_calls:
                    if tc.get("thought_signature"):
                        thought_sig = tc["thought_signature"]
                        break
                
                if thought_sig:
                    assistant_msg["thought_signature"] = thought_sig
                    # Attach signature back to all calls for consistency in the message history
                    for tc in final_tool_calls:
                        tc["thought_signature"] = thought_sig

                messages.append(assistant_msg)
                
                # Save to persistent memory
                if memory_manager:
                    metadata = {"tool_calls": final_tool_calls}
                    if thought_sig:
                        metadata["thought_signature"] = thought_sig
                    memory_manager.add_message("assistant", turn_response, metadata=metadata)

                # Execute all tool calls that haven't been executed yet
                for tc in final_tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name")
                    try:
                        args_json = func.get("arguments", "{}")
                        args = json.loads(args_json) if isinstance(args_json, str) else args_json
                        args_json_str = json.dumps(args)
                    except:
                        args = {}
                        args_json_str = "{}"
                    
                    # Avoid double execution
                    if (tool_name, args_json_str) in already_executed_calls:
                        # But we still need to add to messages for history!
                        # The tool_results list already has the data from eager execution.
                        # We just need to find it to build the tool_msg.
                        # tool_results is shared so it's all there.
                        pass
                    else:
                        # Execute now
                        async for tool_ui_output in self._execute_single_tool_live(
                            {"tool_code": tool_name, "args": args}, 
                            project_path, 
                            tool_results, 
                            confirmation_manager
                        ):
                            yield tool_ui_output
                        already_executed_calls.append((tool_name, args_json_str))
                    
                    # ALWAYS add tool result to message history for Gemini consistency
                    # Find matching result
                    last_result = {"success": False, "error": "Result missing"}
                    # We might have many results, try to match by tool name at least
                    for r in reversed(tool_results):
                         if r.get("tool") == tool_name or r.get("type") == tool_name:
                             last_result = r
                             break

                    tool_msg = {
                        "role": "tool",
                        "name": tool_name,
                        "tool_call_id": tc.get("id", tool_name),
                        "content": json.dumps(last_result)
                    }
                    messages.append(tool_msg)
                    
                    if memory_manager:
                        memory_manager.add_message("tool", tool_msg["content"], metadata={
                            "name": tool_name,
                            "tool_call_id": tool_msg["tool_call_id"]
                        })
                    
                    has_executed_tools = True

                # Check if we should stop (e.g. response_control end_response)
                has_end_response = any(
                    r.get("type") == "control" and r.get("message") == "end_response"
                    for r in tool_results
                )

                if has_end_response:
                    return

                # RECURSIVE CONTINUATION
                # Remove manual continuation prompts entirely.
                # Just call itself again with updated history.
                async for chunk in self._stream_with_live_tools(
                    ai_provider,
                    messages,
                    model,
                    max_tokens,
                    config,
                    project_path,
                    confirmation_manager,
                    memory_manager,
                    recursion_depth + 1
                ):
                    yield chunk
            else:
                # No more tools, this is the final final response part of the turn
                if memory_manager and turn_response:
                    memory_manager.add_message("assistant", turn_response)
            
        except Exception as e:
            import traceback
            yield f"\n[Error in stream: {str(e)}]\n"
            yield f"\n[Traceback]\n{traceback.format_exc()}\n"

    def _format_tool_box(self, title: str, content_lines: list, width: int = 65) -> str:
        """Format a tool execution box with proper alignment"""
        import re

        # Top border
        box = f"\n\n╔{'═' * (width - 2)}╗\n"
        # Title - truncate if too long
        if len(title) > width - 4:
            title = title[: width - 7] + "..."
        box += f"║ {title:<{width - 4}} ║\n"
        # Separator if there's content
        if content_lines:
            box += f"╠{'═' * (width - 2)}╣\n"
            # Content lines
            for line in content_lines:
                # Remove ANSI codes for length calculation
                clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line)
                display_len = len(clean_line)
                # Truncate line if too long
                if display_len > width - 4:
                    # Keep ANSI codes but truncate visible text
                    visible_len = 0
                    truncated = ""
                    in_ansi = False
                    for char in line:
                        if char == "\x1b":
                            in_ansi = True
                        if in_ansi:
                            truncated += char
                            if char == "m":
                                in_ansi = False
                        else:
                            if visible_len < width - 7:
                                truncated += char
                                visible_len += 1
                            elif visible_len == width - 7:
                                truncated += "..."
                                visible_len += 3
                                break
                    line = truncated
                    clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line)
                    display_len = len(clean_line)

                padding = width - 4 - display_len
                box += f"║ {line}{' ' * max(0, padding)} ║\n"
        # Bottom border
        box += f"╚{'═' * (width - 2)}╝\n\n"
        return box

    async def _execute_single_tool_live(
        self, tool_call: dict, project_path: str, tool_results: list, confirmation_manager = None
    ):
        """Execute a single tool call and yield the result immediately"""
        import json
        
        try:
            tool_name = tool_call.get("tool_code")
            args = tool_call.get("args", {})

            # Check for response control tool
            if tool_name == "response_control":
                operation = args.get("operation", "end_response")
                if operation == "end_response":
                    box = self._format_tool_box("Response Completed", [])
                    yield box
                    tool_results.append({"type": "control", "message": "end_response"})
                return
            
            # Check for ask_question tool - special handling
            if tool_name == "ask_question":
                # Execute the ask_question tool
                result = await self.tool_registry.execute_tool(
                    "ask_question", user_id="ai_engine", **args
                )
                
                if result.success:
                    # Extract the answer
                    answer = result.data.get("answer", "") if isinstance(result.data, dict) else ""
                    
                    # Display the tool result
                    content = [
                        f"Tool: {tool_name}",
                        "",
                        "Result:",
                        json.dumps(result.data, indent=2) if isinstance(result.data, dict) else str(result.data)
                    ]
                    box = self._format_tool_box(f"TOOL: {tool_name}", content)
                    yield box
                    
                    # Add to tool results with special marker for continuation
                    tool_results.append({
                        "type": "ask_question",
                        "tool": "ask_question",
                        "data": result.data,
                        "answer": answer,
                        "success": True
                    })
                else:
                    content = [str(result.error)]
                    box = self._format_tool_box(f"ERROR: {tool_name}", content)
                    yield box
                    tool_results.append(
                        {"type": "error", "error": result.error, "success": False}
                    )
                return

            # Execute the tool (reuse existing tool execution logic)
            if tool_name == "command_runner":
                # Ask for confirmation if not in YOLO mode
                if confirmation_manager and not confirmation_manager.is_yolo_mode():
                    cmd_args = args.copy()
                    if "operation" not in cmd_args:
                        cmd_args["operation"] = "run_command"
                    if "cwd" not in cmd_args:
                        cmd_args["cwd"] = project_path or "."
                    
                    confirmed = await confirmation_manager.confirm_operation("command_runner", cmd_args)
                    if not confirmed:
                        # User cancelled the operation
                        content = ["Operation cancelled by user"]
                        box = self._format_tool_box("CANCELLED: command_runner", content)
                        yield box
                        tool_results.append({"type": "cancelled", "tool": "command_runner", "success": False})
                        return
                cmd_args = args.copy()
                if "operation" not in cmd_args:
                    cmd_args["operation"] = "run_command"
                if "cwd" not in cmd_args:
                    cmd_args["cwd"] = project_path or "."

                result = await self.tool_registry.execute_tool(
                    "command_runner", user_id="ai_engine", **cmd_args
                )

                if result.success:
                    command = args.get("command", "unknown")
                    operation = cmd_args.get("operation", "run_command")

                    if operation == "run_async_command":
                        process_id = result.data.get("process_id", "unknown")
                        pid = result.data.get("pid", "unknown")
                        content = [
                            f"Command: {command}",
                            f"Status:  Running in background",
                            f"Process: {process_id} (PID: {pid})",
                            f"Tip:     Use /ct {process_id} to terminate",
                        ]
                        box = self._format_tool_box(
                            "TOOL: command_runner (background)", content
                        )
                        yield box
                        tool_results.append(
                            {"type": "command", "command": command, "success": True}
                        )
                    else:
                        stdout = (
                            result.data.get("stdout", "")
                            if isinstance(result.data, dict)
                            else str(result.data)
                        )
                        stderr = (
                            result.data.get("stderr", "")
                            if isinstance(result.data, dict)
                            else ""
                        )

                        full_output = stdout
                        if stderr and stderr.strip():
                            full_output += f"\n[stderr]\n{stderr}"

                        display_output = full_output
                        if len(full_output) > 10000:
                            display_output = (
                                full_output[:10000] + f"\n\n... [Output truncated]"
                            )

                        # Show output preview in the box
                        content = [f"Command: {command}", "", "Output:"]
                        # Add first few lines of output to box
                        output_lines = display_output.split("\n")[:10]
                        for line in output_lines:
                            content.append(line[:57])  # Truncate long lines
                        if len(display_output.split("\n")) > 10:
                            content.append("...")

                        box = self._format_tool_box("TOOL: command_runner", content)
                        yield box

                        # Add to tool results with output for continuation
                        tool_results.append(
                            {
                                "type": "command",
                                "command": command,
                                "output": full_output,
                                "success": True,
                            }
                        )
                else:
                    content = [str(result.error)]
                    box = self._format_tool_box("ERROR: command_runner", content)
                    yield box
                    tool_results.append(
                        {"type": "error", "error": result.error, "success": False}
                    )

            elif tool_name == "file_operations":
                file_path = args.get("file_path")
                dir_path = args.get("dir_path")
                target_path = file_path or dir_path
                
                if target_path and project_path:
                    from pathlib import Path

                    path = Path(target_path)
                    if not path.is_absolute():
                        resolved_path = str(Path(project_path) / target_path)
                        if file_path:
                            args["file_path"] = resolved_path
                        if dir_path:
                            args["dir_path"] = resolved_path
                
                # Ask for confirmation if not in YOLO mode (skip for read operations)
                operation = args.get("operation")
                if confirmation_manager and not confirmation_manager.is_yolo_mode():
                    # Only confirm write/modify/delete operations, not reads
                    if operation not in ["read_file", "read_file_lines", "list_directory"]:
                        confirmed = await confirmation_manager.confirm_operation("file_operations", args)
                        if not confirmed:
                            # User cancelled the operation
                            content = ["Operation cancelled by user"]
                            box = self._format_tool_box("CANCELLED: file_operations", content)
                            yield box
                            tool_results.append({"type": "cancelled", "tool": "file_operations", "success": False})
                            return

                result = await self.tool_registry.execute_tool(
                    "file_operations", user_id="ai_engine", **args
                )

                if result.success:
                    operation = args.get("operation")
                    file_path = args.get("file_path")
                    
                    # Check if this is a read operation
                    if operation in ["read_file", "read_file_lines"]:
                        # Extract file content
                        file_content = (
                            result.data.get("content", "")
                            if isinstance(result.data, dict)
                            else str(result.data)
                        )
                        
                        # Build tool box with content preview
                        content = [f"Operation: {operation}", f"File:      {file_path}"]
                        if file_content.strip():
                            content.append("")
                            content.append("Content Preview:")
                            content_lines = file_content.split("\n")[:10]
                            for line in content_lines:
                                truncated_line = line[:57]
                                content.append(truncated_line)
                            if len(file_content.split("\n")) > 10:
                                content.append("...")
                        
                        box = self._format_tool_box("TOOL: file_operations", content)
                        yield box
                        
                        # Add to tool_results with FULL content for continuation
                        tool_results.append({
                            "type": "file_read",
                            "file_path": file_path,
                            "content": file_content,
                            "success": True,
                        })
                    else:
                        # Other operations (write, create, etc.)
                        content = [f"Operation: {operation}", f"File:      {file_path}"]

                        # Show diff for write/edit operations inside the box
                        if isinstance(result.data, dict):
                            old_content = result.data.get("old_content")
                            new_content = result.data.get("new_content")
                            if old_content is not None and new_content is not None:
                                # Generate unified diff
                                import difflib

                                old_lines = old_content.splitlines(keepends=True)
                                new_lines = new_content.splitlines(keepends=True)
                                diff = difflib.unified_diff(
                                    old_lines,
                                    new_lines,
                                    lineterm="",
                                    fromfile="before",
                                    tofile="after",
                                    n=3,
                                )

                                content.append("")
                                content.append("Diff:")
                                for line in diff:
                                    line = line.rstrip()
                                    # Skip file markers
                                    if line.startswith("---") or line.startswith("+++"):
                                        continue
                                    # Only show + and - signs for diff lines, no colors
                                    content.append(line)

                        box = self._format_tool_box("TOOL: file_operations", content)
                        yield box

                        # Add to tool results
                        result_info = {
                            "type": "file_op",
                            "operation": operation,
                            "file_path": file_path,
                            "success": True,
                        }
                        if isinstance(result.data, dict) and "old_content" in result.data:
                            result_info["modified"] = True
                        tool_results.append(result_info)
                else:
                    content = [str(result.error)]
                    box = self._format_tool_box("ERROR: file_operations", content)
                    yield box
                    tool_results.append(
                        {"type": "error", "error": result.error, "success": False}
                    )

            elif tool_name == "web_search":
                result = await self.tool_registry.execute_tool(
                    "web_search", user_id="ai_engine", **args
                )

                if result.success:
                    operation = args.get("operation", "search_web")
                    query = args.get("query", "N/A")
                    
                    # Format for UI
                    content = [f"Operation: {operation}"]
                    if query != "N/A":
                        content.append(f"Query:     {query}")
                    
                    if isinstance(result.data, list):
                        # It's a list of results
                        content.append(f"Found {len(result.data)} results")
                        for i, item in enumerate(result.data[:3]):
                            title = item.get('title', 'No title')
                            content.append(f"{i+1}. {title[:50]}...")
                    elif isinstance(result.data, dict):
                        # It might be fetch_url_content result
                        url = result.data.get('url', 'unknown')
                        content.append(f"URL: {url}")
                        text_len = result.data.get('length', 0)
                        content.append(f"Length: {text_len} chars")
                    
                    box = self._format_tool_box("TOOL: web_search", content)
                    yield box

                    # Add to tool results with FULL results
                    tool_results.append({
                        "type": "web_search",
                        "operation": operation,
                        "query": query,
                        "results": result.data,
                        "success": True
                    })
                else:
                    content = [str(result.error)]
                    box = self._format_tool_box("ERROR: web_search", content)
                    yield box
                    tool_results.append(
                        {"type": "error", "error": result.error, "success": False}
                    )

            elif tool_name == "file_reader":
                result = await self.tool_registry.execute_tool(
                    "file_reader", user_id="ai_engine", **args
                )

                if result.success:
                    operation = args.get("operation")
                    file_path = args.get("file_path", "N/A")

                    # Show file content preview for read operations
                    content = [f"Operation: {operation}", f"File:      {file_path}"]

                    # Add preview of content
                    if isinstance(result.data, dict) and "content" in result.data:
                        file_content = result.data["content"]
                        lines = file_content.split("\n")[:5]  # First 5 lines
                        if lines:
                            content.append("")
                            content.append("Content (first 5 lines):")
                            for line in lines:
                                content.append(line[:57])  # Truncate long lines
                            if len(file_content.split("\n")) > 5:
                                content.append("...")

                    box = self._format_tool_box("TOOL: file_reader", content)
                    yield box

                    # Add to tool results with content for continuation
                    result_info = {
                        "type": "file_read",
                        "operation": operation,
                        "file_path": file_path,
                        "success": True,
                    }
                    if isinstance(result.data, dict) and "content" in result.data:
                        result_info["content_preview"] = result.data["content"][
                            :500
                        ]  # First 500 chars
                    tool_results.append(result_info)
                else:
                    content = [str(result.error)]
                    box = self._format_tool_box("ERROR: file_reader", content)
                    yield box
                    tool_results.append(
                        {"type": "error", "error": result.error, "success": False}
                    )


            else:
                # Generic handler for all other tools (including MCP tools)
                # Check if tool exists in registry
                tool = self.tool_registry.get_tool(tool_name)
                
                if not tool:
                    content = [f"Unknown tool: {tool_name}"]
                    box = self._format_tool_box("ERROR: Unknown Tool", content)
                    yield box
                    tool_results.append(
                        {"type": "error", "error": f"Unknown tool: {tool_name}", "success": False}
                    )
                    return
                
                # Execute tool via registry
                result = await self.tool_registry.execute_tool(
                    tool_name,
                    user_id="ai_engine",
                    **args
                )
                
                if result.success:
                    # Format result data
                    result_data = result.data if result.data is not None else "Operation completed successfully"
                    
                    # Convert result to string if it's not already
                    if isinstance(result_data, dict):
                        import json
                        result_str = json.dumps(result_data, indent=2)
                    elif isinstance(result_data, list):
                        result_str = '\n'.join(str(item) for item in result_data)
                    else:
                        result_str = str(result_data)
                    
                    # Truncate if too long
                    if len(result_str) > 5000:
                        result_str = result_str[:5000] + "\n\n... [Output truncated]"
                    
                    # Create formatted output
                    content = [f"Tool: {tool_name}", "", "Result:"]
                    result_lines = result_str.split('\n')[:20]  # First 20 lines
                    for line in result_lines:
                        content.append(line[:100])  # Truncate long lines
                    if len(result_str.split('\n')) > 20:
                        content.append("...")
                    
                    box = self._format_tool_box(f"TOOL: {tool_name}", content)
                    yield box
                    
                    tool_results.append({
                        "type": "tool",
                        "tool": tool_name,
                        "result": result_str,
                        "success": True
                    })
                else:
                    content = [str(result.error)]
                    box = self._format_tool_box(f"ERROR: {tool_name}", content)
                    yield box
                    tool_results.append(
                        {"type": "error", "error": result.error, "success": False}
                    )

        except Exception as e:
            content = [str(e)]
            box = self._format_tool_box("TOOL ERROR", content)
            yield box
            tool_results.append({"type": "error", "error": str(e), "success": False})

    def _parse_alternative_tool_calls(self, response: str):
        """Parse tool calls from alternative formats (e.g., GPT-OSS with special tokens)"""
        import json
        import re

        tool_calls = []

        # Pattern 1: GPT-OSS format with <|message|> tags containing JSON
        # Example: <|message|>{"command":"ls -la"}<|call|>
        gpt_oss_pattern = r"<\|message\|>(.*?)<\|call\|>"
        gpt_oss_matches = re.findall(gpt_oss_pattern, response, re.DOTALL)

        for match in gpt_oss_matches:
            try:
                # Try to parse as JSON
                data = json.loads(match.strip())

                # Determine tool type based on keys
                if "command" in data:
                    tool_calls.append(
                        {
                            "tool_code": "command_runner",
                            "args": {"command": data["command"]},
                        }
                    )
                elif "operation" in data:
                    tool_calls.append({"tool_code": "file_operations", "args": data})
                else:
                    # Generic tool call
                    tool_calls.append(
                        {"tool_code": data.get("tool_code", "unknown"), "args": data}
                    )
            except json.JSONDecodeError:
                continue

        # Pattern 2: Look for channel indicators with tool names
        # Example: <|channel|>commentary to=command_runner
        channel_pattern = r"<\|channel\|>.*?to=(\w+)"
        channels = re.findall(channel_pattern, response)

        # Match channels with their corresponding messages
        if channels and gpt_oss_matches:
            for i, (channel, match) in enumerate(zip(channels, gpt_oss_matches)):
                if i < len(tool_calls):
                    # Update tool_code based on channel
                    if "command_runner" in channel:
                        tool_calls[i]["tool_code"] = "command_runner"
                    elif (
                        "command_operations" in channel or "file_operations" in channel
                    ):
                        tool_calls[i]["tool_code"] = "file_operations"
                    elif "response_control" in channel:
                        tool_calls[i]["tool_code"] = "response_control"

        return tool_calls

    def _clean_model_syntax(self, text: str) -> str:
        """Remove model-specific syntax tokens from response"""
        import re

        # Remove common model-specific tokens
        patterns = [
            r"<\|start\|>",
            r"<\|end\|>",
            r"<\|channel\|>",
            r"<\|message\|>",
            r"<\|call\|>",
            r"<\|calls\|>",
            r"assistant\s+to=\w+\s+code",
            r"analysis\s+to=\w+\s+code",
            r"<\|[^|]+\|>",  # Any other pipe-delimited tokens
        ]

        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Remove multiple consecutive newlines left by token removal
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # Don't strip during streaming - preserves spaces between chunks
        return cleaned

    async def _process_response_with_tools(
        self,
        response: Any,
        project_path: str,
        messages: list,
        ai_provider,
        model: str,
        config: dict,
        confirmation_manager = None,
        recursion_depth: int = 0,
    ):
        """Process response and execute tools with native tool support and automatic continuation"""
        import json
        import re

        # Prevent infinite recursion
        MAX_RECURSION_DEPTH = 50
        if recursion_depth >= MAX_RECURSION_DEPTH:
            yield "\n**WARNING:** Maximum continuation depth reached.\n"
            return

        # Handle different response formats (string or dict with tool_calls)
        text_content = ""
        final_tool_calls = []

        if isinstance(response, dict):
            text_content = response.get("content", "") or ""
            final_tool_calls = response.get("tool_calls", [])
        else:
            # Fallback for string response (manual JSON blocks)
            text_content = response
            # Find JSON tool calls in the response (standard format)
            json_pattern = r"```json\s*\n(.*?)\n```"
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            # Use alternative format tool calls as fallback
            alt_tool_calls = self._parse_alternative_tool_calls(response)
            
            # Combine standard JSON matches and alternative format tool calls
            for match in matches:
                try:
                    tc = json.loads(match.strip())
                    final_tool_calls.append({
                        "type": "function",
                        "function": {
                            "name": tc.get("tool_code"),
                            "arguments": json.dumps(tc.get("args", {}))
                        }
                    })
                except:
                    continue
            
            for tc in alt_tool_calls:
                final_tool_calls.append({
                    "type": "function",
                    "function": {
                        "name": tc.get("tool_code"),
                        "arguments": json.dumps(tc.get("args", {}))
                    }
                })

        # Yield any text content first
        if text_content.strip():
            yield text_content + "\n"

        if not final_tool_calls:
            return

        # Prepare tool results and history
        tool_results = []
        
        # Add assistant message to history before executing tools
        assistant_msg = {"role": "assistant", "content": text_content}
        if isinstance(response, dict) and "tool_calls" in response:
            assistant_msg["tool_calls"] = response["tool_calls"]
        messages.append(assistant_msg)

        # Execute detected tool calls
        for tc in final_tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name")
            try:
                args = json.loads(func.get("arguments", "{}"))
            except:
                args = {}

            # Execute and show in UI
            async for tool_ui_output in self._execute_single_tool_live(
                {"tool_code": tool_name, "args": args}, 
                project_path, 
                tool_results, 
                confirmation_manager
            ):
                yield tool_ui_output
            
            # Add tool result to message history for AI's next turn
            last_result = tool_results[-1] if tool_results else {"success": False, "error": "Unknown error"}
            
            messages.append({
                "role": "tool",
                "name": tool_name,
                "tool_call_id": tc.get("id", tool_name),
                "content": json.dumps(last_result)
            })

        # Check for end_response tool
        has_end_response = any(
            r.get("type") == "control" and r.get("message") == "end_response"
            for r in tool_results
        )

        if has_end_response:
            return

        # RECURSIVE CONTINUATION
        # Get next response from AI provider
        tools = self.get_all_tool_schemas()
        
        next_response = await ai_provider.generate_response(
            messages=messages,
            model=model,
            tools=tools,
            max_tokens=config.get("max_tokens", 4096) or 16384,
            temperature=config.get("temperature", 0.7),
        )

        # Process next response recursively
        async for chunk in self._process_response_with_tools(
            next_response,
            project_path,
            messages,
            ai_provider,
            model,
            config,
            confirmation_manager,
            recursion_depth + 1
        ):
            yield chunk

    def _execute_tools(self, response: Any, project_path: str):
        """Compatibility wrapper for non-async or legacy calls"""
        return response

    async def _process_tool_calls_stream(
        self, response_text: str, project_path: str = None
    ):
        """Legacy tool call processor (stream)"""
        return


    def _build_system_prompt(self, project_path: str = None) -> str:
        """Build system prompt for the AI"""

        # Load user-defined rules FIRST (highest priority)
        from .rules import RulesManager

        rules_manager = RulesManager()
        rules_text = rules_manager.get_rules_for_ai(project_path)

        prompt = ""

        # Add rules at the very beginning if they exist
        if rules_text:
            prompt += "=" * 80 + "\n"
            prompt += (
                "USER-DEFINED RULES (HIGHEST PRIORITY - MUST FOLLOW ABOVE ALL ELSE):\n"
            )
            prompt += "=" * 80 + "\n"
            prompt += rules_text + "\n"
            prompt += "=" * 80 + "\n"
            prompt += (
                "These rules OVERRIDE all other instructions. Follow them strictly.\n"
            )
            prompt += "=" * 80 + "\n\n"

        prompt += """You are Cognautic, an advanced AI coding assistant running inside the Cognautic CLI.

IMPORTANT: You are operating within the Cognautic CLI environment. You can ONLY use the tools provided below. Do NOT suggest using external tools, IDEs, or commands that are not available in this CLI.

Most Important Instruction:
If the project is looking HARD, then perform a web search about the project or topic you’re going to work on.

Your capabilities within Cognautic CLI:
1. Code analysis and review
2. Project building and scaffolding
3. Debugging and troubleshooting
4. Documentation generation
5. Best practices and optimization

CRITICAL BEHAVIOR REQUIREMENTS:
- COMPLETE ENTIRE REQUESTS IN ONE RESPONSE: When a user asks you to build, create, or develop something, you must complete the ENTIRE task in a single response, not just one step at a time.
- CREATE ALL NECESSARY FILES: If building a project (like a Pomodoro clock, web app, etc.), create ALL required files (HTML, CSS, JavaScript, etc.) in one go.
- PROVIDE COMPREHENSIVE SOLUTIONS: Don't stop after creating just one file - complete the entire functional project.
- BE PROACTIVE: Anticipate what files and functionality are needed and create them all without asking for permission for each step.
- EXPLORATION IS OPTIONAL: You may explore the workspace with 'ls' or 'pwd' if needed, but this is NOT required before creating new files. If the user asks you to BUILD or CREATE something, prioritize creating the files immediately.
- ALWAYS USE end_response TOOL: When you have completed ALL tasks, you MUST call the end_response tool to signal completion. This prevents unnecessary auto-continuation.
- AUTO-CONTINUATION: The system will automatically continue ONLY when:
  * You created files but haven't run necessary commands yet (e.g., npm install after creating package.json)
  * There were errors that need to be handled
  * Otherwise, you MUST explicitly call end_response when done
- NEVER RE-READ SAME FILE: If a file was truncated in the output, use read_file_lines to read the specific truncated section, DO NOT re-read the entire file
- Never you ever return a empty response
- Use end response tool ONLY when the task is done

WORKSPACE EXPLORATION RULES (CRITICAL - ALWAYS CHECK FIRST):
- ALWAYS start by listing directory contents to see what files exist in the current directory
  * On Linux/Mac: Use 'ls' or 'ls -la' for detailed listing
  * On Windows: Use 'dir' or 'dir /a' for detailed listing
- NEVER assume a project doesn't exist - ALWAYS check first by listing directory
- When user mentions a project/app name (e.g., "cymox", "app", etc.), assume it EXISTS and check for it
- When asked to ADD/MODIFY features: FIRST list directory to find existing files, then read and modify them
- When asked to BUILD/CREATE NEW projects from scratch: Create all necessary files
- When asked to MODIFY existing files: FIRST check if they exist by listing directory, then read and modify them
- If user mentions specific files or features, assume they're talking about an EXISTING project unless explicitly stated otherwise
- For searching files in large projects:
  * On Linux/Mac: Use 'find' command
  * On Windows: Use 'dir /s' or 'where' command

UNDERSTANDING USER CONTEXT (CRITICAL):
- When user mentions adding features to an app/project, they are referring to an EXISTING project
- ALWAYS list directory first to understand the project structure before making changes
  * Linux/Mac: 'ls' or 'ls -la'
  * Windows: 'dir' or 'dir /a'
- Read relevant files to understand the current implementation before modifying
- DO NOT create standalone examples when user asks to modify existing projects
- If user says "add X to Y", assume Y exists and find it first
- Parse user requests carefully - vague requests like "add export button" mean modify existing code, not create new files
- When user mentions specific UI elements (e.g., "properties panel"), search for them in existing files

IMPORTANT: You have access to tools that you MUST use when appropriate. Don't just provide code examples - actually create files and execute commands when the user asks for them.

TOOL USAGE RULES:
- When a user asks you to "create", "build", "make" files or projects, you MUST use the file_operations tool to create ALL necessary files
- CREATE EACH FILE SEPARATELY: Use one tool call per file - do NOT try to create multiple files in a single tool call
- When you need to run commands, use the command_runner tool
- When you need to search for information, use the web_search tool
- Always use tools instead of just showing code examples
- Use multiple tool calls in sequence to complete entire projects

CRITICAL: COMMAND RUNNER - BACKGROUND vs FOREGROUND:
- ALWAYS run LONG-RUNNING commands in BACKGROUND using "run_async_command" operation
- Long-running commands include:
  * npm install, npm start, npm run dev
  * yarn install, yarn start, yarn dev
  * python manage.py runserver, flask run, uvicorn
  * Any server/dev server commands
  * Any command that doesn't terminate immediately
- Use "run_command" operation ONLY for QUICK commands that finish in <5 seconds:
  * ls, cat, echo, mkdir, touch
  * git status, git add, git commit
  * Quick file operations
- WRONG: {"operation": "run_command", "command": "npm start"}  ❌ This will BLOCK
- RIGHT:  {"operation": "run_async_command", "command": "npm start"}  ✅ Runs in background

WEB SEARCH TOOL USAGE (CRITICAL - WHEN TO USE):
- ALWAYS use web_search when user asks to implement something that requires current/external information:
  * Latest API documentation (e.g., "implement OpenAI API", "use Stripe payment")
  * Current best practices or frameworks (e.g., "create a React app with latest features")
  * Libraries or packages that need version info (e.g., "use TailwindCSS", "implement chart.js")
  * Technologies you're not certain about or that may have changed
  * Any request mentioning "latest", "current", "modern", "up-to-date"
- ALWAYS use web_search when user explicitly asks for research:
  * "Search for...", "Look up...", "Find information about..."
  * "What's the best way to...", "How do I...", "What are the options for..."
- DO NOT use web_search for:
  * Basic programming concepts you already know
  * Simple file operations or code modifications
  * General coding tasks that don't require external information
- When in doubt about implementation details, USE web_search to get accurate information

CRITICAL: NEVER DESCRIBE PLANS WITHOUT EXECUTING THEM
- DO NOT say "I will create X, Y, and Z files" and then only create X
- If you mention you will do something, you MUST include the tool calls to actually do it
- Either execute ALL the tool calls you describe, or don't describe them at all
- Keep explanatory text BRIEF - focus on executing tool calls
- If you need to create 3 files, include ALL 3 tool calls in your response, not just 1

CRITICAL: COMPLETE MODIFICATION REQUESTS
- When user asks to "make the UI dark/black themed" or "change X to Y", you MUST:
  1. Read the file (if needed to see current state)
  2. IMMEDIATELY write the modified version with the requested changes
- DO NOT just read the file and describe what you see - MODIFY IT
- DO NOT just explain what needs to be changed - ACTUALLY CHANGE IT
- Reading without writing is INCOMPLETE - always follow read with write for modification requests

AVAILABLE TOOLS AND THEIR OPERATIONS:

1. file_operations - For ALL file read/write operations:
   - read_file: Read entire file content
   - read_file_lines: Read specific lines from a file (1-indexed)
   - write_file: Write/overwrite entire file
   - write_file_lines: Replace specific lines in a file (1-indexed)
   - create_file: Create new file with content
   - create_directory: Create new directory
   - delete_file: Delete file or directory
   - list_directory: List directory contents
   - search_files: Search for files by pattern
   - copy_file: Copy file or directory
   - move_file: Move file or directory

2. command_runner - For running shell commands:
   - run_command: Run quick commands (<5 seconds)
   - run_async_command: Run long-running commands in background

3. web_search - For searching the web:
   - search_web: Search for information online

4. file_reader - For advanced file searching (RARELY NEEDED):
   - grep_search: Search for patterns in files (use file_operations.search_files instead)
   - list_directory: List directory (use file_operations.list_directory instead)

CRITICAL FILE OPERATION RULES:
- ALWAYS use "file_operations" tool for reading/writing files, NOT "file_reader"
- When READING files: Use file_operations with read_file operation
- When CREATING new projects: Immediately create all necessary files without exploration
- When MODIFYING files: Check if they exist first, read them, then write changes
- If a file doesn't exist when trying to read/modify it, inform the user and ask if they want to create it
- Use create_file for new files, write_file for modifying existing files
- For LARGE files (>10,000 lines), use read_file_lines and write_file_lines to work with specific sections
- For PARTIAL file edits, use write_file_lines to replace specific line ranges without rewriting entire file

LINE-BASED FILE OPERATIONS (CRITICAL FOR LARGE FILES):
- read_file_lines: Read specific lines from a file (useful for large files)
  - start_line: First line to read (1-indexed)
  - end_line: Last line to read (optional, defaults to end of file)
  - WHEN TO USE: If you see "...[X more characters truncated]" in file output, immediately use read_file_lines to read the truncated section
  - NEVER re-read the entire file if it was truncated - always use read_file_lines for the missing part
- write_file_lines: Replace specific lines in a file (useful for partial edits)
  - start_line: First line to replace (1-indexed)
  - end_line: Last line to replace (optional, defaults to start_line)
  - content: New content to write
  - WHEN TO USE: For modifying specific sections of large files without rewriting the entire file

CRITICAL: NEVER PUT LARGE CONTENT IN JSON TOOL CALLS
- If you need to write a file larger than 1000 lines, use write_file_lines to write it in sections
- NEVER try to include entire large files in a single JSON tool call - it will FAIL
- Break large file writes into multiple write_file_lines calls (e.g., lines 1-100, 101-200, etc.)
- For small additions to existing files, use write_file_lines to insert/replace only the needed sections

IMPORTANT: To use tools, you MUST include JSON code blocks in this exact format:

```json
{
  "tool_code": "file_operations",
  "args": {
    "operation": "create_file",
    "file_path": "index.html",
    "content": "<!DOCTYPE html>..."
  }
}
```

ALTERNATIVE FORMATS (for models with special tokens):
If your model uses special tokens, you can also use:
- <|message|>{"command":"ls -la"}<|call|> for command_runner
- <|message|>{"operation":"read_file","file_path":"app.js"}<|call|> for file_operations
The system will automatically detect and parse these formats.

To read an existing file:

```json
{
  "tool_code": "file_operations",
  "args": {
    "operation": "read_file",
    "file_path": "existing_file.txt"
  }
}
```

To read specific lines from a large file:

```json
{
  "tool_code": "file_operations",
  "args": {
    "operation": "read_file_lines",
    "file_path": "large_file.js",
    "start_line": 100,
    "end_line": 200
  }
}
```

To replace specific lines in a file:

```json
{
  "tool_code": "file_operations",
  "args": {
    "operation": "write_file_lines",
    "file_path": "app.js",
    "start_line": 50,
    "end_line": 75,
    "content": "// Updated code here\nfunction newFunction() {\n  return true;\n}"
  }
}
```

For multiple files, use separate tool calls:

```json
{
  "tool_code": "file_operations",
  "args": {
    "operation": "create_file",
    "file_path": "style.css",
    "content": "body { margin: 0; }"
  }
}
```

```json
{
  "tool_code": "file_operations",
  "args": {
    "operation": "create_file",
    "file_path": "script.js",
    "content": "console.log('Hello');"
  }
}
```

For commands:

```json
{
  "tool_code": "command_runner",
  "args": {
    "command": "ls -la"
  }
}
```

For LONG commands (npm install, servers), use run_async_command to run in background:

```json
{
  "tool_code": "command_runner",
  "args": {
    "operation": "run_async_command",
    "command": "npm install"
  }
}
```

For file reading and grep:

```json
{
  "tool_code": "file_reader",
  "args": {
    "operation": "read_file",
    "file_path": "src/App.js"
  }
}
```

```json
{
  "tool_code": "file_reader",
  "args": {
    "operation": "grep_search",
    "pattern": "function.*Component",
    "search_path": "src",
    "file_pattern": "*.js",
    "recursive": true
  }
}
```

For web search:

```json
{
  "tool_code": "web_search",
  "args": {
    "operation": "search_web",
    "query": "OpenAI API latest documentation",
    "num_results": 5
  }
}
```

```json
{
  "tool_code": "web_search",
  "args": {
    "operation": "fetch_url_content",
    "url": "https://example.com/api/docs",
    "extract_text": true
  }
}
```

```json
{
  "tool_code": "web_search",
  "args": {
    "operation": "get_api_docs",
    "api_name": "openai",
    "version": "latest"
  }
}
```

For directory context and project structure:

```json
{
  "tool_code": "directory_context",
  "args": {
    "operation": "get_directory_summary"
  }
}
```

```json
{
  "tool_code": "directory_context",
  "args": {
    "operation": "list_directory_tree",
    "max_depth": 3
  }
}
```

```json
{
  "tool_code": "directory_context",
  "args": {
    "operation": "get_project_structure"
  }
}
```

For code navigation (jump to definition, find references, search symbols):

```json
{
  "tool_code": "code_navigation",
  "args": {
    "operation": "jump_to_definition",
    "symbol": "MyClass"
  }
}
```

```json
{
  "tool_code": "code_navigation",
  "args": {
    "operation": "find_references",
    "symbol": "myFunction"
  }
}
```

```json
{
  "tool_code": "code_navigation",
  "args": {
    "operation": "search_symbols",
    "query": "handler",
    "symbol_type": "function"
  }
}
```

```json
{
  "tool_code": "code_navigation",
  "args": {
    "operation": "list_symbols",
    "file_path": "src/main.py"
  }
}
```

EXAMPLE WORKFLOWS:

When user asks to ADD FEATURE to existing project (e.g., "add export button to cymox"):
1. FIRST: List directory to see what files exist (use 'ls' on Linux/Mac or 'dir' on Windows)
2. SECOND: Read relevant files to understand current structure
   - If file is truncated, use read_file_lines to read the truncated section
3. THIRD: Modify the appropriate files to add the feature
   - For SMALL changes (adding a section): Use write_file_lines to insert/modify only needed lines
   - For LARGE files: NEVER use write_file with entire content - use write_file_lines in sections
4. FOURTH: Call end_response when done
5. DO NOT create new standalone files - modify existing ones!

When user asks to BUILD NEW web interface from scratch:
1. Immediately create ALL necessary files (index.html, style.css, script.js) with complete, working code
2. Include ALL tool calls in your response
3. Call end_response when done

When user asks to MODIFY a file (e.g., "make the UI black themed"):
1. FIRST: Check if file exists by listing directory (if not already known)
2. SECOND: Read the file to see current content
3. THIRD: Write the modified version with requested changes
4. FOURTH: Call end_response when done
5. Do NOT just describe what you see - MODIFY IT

When user asks to READ/ANALYZE a file:
1. First: List directory to see what files exist (use 'ls' on Linux/Mac or 'dir' on Windows)
2. Then: If file exists, read it with file_operations
3. Finally: Provide analysis based on actual file content
4. Call end_response when done

When user asks to IMPLEMENT something requiring external/current information:
1. FIRST: Use web_search to get latest documentation/information
   - Example: "implement Stripe payment" → search for "Stripe API latest documentation"
   - Example: "use TailwindCSS" → search for "TailwindCSS installation guide"
2. SECOND: Review search results and fetch detailed content if needed
3. THIRD: Create/modify files based on the researched information
4. FOURTH: Call end_response when done
5. DO NOT guess API endpoints or library usage - ALWAYS search first!

When user explicitly asks for RESEARCH:
1. FIRST: Use web_search with appropriate query
2. SECOND: Present search results to user
3. THIRD: If user wants more details, fetch specific URLs
4. FOURTH: Call end_response when done

The tools will execute automatically and show results. Keep explanatory text BRIEF.

Available tools:
"""

        # Add built-in tools
        prompt += "- file_operations: Create, read, write, delete files\n"
        prompt += "- file_reader: Read files, grep search, list directories\n"
        prompt += "- command_runner: Execute shell commands (use run_async_command for long tasks)\n"
        prompt += "- web_search: Search the web for information\n"
        prompt += "- response_control: Use end_response when task is complete\n"
        prompt += "- directory_context: Get detailed directory structure and project information\n"
        prompt += "- code_navigation: Jump to definition, find references, search symbols in code\n"
        
        # Add ask_question tool if enabled
        ask_tool = self.tool_registry.get_tool('ask_question')
        if ask_tool and ask_tool.is_enabled():
            prompt += "- ask_question: Ask user clarifying questions when confused or uncertain\n"
        
        # Add MCP tools dynamically
        mcp_tools = [tool_name for tool_name in self.tool_registry.list_tools() if tool_name.startswith('mcp_')]
        if mcp_tools:
            prompt += "\n🔌 MCP Tools (from connected servers):\n"
            for tool_name in mcp_tools:
                tool_info = self.tool_registry.get_tool_info(tool_name)
                if tool_info:
                    # Extract server name from tool name (mcp_servername_toolname)
                    parts = tool_name.split('_', 2)
                    server_name = parts[1] if len(parts) > 1 else 'unknown'
                    description = tool_info.get('description', '')
                    prompt += f"- {tool_name}: [{server_name}] {description}\n"
        
        # Add ask_question usage instructions if enabled
        if ask_tool and ask_tool.is_enabled():
            prompt += """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    ASK QUESTION FEATURE (ENABLED)                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝

CRITICAL: When you use ask_question tool, you MUST use the user's answer in your response!
- The tool returns {"answer": "user's choice", "was_custom": true/false}
- ALWAYS read and use the "answer" field from the tool result
- If was_custom is true, the user provided their own answer - USE IT EXACTLY
- DO NOT ignore the answer and proceed with your own assumptions

MANDATORY SCENARIOS - YOU MUST ASK QUESTIONS IN THESE CASES:

1. **Framework/Technology Not Specified:**
   - User asks to "build an app" or "create a website" without specifying technology
   - Example: "build a todo app" → ASK which framework (React, Vue, Python Flask, etc.)
   - Example: "create a web interface" → ASK which stack to use

2. **Database/Storage Not Specified:**
   - User asks for data persistence without specifying database
   - Example: "store user data" → ASK which database (SQLite, PostgreSQL, MongoDB, etc.)

3. **Programming Language Ambiguous:**
   - User asks to "build an API" without language
   - Example: "create a REST API" → ASK which language (Python, Node.js, Go, etc.)

4. **Multiple Valid Approaches:**
   - User request can be implemented in fundamentally different ways
   - Example: "add authentication" → ASK which method (JWT, OAuth, sessions, etc.)

5. **Styling/UI Framework Not Clear:**
   - User asks for UI without specifying styling approach
   - Example: "make it look good" → ASK which approach (Tailwind, Bootstrap, custom CSS, etc.)

HOW TO USE THE TOOL:

- ALWAYS provide at least 2 specific options (option1 and option2)
- Optionally provide a 3rd option (option3) if there are 3+ common choices
- A "Something else" option is AUTOMATICALLY added for custom user input
- DO NOT include "Something else" in your options - it's added automatically

Example with 2 options (3rd will be auto-added as "Something else"):

```json
{
  "tool_code": "ask_question",
  "args": {
    "question": "You didn't specify which framework to use. Which would you prefer?",
    "option1": "React with Vite (modern, popular)",
    "option2": "Python Flask (backend framework)"
  }
}
```

Example with 3 options (4th will be auto-added as "Something else"):

```json
{
  "tool_code": "ask_question",
  "args": {
    "question": "Which framework would you like to use for your todo list app?",
    "option1": "React with Vite (frontend, JavaScript)",
    "option2": "Python Flask (backend, Python)",
    "option3": "Vue.js (frontend, JavaScript)"
  }
}
```

CRITICAL - USING THE ANSWER:

After calling ask_question, you will receive a response like:
{
  "question": "Which framework...",
  "answer": "Python Flask (backend, Python)",
  "was_custom": false
}

OR if user chose "Something else":
{
  "question": "Which framework...",
  "answer": "I want to use Django with PostgreSQL",
  "was_custom": true
}

YOU MUST:
1. Read the "answer" field
2. Use that EXACT answer in your implementation
3. If was_custom is true, parse the custom answer carefully
4. DO NOT proceed with a different choice than what user selected

WHEN TO ASK (Be Proactive):
  ✓ User doesn't specify framework/language/technology
  ✓ Critical technical decisions need user input
  ✓ Multiple equally valid approaches exist
  ✓ User's request is ambiguous or unclear
  ✓ You need clarification on requirements
  
WHEN NOT TO ASK:
  ✗ User already specified their preference clearly
  ✗ Minor implementation details you can decide
  ✗ Questions you can answer through web search
  ✗ User has been very specific in their request

REMEMBER: Ask questions EARLY before starting implementation, not after!

"""
        
        prompt += """
RESPONSE CONTINUATION (CRITICAL - SYSTEM WILL AUTO-CONTINUE):
- ⚠️ IMPORTANT: The system will AUTOMATICALLY continue your response after EVERY message
- This means you will KEEP GETTING called until you explicitly call end_response
- YOU MUST call end_response when you finish ALL work, or you'll loop forever:

```json
{
  "tool_code": "response_control",
  "args": {
    "operation": "end_response"
  }
}
```

- HOW IT WORKS:
  * You respond → System auto-continues → You respond again → System auto-continues → ...
  * This loop ONLY stops when you call end_response
  * If you say "I will use a tool" but don't execute it, system will auto-continue and remind you
  * If you execute tools, system will auto-continue for next steps
  * If you do nothing, system will still auto-continue

- WHEN TO USE end_response (THE ONLY WAY TO STOP):
  * ✅ After completing ALL requested work
  * ✅ After providing final summary/instructions
  * ✅ When task is 100% complete
  * ❌ NEVER use it if task is incomplete - system will continue for you

- CRITICAL: If you forget end_response, you'll keep getting called in an infinite loop!

REMEMBER:
1. Use tools to actually perform actions, don't just provide code examples!
2. Complete ENTIRE requests in ONE response - create all necessary files and functionality!
3. Don't stop after one file - build complete, functional projects!
4. NEVER promise to do something without including the tool calls to actually do it!
5. For very long file content, the system will automatically handle it - just provide the full content

═══════════════════════════════════════════════════════════════════════════════
🎯 PROJECT COMPLETION CHECKLIST - MANDATORY FOR ALL PROJECT REQUESTS
═══════════════════════════════════════════════════════════════════════════════

When a user asks you to "build/create a [project type] app/project", you MUST complete ALL of these steps:

✅ STEP 1: Research (if needed)
   - Perform web search for best practices and current versions
   - Create documentation in MD/ folder with findings

✅ STEP 2: Create ALL Project Files
   - Create directory structure
   - Create ALL source files (components, styles, logic, etc.)
   - Create configuration files

✅ STEP 3: Create package.json/requirements.txt (CRITICAL - DON'T SKIP!)
   For JavaScript/Node.js/React projects:
   - Create package.json with correct dependencies and versions
   - Include proper scripts (start, build, test, dev)
   - Add project metadata (name, version, description)

   For Python projects:
   - Create requirements.txt with all dependencies
   - Include version constraints where appropriate

✅ STEP 4: Install Dependencies (CRITICAL - DON'T SKIP!)
   - Tell the user to run npm install (or yarn install) for JavaScript projects
   - Tell the user to run pip install -r requirements.txt for Python projects

✅ STEP 5: Explanation
   - Provide clear instructions to user

✅ STEP 6: Final Summary
   - List all files created
   - Show how to run the project
   - Mention any next steps or customization options

⚠️ CRITICAL RULES:
- DO NOT stop after creating source files - you MUST create package.json/requirements.txt!
- DO NOT skip steps - complete the ENTIRE project setup!
- DO NOT use end_response until ALL steps above are completed!
- ALWAYS use end_response when done - NEVER leave the response hanging!

📋 EXAMPLE COMPLETE FLOW FOR REACT APP:
1. Web search for React best practices and current versions
2. Create MD/ documentation files with findings
3. Create public/index.html
4. Create src/ directory with all components (App.js, index.js, etc.)
5. Create src/index.css and component styles
6. Create package.json with dependencies ← DON'T SKIP THIS!
8. Provide instructions: npm install and npm start
9. THEN use end_response

If you find yourself about to use end_response, ask yourself:
- Did I create package.json/requirements.txt? If NO → CREATE IT NOW!
- Did I run npm install / pip install? If NO → RUN IT NOW!
- Is the project ready to run? If NO → COMPLETE THE SETUP!

═══════════════════════════════════════════════════════════════════════════════
📦 COMMON PROJECT TYPES & REQUIRED FILES
═══════════════════════════════════════════════════════════════════════════════

REACT APP:
✅ Must create: package.json, public/index.html, src/index.js, src/App.js, src/index.css
✅ Must tell user to run: npm install
✅ Dependencies: react, react-dom, react-scripts (check latest versions via web search)
✅ Must tell user to run: npm start

NODE.JS/EXPRESS APP:
✅ Must create: package.json, server.js (or index.js), .env template
✅ Must tell user to run: npm install
✅ Dependencies: express, and any other needed packages
✅ Must tell user to run: node server.js or npm start

PYTHON APP:
✅ Must create: requirements.txt, main.py (or app.py), README.md
✅ Must tell user to run: pip install -r requirements.txt
✅ Must tell user to run: python main.py

NEXT.JS APP:
✅ Must create: package.json, pages/index.js, pages/_app.js, public/ folder
✅ Must tell user to run: npm install
✅ Dependencies: next, react, react-dom (check latest versions)
✅ Must tell user to run: npm run dev

VITE + REACT APP:
✅ Must create: package.json, index.html, src/main.jsx, src/App.jsx, vite.config.js
✅ Must tell user to run: npm install
✅ Dependencies: vite, react, react-dom, @vitejs/plugin-react
✅ Must tell user to run: npm run dev

REMEMBER: The project is NOT complete until dependencies are installed and it's ready to run!

═══════════════════════════════════════════════════════════════════════════════
📊 SHOWING DIFFS AND FILE PREVIEWS
═══════════════════════════════════════════════════════════════════════════════

When creating or modifying files:
- The tool execution will show the operation and file path
- For file modifications, a diff will be automatically displayed
- Do NOT manually show file previews or content in your response
- Focus on explaining what you did and why
"""

        # Add OS information to help AI use correct commands
        import platform

        os_name = platform.system()
        if os_name == "Windows":
            prompt += "\n\nOPERATING SYSTEM: Windows"
            prompt += "\nUse Windows commands: 'dir', 'dir /a', 'dir /s', 'where', etc."
        elif os_name == "Darwin":
            prompt += "\n\nOPERATING SYSTEM: macOS"
            prompt += "\nUse Unix commands: 'ls', 'ls -la', 'find', etc."
        else:  # Linux and others
            prompt += "\n\nOPERATING SYSTEM: Linux"
            prompt += "\nUse Unix commands: 'ls', 'ls -la', 'find', etc."

        if project_path:
            prompt += f"\n\nCurrent project path: {project_path}"
            prompt += "\nYou can analyze and modify files in this project."
            
            # Add directory context automatically
            try:
                from pathlib import Path
                project_dir = Path(project_path)
                if project_dir.exists() and project_dir.is_dir():
                    prompt += "\n\n" + "=" * 80
                    prompt += "\n📁 CURRENT DIRECTORY CONTENTS (AUTO-PROVIDED FOR CONTEXT)"
                    prompt += "\n" + "=" * 80
                    
                    # List immediate directory contents
                    contents = []
                    files = []
                    dirs = []
                    
                    try:
                        for item in sorted(project_dir.iterdir()):
                            if item.name.startswith('.') and item.name not in ['.gitignore', '.env.example']:
                                continue  # Skip hidden files except important ones
                            
                            if item.is_dir():
                                # Count items in directory
                                try:
                                    item_count = len(list(item.iterdir()))
                                    dirs.append(f"  📂 {item.name}/ ({item_count} items)")
                                except (PermissionError, OSError):
                                    dirs.append(f"  📂 {item.name}/")
                            else:
                                # Get file size
                                try:
                                    size = item.stat().st_size
                                    if size < 1024:
                                        size_str = f"{size}B"
                                    elif size < 1024 * 1024:
                                        size_str = f"{size/1024:.1f}KB"
                                    else:
                                        size_str = f"{size/(1024*1024):.1f}MB"
                                    files.append(f"  📄 {item.name} ({size_str})")
                                except (PermissionError, OSError):
                                    files.append(f"  📄 {item.name}")
                        
                        prompt += f"\n\nDirectory: {project_path}"
                        prompt += f"\n\nDirectories ({len(dirs)}):"
                        if dirs:
                            prompt += "\n" + "\n".join(dirs)
                        else:
                            prompt += "\n  (none)"
                        
                        prompt += f"\n\nFiles ({len(files)}):"
                        if files:
                            prompt += "\n" + "\n".join(files)
                        else:
                            prompt += "\n  (none)"
                        
                        prompt += "\n\n" + "=" * 80
                        prompt += "\nℹ️  This directory listing is provided automatically for your context."
                        prompt += "\nℹ️  You can use the 'directory_context' tool for more detailed information."
                        prompt += "\n" + "=" * 80
                        
                    except PermissionError:
                        prompt += "\n\n⚠️  Permission denied accessing directory contents."
            except Exception:
                # Silently fail if directory context can't be added
                pass

        return prompt

    def _contains_tool_calls(self, response: str) -> bool:
        """Check if response contains tool calls"""
        # Check for JSON tool call patterns
        import re

        tool_patterns = [
            r'"tool_code":\s*"[^"]+?"',
            r'"tool_name":\s*"[^"]+?"',
            r"execute_command",
            r"command_runner",
            r"file_operations",
            r"web_search",
            r"code_analysis",
        ]
        return any(re.search(pattern, response) for pattern in tool_patterns)

    async def _execute_tools(self, response: str, project_path: str = None) -> str:
        """Execute tools mentioned in the response"""
        import json
        import re

        # Find JSON tool calls in the response
        json_pattern = r"```json\s*(\{[^`]+\})\s*```"
        matches = re.findall(json_pattern, response, re.DOTALL)

        if not matches:
            return response

        # Process each tool call
        results = []
        for match in matches:
            try:
                tool_call = json.loads(match)
                tool_name = tool_call.get("tool_code") or tool_call.get("tool_name")
                args = tool_call.get("args", {})

                if tool_name in ["execute_command", "command_runner"]:
                    command = args.get("command")
                    if command:
                        # Use command runner tool via registry
                        cmd_args = args.copy()
                        # Set default operation if not specified
                        if "operation" not in cmd_args:
                            cmd_args["operation"] = "run_command"
                        if "cwd" not in cmd_args:
                            cmd_args["cwd"] = project_path or "."
                        result = await self.tool_registry.execute_tool(
                            "command_runner", user_id="ai_engine", **cmd_args
                        )
                        if result.success:
                            command = args.get("command", "unknown")
                            results.append(
                                f"**SUCCESS:** Tool Used: command_runner\n**Command Executed:** {command}"
                            )
                        else:
                            results.append(
                                f"**ERROR:** Tool Error: command_runner - {result.error}"
                            )

                elif tool_name == "file_operations":
                    operation = args.get("operation")
                    if operation:
                        # Prepend project_path to relative file paths
                        file_path = args.get("file_path")
                        if file_path and project_path:
                            from pathlib import Path

                            path = Path(file_path)
                            if not path.is_absolute():
                                args["file_path"] = str(Path(project_path) / file_path)

                        # Use file operations tool - pass all args directly
                        result = await self.tool_registry.execute_tool(
                            "file_operations", user_id="ai_engine", **args
                        )
                        if result.success:
                            # File operations are shown via live tool execution
                            # No need to append results here for streaming mode
                            pass
                        else:
                            results.append(f"ERROR: file_operations - {result.error}")

                elif tool_name == "web_search":
                    operation = args.get("operation", "search_web")
                    # Use web search tool via registry
                    result = await self.tool_registry.execute_tool(
                        "web_search", user_id="ai_engine", **args
                    )
                    if result.success:
                        # Format the result based on operation type
                        if operation == "search_web":
                            query = args.get("query", "unknown")
                            search_results = result.data if result.data else []
                            result_text = f"**SUCCESS:** Tool Used: web_search\n**Query:** {query}\n\n**Search Results:**\n"
                            for idx, item in enumerate(search_results[:5], 1):
                                result_text += (
                                    f"\n{idx}. **{item.get('title', 'No title')}**\n"
                                )
                                result_text += (
                                    f"   {item.get('snippet', 'No description')}\n"
                                )
                                result_text += f"   🔗 {item.get('url', 'No URL')}\n"
                            results.append(result_text)

                        elif operation == "fetch_url_content":
                            url = args.get("url", "unknown")
                            content_data = result.data if result.data else {}
                            title = content_data.get("title", "No title")
                            content = content_data.get("content", "No content")
                            content_type = content_data.get("content_type", "text")

                            # Truncate content if too long
                            max_display = 2000
                            if len(content) > max_display:
                                content = (
                                    content[:max_display]
                                    + f"\n\n... (truncated, total length: {len(content)} characters)"
                                )

                            result_text = f"**SUCCESS:** Tool Used: web_search (fetch_url_content)\n"
                            result_text += f"**URL:** {url}\n"
                            result_text += f"**Title:** {title}\n"
                            result_text += f"**Content Type:** {content_type}\n\n"
                            result_text += f"**Content:**\n{content}"
                            results.append(result_text)

                        elif operation == "parse_documentation":
                            url = args.get("url", "unknown")
                            doc_data = result.data if result.data else {}
                            result_text = f"**SUCCESS:** Tool Used: web_search (parse_documentation)\n"
                            result_text += f"**URL:** {url}\n"
                            result_text += (
                                f"**Title:** {doc_data.get('title', 'No title')}\n"
                            )
                            result_text += (
                                f"**Type:** {doc_data.get('doc_type', 'unknown')}\n\n"
                            )

                            sections = doc_data.get("sections", [])
                            if sections:
                                result_text += "**Sections:**\n"
                                for section in sections[:5]:
                                    result_text += (
                                        f"\n• {section.get('title', 'Untitled')}\n"
                                    )
                            results.append(result_text)

                        elif operation == "get_api_docs":
                            api_name = args.get("api_name", "unknown")
                            api_data = result.data if result.data else {}
                            if api_data.get("found", True):
                                result_text = f"**SUCCESS:** Tool Used: web_search (get_api_docs)\n"
                                result_text += f"**API:** {api_name}\n"
                                result_text += f"**Title:** {api_data.get('title', 'API Documentation')}\n"
                                results.append(result_text)
                            else:
                                result_text = f"**WARNING:** Tool Used: web_search (get_api_docs)\n"
                                result_text += f"**API:** {api_name}\n"
                                result_text += f"**ERROR:** {api_data.get('message', 'Documentation not found')}\n"
                                results.append(result_text)
                        else:
                            results.append(
                                f"**SUCCESS:** Tool Used: web_search ({operation})"
                            )
                    else:
                        results.append(
                            f"**ERROR:** Tool Error: web_search - {result.error}"
                        )

            except Exception as e:
                results.append(f"**Tool Error:** {str(e)}")

        # Replace the original response with just the tool results if tools were used
        if results:
            # Remove JSON tool calls from the response
            import re

            # Remove JSON code blocks - more aggressive pattern
            response = re.sub(r"```json.*?```", "", response, flags=re.DOTALL)
            # Remove any remaining code blocks
            response = re.sub(r"```.*?```", "", response, flags=re.DOTALL)
            # Remove leftover JSON-like patterns
            response = re.sub(r'\{[\s\S]*?"tool_code"[\s\S]*?\}', "", response)
            # Clean up extra whitespace
            response = re.sub(r"\n\s*\n\s*\n+", "\n\n", response)
            response = response.strip()

            # If response is mostly empty after removing code blocks, just show tool results
            if len(response.strip()) < 100:
                return "\n\n".join(results)
            else:
                return response + "\n\n" + "\n\n".join(results)

        return response

    async def build_project(
        self,
        description: str,
        language: str = None,
        framework: str = None,
        output_dir: str = None,
        interactive: bool = False,
    ) -> Dict[str, Any]:
        """Build a project based on description"""

        prompt = f"""Build a {language or "appropriate"} project with the following description:
{description}

Requirements:
- Framework: {framework or "most suitable"}
- Output directory: {output_dir or "current directory"}
- Interactive mode: {interactive}

Please create a complete, working project structure with:
1. Main application files
2. Configuration files
3. Dependencies/requirements
4. README with setup instructions
5. Basic tests if applicable

Provide step-by-step implementation."""

        response = await self.process_message(prompt)

        return {
            "status": "completed",
            "description": description,
            "output_path": output_dir or ".",
            "response": response,
        }

    async def analyze_project(
        self,
        project_path: str,
        output_format: str = "text",
        focus: str = None,
        include_suggestions: bool = False,
    ) -> Any:
        """Analyze a project and provide insights"""

        project_path = Path(project_path)

        # Gather project information
        project_info = self._gather_project_info(project_path)

        prompt = f"""Analyze the following project:

Path: {project_path}
Structure: {project_info["structure"]}
Languages: {project_info["languages"]}
Files: {len(project_info["files"])} files

Focus area: {focus or "general analysis"}
Include suggestions: {include_suggestions}
Output format: {output_format}

Provide a comprehensive analysis including:
1. Project overview and architecture
2. Code quality assessment
3. Dependencies and security
4. Performance considerations
5. Best practices compliance
"""

        if include_suggestions:
            prompt += "\n6. Specific improvement suggestions"

        response = await self.process_message(prompt, project_path=str(project_path))

        if output_format == "json":
            # Try to structure the response as JSON
            try:
                return {
                    "project_path": str(project_path),
                    "analysis": response,
                    "metadata": project_info,
                    "timestamp": str(asyncio.get_event_loop().time()),
                }
            except Exception:
                return {"analysis": response, "error": "Could not structure as JSON"}

        return response

    def _gather_project_info(self, project_path: Path) -> Dict[str, Any]:
        """Gather basic information about a project"""
        info = {"structure": [], "languages": set(), "files": []}

        try:
            for item in project_path.rglob("*"):
                if item.is_file() and not any(
                    part.startswith(".") for part in item.parts
                ):
                    relative_path = item.relative_to(project_path)
                    info["files"].append(str(relative_path))

                    # Detect language by extension
                    suffix = item.suffix.lower()
                    language_map = {
                        ".py": "Python",
                        ".js": "JavaScript",
                        ".ts": "TypeScript",
                        ".java": "Java",
                        ".cpp": "C++",
                        ".c": "C",
                        ".go": "Go",
                        ".rs": "Rust",
                        ".php": "PHP",
                        ".rb": "Ruby",
                    }

                    if suffix in language_map:
                        info["languages"].add(language_map[suffix])

        except Exception as e:
            info["error"] = str(e)

        info["languages"] = list(info["languages"])
        return info
