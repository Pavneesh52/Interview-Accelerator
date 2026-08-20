from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel
import json
import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        pass
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        pass


class NemotronProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.NEMOTRON_API_BASE
        self.api_key = settings.NEMOTRON_API_KEY
        self.model = settings.NEMOTRON_MODEL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            timeout=120.0,
        )
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        schema = response_model.model_json_schema()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        structured_prompt = f"""{prompt}

You must respond with a valid JSON object that matches this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON object, no additional text."""
        
        messages.append({"role": "user", "content": structured_prompt})
        
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        try:
            parsed = json.loads(content)
            return response_model(**parsed)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON", error=str(e), content=content[:500])
            raise
        except Exception as e:
            logger.error("Failed to validate LLM response", error=str(e))
            raise
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def close(self):
        await self.client.aclose()


class OpenAIProvider(LLMProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_model,
        )
        return response.choices[0].message.parsed
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    def __init__(self):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        schema = response_model.model_json_schema()
        
        system = system_prompt or ""
        system += f"\n\nYou must respond with a valid JSON object matching this schema:\n{json.dumps(schema, indent=2)}"
        
        response = await self.client.messages.create(
            model=self.model,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.content[0].text
        parsed = json.loads(content)
        return response_model(**parsed)
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content[0].text


class LLMService:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        if settings.NEMOTRON_API_BASE:
            self.providers["nemotron"] = NemotronProvider()
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIProvider()
        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = AnthropicProvider()
        
        self.default_provider = "nemotron" if "nemotron" in self.providers else list(self.providers.keys())[0] if self.providers else None
    
    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        provider_name = name or self.default_provider
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"LLM provider '{provider_name}' not available")
        return self.providers[provider_name]
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> T:
        llm = self.get_provider(provider)
        return await llm.generate_structured(prompt, response_model, system_prompt, **kwargs)
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> str:
        llm = self.get_provider(provider)
        return await llm.generate_text(prompt, system_prompt, **kwargs)
    
    async def close(self):
        for provider in self.providers.values():
            if hasattr(provider, "close"):
                await provider.close()


llm_service = LLMService()