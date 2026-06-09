import logging
from langdetect import detect as langdetect_detect
from app.services.audit import AuditLogger, AuditRecord
from app.ai.providers.registry import ProviderRegistry
from app.schemas.provider import ModelRequest, ChatMessage

logger = logging.getLogger(__name__)

class TranslationError(Exception):
    pass

class LanguageService:
    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger

    async def detect(self, text: str) -> str:
        try:
            return langdetect_detect(text)
        except Exception:
            registry = ProviderRegistry()
            provider = registry.get_default()
            for name, cls in registry._providers.items():
                inst = cls()
                if inst.descriptor().configured:
                    try:
                        request = ModelRequest(
                            model=inst.descriptor().default_models[0],
                            messages=[ChatMessage(role="user", content=f"Reply with only the ISO 639-1 two-letter language code for this text: {text[:200]}")],
                            max_tokens=10
                        )
                        res = await inst.complete(request)
                        code = res.content.strip().lower()
                        if len(code) == 2:
                            return code
                    except Exception:
                        pass
            return "en"

    async def translate_prompt_output(self, text: str, target_lang: str, context: str) -> tuple[str, str | None]:
        if not target_lang or target_lang.lower() == "en" or not text:
            return text, None
            
        registry = ProviderRegistry()
        for name, inst in registry._providers.items():
            if inst.descriptor().configured:
                try:
                    prompt = f"You are a technical translator. Translate the following open-source contribution guidance into {target_lang}.\nPreserve all code blocks, file paths, and technical terms exactly as-is. Output only the translation."
                    
                    request = ModelRequest(
                        model=inst.descriptor().default_models[0],
                        messages=[
                            ChatMessage(role="system", content=prompt),
                            ChatMessage(role="user", content=text)
                        ],
                        max_tokens=2000
                    )
                    response = await inst.complete(request)
                    translated = response.content
                    
                    await self.audit.record(AuditRecord(
                        action="language_service",
                        actor="language_service",
                        status="completed",
                        input_summary=f"en -> {target_lang}",
                        output_summary=f"{len(translated)} chars",
                        metadata={"context": context}
                    ))
                    return translated, None
                except Exception as e:
                    logger.error(f"Translation failed: {e}")
                    return text, "Translation unavailable, showing English"
                    
        return text, "Translation unavailable, showing English"
