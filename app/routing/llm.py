from typing import Optional
from openai import OpenAI
from core.config import settings
from core.text_utils import clean_setor
from core.sector_meta import allowed_sectors
from core.models import Chamado

class LLMRouter(Router):
    def __init__(self, successor: Optional[Router] = None):
        super().__init__(successor)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.FINETUNED_MODEL

    def _route(self, chamado: Chamado) -> Optional[str]:
        system_msg = (
            "Você é um roteador de chamados. Responda APENAS com um dos setores válidos:\n" +
            ", ".join(allowed_sectors)
        )
        user_msg = f"Título: {chamado.titulo}\nDescrição: {chamado.descricao}"
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"system","content":system_msg},
                      {"role":"user","content":user_msg}],
            temperature=0.0
        )
        bruto = clean_setor(resp.choices[0].message.content.strip())
        return bruto if bruto in allowed_sectors else None