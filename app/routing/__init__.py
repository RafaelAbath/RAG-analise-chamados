from .keywords       import KeywordRouter
from .classification import ClassificationRouter
from .llm            import LLMRouter

keyword_router        = KeywordRouter()
classification_router = ClassificationRouter()
llm_router            = LLMRouter()

# NOVA ordem: classify → keywords → llm
classification_router.set_successor(keyword_router)
keyword_router.set_successor(llm_router)

router_chain = classification_router       # agora o “head” é o ClassificationRouter
