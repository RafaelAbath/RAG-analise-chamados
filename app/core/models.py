from pydantic import BaseModel
from typing import Any, Dict, Optional

class Chamado(BaseModel):
    protocolo: str
    descricao: str
    collection: Optional[str] = None
    proveniencia: Optional[str] = None 

class Resposta(BaseModel):
    setor_ia: str
    tecnico_id: int
    tecnico_nome: str
    tecnico_setor: str
    confianca: float
    proveniencia: str 
    collection: str

class RespostaDebug(Resposta):
    raw_model_response: Dict[str, Any]

class Config:
        orm_mode = True