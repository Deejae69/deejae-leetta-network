"""Agent sub-package — six autonomous AI agents for the DeeJae LeEtta Network."""

from deejae.agents.base import BaseAgent
from deejae.agents.mmo_customer import MMOCustomerAgent
from deejae.agents.ecommerce import EcommerceClientFinderAgent
from deejae.agents.arts_marketing import ArtsMarketingAgent
from deejae.agents.investor_relations import InvestorRelationsAgent
from deejae.agents.trading_strategy import TradingStrategyAgent
from deejae.agents.campaign_optimizer import CampaignOptimizerAgent

REGISTRY: dict[str, type[BaseAgent]] = {
    "mmo_customer": MMOCustomerAgent,
    "ecommerce": EcommerceClientFinderAgent,
    "arts_marketing": ArtsMarketingAgent,
    "investor_relations": InvestorRelationsAgent,
    "trading_strategy": TradingStrategyAgent,
    "campaign_optimizer": CampaignOptimizerAgent,
}

__all__ = [
    "BaseAgent",
    "MMOCustomerAgent",
    "EcommerceClientFinderAgent",
    "ArtsMarketingAgent",
    "InvestorRelationsAgent",
    "TradingStrategyAgent",
    "CampaignOptimizerAgent",
    "REGISTRY",
]
