from routing.keywords import KeywordRouter
from routing.finance import FinanceOverrideRouter
from routing.llm import LLMRouter

# Monta a corrente de roteamento
router_chain = KeywordRouter(
    FinanceOverrideRouter(
        LLMRouter()
    )
)