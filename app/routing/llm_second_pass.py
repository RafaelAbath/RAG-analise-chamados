from routing.base import Router
from routing.utils import clean_setor
from routing.patterns import COLLECTION_RULES
from core.config import settings
from openai import OpenAI

class LLMSecondPassRouter(Router):
    def __init__(self, successor=None):
        super().__init__(successor)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.allowed = sorted({
            setor
            for rules in COLLECTION_RULES.values()
            for _, setor in rules
        })

    def _route(self, chamado):
        msgs = [
            {
                "role": "system",
                "content": (
                    "Você é um roteador de chamados. Responda APENAS com um dos setores válidos:\n"
                    + ", ".join(self.allowed)
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Protocolo: {chamado.protocolo}\n"
                    f"Descrição: {chamado.descricao}"
                ),
            },
        ]
        raw = self.openai.chat.completions.create(
            model=settings.FINETUNED_MODEL,
            messages=msgs,
            temperature=0.0,
        )
        setor = clean_setor(raw.choices[0].message.content.strip())
        chamado.proveniencia = "llm"
        return setor
