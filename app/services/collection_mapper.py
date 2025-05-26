from core.config import settings

SECTOR2COLL = {
    "Autorização"                              : settings.QDRANT_COLL_AUTH,
    "OPME"                                     : settings.QDRANT_COLL_AUTH,
    "Medicamento"                              : settings.QDRANT_COLL_AUTH,
    "TEA/TGD/TDAH"                             : settings.QDRANT_COLL_AUTH,
    "Garantia de Atendimento (Busca de rede)"  : settings.QDRANT_COLL_AUTH,

    "Judiciais + NIPs"                         : settings.QDRANT_COLL_NIPS,
    "NIP Reclames e judiciais OPME"            : settings.QDRANT_COLL_NIPS,
    "NIP Reclames e judiciais HC"              : settings.QDRANT_COLL_NIPS,
    "NIP Casos especiais Faturamento"          : settings.QDRANT_COLL_NIPS,
    "NIP + Judicial Reembolso"                 : settings.QDRANT_COLL_NIPS,
    "NIP + G.A."                               : settings.QDRANT_COLL_NIPS,

    "Faturamento"                              : settings.QDRANT_COLL_FIN,
    "Financeiro / Tributos"                    : settings.QDRANT_COLL_FIN,
    "Faturamento Bruto"                        : settings.QDRANT_COLL_FIN,

    "Reembolso"                                : settings.QDRANT_COLL_REEMB,
    "Negociação"                               : settings.QDRANT_COLL_REEMB,

    "Odonto Faturamento"                       : settings.QDRANT_COLL_ODO,
    "Odonto Reembolso"                         : settings.QDRANT_COLL_ODO,
    "Odonto Autorização"                       : settings.QDRANT_COLL_ODO,

    "Home Care"                                : settings.QDRANT_COLL_GERAL,
    "Prévia de Reembolso + Programas"          : settings.QDRANT_COLL_GERAL,
    "Credenciamento + Termo Aditivo"           : settings.QDRANT_COLL_GERAL,
}

def collection_for(setor: str) -> str:
    return SECTOR2COLL.get(setor, settings.QDRANT_COLL_GERAL)