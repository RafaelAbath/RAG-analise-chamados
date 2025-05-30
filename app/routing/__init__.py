from .collection_router  import CollectionRouter
from .collection_rules   import CollectionRuleRouter 
from .llm_second_pass    import LLMSecondPassRouter
from .cnpj                 import CnpjRouter

coll_router    = CollectionRouter()
rule_router    = CollectionRuleRouter()
fallback_router = LLMSecondPassRouter()
cnpj_router     = CnpjRouter()


coll_router.set_successor(rule_router)
rule_router.set_successor(fallback_router)
cnpj_router.set_successor(fallback_router)

router_chain = coll_router

llm_router = fallback_router          
__all__ = ["router_chain", "llm_router"]