from typing import Optional
from core.config import settings

# Palavras-chave para identificar NIP/Reclames/ANS/Judiciais
NIP_KEYS = ("nip", "ans", "judicial", "reclame")

# Setores que caem na coleção de autorização geral
AUT_SETS = {
    "Autorização",
    "Medicamento",
    "Garantia de Atendimento (Busca de rede)",
}


def collection_for(setor: str, classificacao: Optional[str] = None) -> str:
 
    # 1) Autorização geral
    if setor in AUT_SETS:
        return settings.QDRANT_COLLECTION_AUT
    
    # 2) NIP/Reclames/ANS/Judiciais via substring no lowercase
    lower = setor.lower()
    if any(key in lower for key in NIP_KEYS):
        return settings.QDRANT_COLLECTION_NIP

    # 3) Default
    return settings.QDRANT_COLLECTION
