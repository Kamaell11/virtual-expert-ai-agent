import httpx
import json
import os
import asyncio
from typing import List, Optional, Dict
from dotenv import load_dotenv
# from transformers import AutoTokenizer, AutoModelForCausalLM
# import torch

load_dotenv()

class LLMService:
    """Service for interacting with Ollama LLM models and fine-tuned models"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.current_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        self.current_fine_tuned_model = None
        self.fine_tuned_model_cache = {}
        self.default_parameters = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1
        }
    
    async def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_available_models(self) -> List[Dict]:
        """Get list of available models from Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
                return []
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model from Ollama"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes timeout for model download
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Error pulling model {model_name}: {e}")
            return False
    
    async def switch_model(self, model_name: str) -> bool:
        """Switch to a different model"""
        try:
            # Check if model exists
            models = await self.get_available_models()
            model_names = [model.get("name", "") for model in models]
            
            if model_name not in model_names:
                # Try to pull the model if it doesn't exist
                success = await self.pull_model(model_name)
                if not success:
                    return False
            
            self.current_model = model_name
            return True
        except Exception as e:
            print(f"Error switching to model {model_name}: {e}")
            return False
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict] = None
    ) -> str:
        """Generate response using the current LLM model"""
        try:
            # Prepare the request payload
            payload = {
                "model": self.current_model,
                "prompt": prompt,
                "stream": False,
                "options": {**self.default_parameters, **(parameters or {})}
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "No response generated")
                else:
                    return f"Error: Failed to generate response (Status: {response.status_code})"
                    
        except httpx.TimeoutException:
            return "Error: Request timed out. The model might be processing a complex query."
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        parameters: Optional[Dict] = None
    ) -> str:
        """Generate chat completion using conversation history"""
        try:
            payload = {
                "model": self.current_model,
                "messages": messages,
                "stream": False,
                "options": {**self.default_parameters, **(parameters or {})}
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("message", {}).get("content", "No response generated")
                else:
                    return f"Error: Failed to generate chat response (Status: {response.status_code})"
                    
        except httpx.TimeoutException:
            return "Error: Request timed out. The model might be processing a complex query."
        except Exception as e:
            return f"Error in chat completion: {str(e)}"
    
    async def switch_to_fine_tuned_model(self, model_path: str, specialization: str = None) -> bool:
        """Switch to a fine-tuned model"""
        try:
            if model_path in self.fine_tuned_model_cache:
                self.current_fine_tuned_model = self.fine_tuned_model_cache[model_path]
                return True
            
            # For now, we'll simulate loading fine-tuned models
            # In production, you would load the actual fine-tuned model
            self.current_fine_tuned_model = {
                "path": model_path,
                "specialization": specialization,
                "loaded": True
            }
            self.fine_tuned_model_cache[model_path] = self.current_fine_tuned_model
            return True
        except Exception as e:
            print(f"Error switching to fine-tuned model: {e}")
            return False
    
    async def switch_to_base_model(self) -> bool:
        """Switch back to base Ollama model"""
        self.current_fine_tuned_model = None
        return True
    
    async def generate_with_fine_tuned_model(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict] = None
    ) -> str:
        """Generate response using fine-tuned model (simulation for now)"""
        if not self.current_fine_tuned_model:
            return await self.generate_response(prompt, system_prompt, parameters)
        
        # Enhance the system prompt with specialization context
        specialization = self.current_fine_tuned_model.get("specialization", "")
        
        if specialization == "medical":
            enhanced_system_prompt = """You are a medical expert AI assistant with specialized training in healthcare, medicine, and medical procedures. You have extensive knowledge about:
- Medical diagnoses and treatments
- Symptoms and conditions  
- Medications and their effects
- Medical procedures and best practices
- Healthcare guidelines and protocols

Always provide accurate, evidence-based medical information while emphasizing that users should consult healthcare professionals for personal medical advice."""
        
        elif specialization == "legal":
            enhanced_system_prompt = """You are a legal expert AI assistant with specialized training in law, legal procedures, and legal systems. You have extensive knowledge about:
- Legal principles and concepts
- Court procedures and processes
- Contract law and regulations
- Civil and criminal law
- Legal rights and responsibilities

Always provide accurate legal information while emphasizing that users should consult qualified attorneys for specific legal advice."""
        
        elif specialization == "mechanic":
            enhanced_system_prompt = """You are an automotive expert AI assistant with specialized training in vehicle mechanics, repair, and maintenance. You have extensive knowledge about:
- Engine diagnostics and repair
- Automotive systems and components
- Maintenance schedules and procedures
- Troubleshooting vehicle problems
- Tool usage and safety practices

Provide detailed, practical automotive advice based on industry best practices."""
        
        else:
            enhanced_system_prompt = system_prompt or "You are a helpful AI assistant with specialized domain knowledge."
        
        # Use the enhanced system prompt with base model
        return await self.generate_response(
            prompt, 
            enhanced_system_prompt, 
            parameters
        )

    async def create_agent_response(
        self,
        query: str,
        agent_config: Optional[Dict] = None,
        web_search_service=None,
        fine_tuned_model_info: Optional[Dict] = None
    ) -> str:
        """Generate response with AI agent capabilities and tools"""
        
        # Check if we should use fine-tuned model
        if fine_tuned_model_info:
            await self.switch_to_fine_tuned_model(
                fine_tuned_model_info.get("model_path", ""),
                fine_tuned_model_info.get("specialization", "")
            )
        
        # Natural conversational AI system prompt
        agent_system_prompt = """You are a helpful, conversational AI assistant with web search capabilities. Respond naturally to questions and have normal conversations with users.

**Important Rules:**
1. Answer the user's actual question directly and naturally
2. Be conversational and friendly, like talking to a friend
3. Don't mention your capabilities unless directly asked
4. When users ask for current information (weather, news, recent events), you can search the web
5. Only generate files when explicitly asked (using words like "generate", "create", "export", "download")

**Web Search Capabilities:**
- You can search for current weather, news, and recent information
- When you have web search results, provide the information naturally
- Always cite your sources when using search results

**Examples:**
- User: "Hi" → You: "Hi there! How can I help you today?"
- User: "What's the weather in Lublin?" → Search for weather and provide current information
- User: "Generate CSV with sales data" → Create the file as requested

Be natural, helpful, and conversational. Don't be robotic or overly formal."""
        
        system_prompt = agent_system_prompt
        parameters = self.default_parameters.copy()
        
        if agent_config:
            system_prompt = agent_config.get("system_prompt", agent_system_prompt)
            if agent_config.get("parameters"):
                try:
                    custom_params = json.loads(agent_config["parameters"])
                    parameters.update(custom_params)
                except json.JSONDecodeError:
                    pass
        
        # Check if user wants web search
        search_keywords = ['weather', 'current', 'now', 'today', 'latest', 'recent', 'news', 'what is happening', 'search']
        needs_search = any(keyword in query.lower() for keyword in search_keywords)
        
        search_results = None
        if needs_search and web_search_service:
            try:
                # Determine search type
                if 'weather' in query.lower():
                    # Better city name extraction
                    city_query = query.lower()
                    # Remove common words
                    for word in ['weather', 'in', 'tell', 'me', 'what', 'is', 'the', 'right', 'now', 'today', 'current']:
                        city_query = city_query.replace(word, ' ')
                    
                    # Clean up the city name
                    city = ' '.join([word for word in city_query.split() if len(word) > 1]).strip()
                    country = 'Poland' if 'poland' in query.lower() or 'lublin' in query.lower() else ''
                    search_results = await web_search_service.get_weather_info(city, country)
                else:
                    result = await web_search_service.search_general_info(query)
                    search_results = result
            except Exception as e:
                print(f"Search error: {e}")
        
        # Check if user wants file generation
        if any(keyword in query.lower() for keyword in ['generate', 'create', 'export', 'download', 'save', 'give me a file', 'csv file']):
            file_instruction = f"""

SPECIAL INSTRUCTION: The user is asking for file generation. After your normal response, add this JSON format:
{{
  "action": "generate_csv",
  "description": "[what data to generate based on user request]",
  "filename": "[suggested filename].csv"
}}"""
            enhanced_query = query + file_instruction
        else:
            enhanced_query = query
        
        # Add search results to query if available
        if search_results:
            if 'temperature' in str(search_results):
                # Weather results
                enhanced_query += f"\n\nWEB SEARCH RESULTS: {json.dumps(search_results, indent=2)}\nUse this information to answer about the weather."
            else:
                # General search results
                enhanced_query += f"\n\nWEB SEARCH RESULTS: {json.dumps(search_results, indent=2)}\nUse this information to provide an accurate answer."
        
        # Use fine-tuned model if available, otherwise use base model
        if self.current_fine_tuned_model:
            return await self.generate_with_fine_tuned_model(
                prompt=enhanced_query,
                system_prompt=system_prompt,
                parameters=parameters
            )
        else:
            return await self.generate_response(
                prompt=enhanced_query,
                system_prompt=system_prompt,
                parameters=parameters
            )
    
    def get_model_info(self) -> Dict:
        """Get current model information"""
        return {
            "current_model": self.current_model,
            "current_fine_tuned_model": self.current_fine_tuned_model,
            "base_url": self.base_url,
            "default_parameters": self.default_parameters
        }