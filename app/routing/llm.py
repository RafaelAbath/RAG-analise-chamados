import unicodedata
from typing import Optional, List
from openai import OpenAI
from core.config import settings
from core.models import Chamado
from routing.base import Router

openai = OpenAI(api_key=settings.OPENAI_API_KEY)

class LLMRouter(Router):
    """
    Fallback router que envia o texto ao modelo finetuned para inferir o setor.
    Usa a lista de setores válidos de `settings.ALLOWED_SECTORS`.
    """
    def _route(self, chamado: Chamado) -> Optional[str]:
        system_msg = (
            "Você é um roteador de chamados. Responda apenas com um dos setores válidos:\n"
            + ", ".join(settings.ALLOWED_SECTORS)
        )
        user_msg = f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}"

        
        resp = openai.chat.completions.create(
            model=settings.FINETUNED_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.0,
        )
        raw = resp.choices[0].message.content.strip()
        setor = self._clean_setor(raw)

        
        if setor not in settings.ALLOWED_SECTORS:
           
            from difflib import get_close_matches
            match = get_close_matches(setor, settings.ALLOWED_SECTORS, n=1, cutoff=0.6)
            return match[0] if match else None

        return setor

    def _clean_setor(self, raw: str) -> str:
        
        return raw.split(":", 1)[1].strip() if ":" in raw else raw.strip()
