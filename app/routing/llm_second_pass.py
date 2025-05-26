# routing/llm_second_pass.py
from routing.base import Router
from routing.utils import clean_setor, get_allowed_sectors
from core.config import settings
from openai import OpenAI

class LLMSecondPassRouter(Router):
    def __init__(self, successor=None):
        super().__init__(successor)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.allowed = get_allowed_sectors()

    def _route(self, chamado):
        msgs = [
            {
                "role": "system",
                "content": (
                    "Você é um roteador de chamados. Responda apenas com um dos setores válidos:\n"
                    + ", ".join(self.allowed)
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Protocolo: {chamado.protocolo}\n"
                    f"Descrição: {chamado.descricao}\n"
                    f"Classificação extra: {chamado.classificacao or '—'}"
                ),
            },
        ]
        raw = self.openai.chat.completions.create(
            model=settings.FINETUNED_MODEL,
            messages=msgs,
            temperature=0.0,
        )
        return clean_setor(raw.choices[0].message.content.strip())
