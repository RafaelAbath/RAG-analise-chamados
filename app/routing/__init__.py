from .keywords           import KeywordRouter
from .collection_router  import CollectionRouter
from .collection_rules   import CollectionRuleRouter
from .classification     import ClassificationRouter   # opcional, pode virar heurística extra
from .llm_second_pass    import LLMSecondPassRouter

kw_router      = KeywordRouter()
coll_router    = CollectionRouter()
rule_router    = CollectionRuleRouter()
fallback_router = LLMSecondPassRouter()


kw_router.set_successor(coll_router)
coll_router.set_successor(rule_router)
rule_router.set_successor(fallback_router)

router_chain = kw_router

llm_router = fallback_router          # LLMSecondPassRouter
__all__ = ["router_chain", "llm_router"]