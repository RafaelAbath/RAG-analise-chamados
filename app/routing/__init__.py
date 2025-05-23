from .keywords       import KeywordRouter
from .classification import ClassificationRouter
from .llm            import LLMRouter
from .cnpj           import CnpjRouter

cnpj_router           = CnpjRouter()
keyword_router        = KeywordRouter()
classification_router = ClassificationRouter()
llm_router            = LLMRouter()

classification_router.set_successor(cnpj_router)
keyword_router.set_successor(classification_router)
classification_router.set_successor(llm_router)



router_chain = classification_router