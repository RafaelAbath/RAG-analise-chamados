from openai import OpenAI
from routing.base import Router
from routing.utils import get_allowed_sectors
from core.text_utils import clean_setor
from core.config import settings

class LLMRouter(Router):
    def __init__(self):
        super().__init__()
        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.allowed_sectors = get_allowed_sectors()

    def _route(self, chamado):
        system_msg = (
            "Você é um roteador de chamados. Responda APENAS com um dos setores válidos:\n"
            + ", ".join(self.allowed_sectors)
        )
        user_msg = f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}"
        resp = self.llm.chat.completions.create(
            model=settings.FINETUNED_MODEL,
            messages=[{"role":"system","content":system_msg},
                      {"role":"user",  "content":user_msg}],
            temperature=0.0
        )
        bruto = clean_setor(resp.choices[0].message.content.strip())
        if bruto not in self.allowed_sectors:
            return None
        return bruto
