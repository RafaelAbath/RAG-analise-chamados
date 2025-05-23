from .keywords       import KeywordRouter
from .classification import ClassificationRouter
from .llm            import LLMRouter

keyword_router        = KeywordRouter()
classification_router = ClassificationRouter()
llm_router            = LLMRouter()


keyword_router.set_successor(classification_router)
classification_router.set_successor(llm_router)


router_chain = keyword_router