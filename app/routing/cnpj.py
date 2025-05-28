import re
from typing import Optional
from core.config import settings
from core.models import Chamado
from routing.base import Router

class CnpjRouter(Router):
    def _route(self, chamado: Chamado) -> Optional[str]:
        # Só dispara quando a collection já for "financeiros"
        if getattr(chamado, "collection", None) != settings.QDRANT_COLL_FIN:
            return None

        # Extrai apenas dígitos e busca CNPJs configurados
        digits = re.sub(r"\D", "", f"{chamado.protocolo}{chamado.descricao}")
        for cnpj in settings.CNPJS_FAT_BRUTO:  # carrega do .env → FAT_BRUTO_CNPJ_FILE :contentReference[oaicite:0]{index=0}
            if cnpj and cnpj in digits:
                chamado.proveniencia = "cnpj"
                return "Faturamento Bruto"
        return None
