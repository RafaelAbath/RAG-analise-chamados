import re
from typing import Optional
from core.config import settings
from .base import BaseRouter

CNPJS_FAT_BRUTO = settings.CNPJS_FAT_BRUTO

class CnpjRouter(BaseRouter):
    def handle(self, chamado) -> Optional[str]:
        if not CNPJS_FAT_BRUTO:
            return super().handle(chamado)

        digits = re.sub(r"\D", "", f"{chamado.titulo}{chamado.descricao}")
        for cnpj in CNPJS_FAT_BRUTO:
            if cnpj and cnpj in digits:
                
                return "Faturamento Bruto"
        return super().handle(chamado)
