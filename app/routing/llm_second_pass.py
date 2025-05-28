from routing.base import Router
from routing.utils import clean_setor
from routing.patterns import COLLECTION_RULES
from core.config import settings
from openai import OpenAI

class LLMSecondPassRouter(Router):
    def __init__(self, successor=None):
        super().__init__(successor)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _route(self, chamado: Chamado) -> str:
        
        coll = getattr(chamado, "collection", None) or "geral"
        
        options = [setor for _, setor in COLLECTION_RULES.get(coll, [])]

        
        system_msg = (
            f"Você é um roteador de chamados para a coleção “{coll}”.\n"
            "Responda **exatamente** com **um** destes setores **sem nada mais**:\n"
            + "\n".join(f"- {s}" for s in options)
        )
        user_msg = f"Protocolo: {chamado.protocolo}\nDescrição: {chamado.descricao}"

        raw = self.openai.chat.completions.create(
            model=settings.FINETUNED_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.0,
        ).choices[0].message.content.strip()

        
        setor = clean_setor(raw, options)
        chamado.proveniencia = "llm"
        return setor
