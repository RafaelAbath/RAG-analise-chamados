from routing.keywords import KeywordRouter
from routing.finance import FinanceOverrideRouter
from routing.llm import LLMRouter

# Monta a cadeia de roteadores
router_chain = KeywordRouter(
    FinanceOverrideRouter(
        LLMRouter()
    )
)