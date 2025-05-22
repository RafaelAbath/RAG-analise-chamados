from routing.keywords        import KeywordRouter
from routing.classification import ClassificationRouter
from routing.llm            import LLMRouter

router_chain = KeywordRouter(
    ClassificationRouter(
        LLMRouter()
    )
)