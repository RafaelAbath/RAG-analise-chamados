import re
from typing import Optional
from core.models import Chamado
from core.text_utils import normalize_text
from routing.base import Router

class ClassificationRouter(Router):
    opme_patterns = [
        'credenciado ativo',
        'manutencao de contrato',
        'autorizacao previa',
        'senhas',
        'guias',
        'revisao de ap negada',
        'sobre ap em andamento',
        'tratar pedido de revisao',
        'tratar solicitacao de prioridade'
    ]
    ga_patterns = [
        'agendamento',
        'garantia de atendimento',
        'reembolso integral'
    ]

    def _route(self, chamado: Chamado) -> Optional[str]:
        if not chamado.classificacao:
            return None

        norm = normalize_text(chamado.classificacao)

        
        opme_count = sum(1 for pat in self.opme_patterns if pat in norm)
        if opme_count >= 3:
            return 'OPME'

        
        if any(pat in norm for pat in self.ga_patterns):
            return 'Garantia de Atendimento (Busca de rede)'

        return None
