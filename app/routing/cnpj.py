import re
from typing import Optional
from core.config import settings
from .base import Router

CNPJS_FAT_BRUTO = settings.CNPJS_FAT_BRUTO

class CnpjRouter(Router):
    """Se encontrar CNPJ da lista ⇒ setor 'Faturamento Bruto'."""

    def _route(self, chamado) -> Optional[str]:
        if not CNPJS_FAT_BRUTO:
            return None

        digits = re.sub(r"\D", "", f"{chamado.titulo}{chamado.descricao}")
        for cnpj in CNPJS_FAT_BRUTO:
            if cnpj and cnpj in digits:
                # opcional: marque a proveniência
                chamado.proveniencia = "cnpj"
                return "Faturamento Bruto"
        return None