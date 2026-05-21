"""
Unit tests for all individual agent implementations.

Covers execute_task, learn_from_result, and any public helper methods for:
  - MMOCustomerAgent
  - ECommerceClientFinder
  - ArtsMarketingAgent
  - CampaignOptimizerAgent
  - InvestorRelationsAgent
  - TradingStrategyAgent
"""

import pytest
from agents.base_agent import AgentTask


def _task(task_type, data=None, task_id="t1", priority=5):
    return AgentTask(
        task_id=task_id,
        task_type=task_type,
        priority=priority,
        data=data or {},
    )


# ===========================================================================
# MMOCustomerAgent
# ===========================================================================

class TestMMOCustomerAgent:
    def setup_method(self):
        from agents.mmo_customer_agent import MMOCustomerAgent
        self.agent = MMOCustomerAgent()

    def test_initialization(self):
        assert self.agent.name == "MMO Customer Agent"
        assert self.agent.is_active is True
        assert len(self.agent.target_audiences) > 0

    def test_identify_prospects(self):
        result = self.agent.execute_task(_task("identify_prospects", {"audience": "gamers"}))
        assert result["audience"] == "gamers"
        assert "estimated_size" in result
        assert "recommended_channels" in result

    def test_identify_prospects_default_audience(self):
        result = self.agent.execute_task(_task("identify_prospects"))
        assert result["audience"] == "general"

    def test_create_campaign(self):
        result = self.agent.execute_task(_task("create_campaign", {
            "type": "awareness",
            "channel": "discord"
        }))
        assert "campaign_id" in result
        assert result["channel"] == "discord"
        assert result["type"] == "awareness"
        assert len(self.agent.campaign_history) == 1

    def test_create_campaign_message_types(self):
        for campaign_type in ("awareness", "engagement", "conversion"):
            result = self.agent.execute_task(_task("create_campaign", {"type": campaign_type}))
            assert len(result["message"]) > 0

    def test_engage_user(self):
        result = self.agent.execute_task(_task("engage_user", {
            "user_id": "u123",
            "type": "welcome"
        }))
        assert result["user_id"] == "u123"
        assert result["message_sent"] is True

    def test_analyze_conversion(self):
        result = self.agent.execute_task(_task("analyze_conversion", {
            "channel": "twitter",
            "conversions": 5,
            "impressions": 100,
        }))
        assert result["channel"] == "twitter"
        assert result["conversion_rate"] == pytest.approx(0.05)
        assert result["converted"] is True

    def test_analyze_conversion_zero_impressions(self):
        result = self.agent.execute_task(_task("analyze_conversion", {
            "channel": "discord",
            "conversions": 0,
            "impressions": 0,
        }))
        assert result["conversion_rate"] == 0

    def test_unknown_task_type(self):
        result = self.agent.execute_task(_task("nonexistent"))
        assert result["status"] == "unknown_task_type"

    def test_learn_from_conversion_updates_metrics(self):
        task = _task("analyze_conversion", {"channel": "twitter", "conversions": 3, "impressions": 100})
        result = self.agent.execute_task(task)
        before = self.agent.metrics.conversions
        self.agent.learn_from_result(task, result)
        assert self.agent.metrics.conversions > before
        assert self.agent.metrics.total_revenue_generated > 0

    def test_get_best_channels_empty(self):
        assert self.agent.get_best_channels() == []

    def test_get_best_channels_ranked(self):
        task = _task("analyze_conversion", {"channel": "discord", "conversions": 10, "impressions": 100})
        result = self.agent.execute_task(task)
        self.agent.learn_from_result(task, result)
        channels = self.agent.get_best_channels()
        assert "discord" in channels


# ===========================================================================
# ECommerceClientFinder
# ===========================================================================

class TestECommerceClientFinder:
    def setup_method(self):
        from agents.ecommerce_client_finder import ECommerceClientFinder
        self.agent = ECommerceClientFinder()

    def test_initialization(self):
        assert self.agent.name == "E-Commerce Client Finder"
        assert len(self.agent.product_categories) > 0

    def test_find_clients(self):
        result = self.agent.execute_task(_task("find_clients", {"category": "art", "source": "organic"}))
        assert result["category"] == "art"
        assert result["potential_clients"] >= 0
        assert "contact_list" in result

    def test_segment_customers_high_value(self):
        customers = [{"lifetime_value": 600}, {"lifetime_value": 200}]
        result = self.agent.execute_task(_task("segment_customers", {"customers": customers}))
        assert result["segments"]["high_value"] == 1
        assert result["segments"]["new_customers"] == 1

    def test_segment_customers_repeat_buyers(self):
        customers = [{"purchase_count": 5, "lifetime_value": 400}]
        result = self.agent.execute_task(_task("segment_customers", {"customers": customers}))
        assert result["segments"]["repeat_buyers"] == 1

    def test_segment_customers_at_risk(self):
        customers = [{"days_since_last_purchase": 100, "lifetime_value": 0, "purchase_count": 0}]
        result = self.agent.execute_task(_task("segment_customers", {"customers": customers}))
        assert result["segments"]["at_risk"] == 1

    def test_segment_customers_empty(self):
        result = self.agent.execute_task(_task("segment_customers", {"customers": []}))
        for segment in ("high_value", "repeat_buyers", "at_risk", "new_customers"):
            assert result["segments"][segment] == 0

    def test_optimize_funnel(self):
        result = self.agent.execute_task(_task("optimize_funnel", {
            "funnel_name": "main",
            "data": {"visitors": 1000, "product_views": 400, "add_to_cart": 150, "checkout": 80, "purchases": 50},
        }))
        assert result["funnel_name"] == "main"
        assert "overall_conversion" in result
        assert result["overall_conversion"] == pytest.approx(0.05)

    def test_optimize_funnel_with_zero_visitors(self):
        result = self.agent.execute_task(_task("optimize_funnel", {
            "funnel_name": "empty",
            "data": {"visitors": 0},
        }))
        assert result["stages"]["visitor_to_view"] == 0

    def test_track_purchase(self):
        result = self.agent.execute_task(_task("track_purchase", {
            "category": "art",
            "amount": 120.0,
            "customer_id": "c42",
        }))
        assert result["product_category"] == "art"
        assert result["amount"] == 120.0
        assert result["customer_id"] == "c42"

    def test_learn_from_purchase_updates_metrics(self):
        task = _task("track_purchase", {"category": "music", "amount": 50.0, "customer_id": "c1"})
        result = self.agent.execute_task(task)
        self.agent.learn_from_result(task, result)
        assert self.agent.metrics.conversions == 1
        assert self.agent.metrics.total_revenue_generated == pytest.approx(50.0)
        assert self.agent.customer_segments["music"]["purchases"] == 1

    def test_unknown_task_type(self):
        result = self.agent.execute_task(_task("bad_task"))
        assert result["status"] == "unknown_task_type"


# ===========================================================================
# ArtsMarketingAgent
# ===========================================================================

class TestArtsMarketingAgent:
    def setup_method(self):
        from agents.arts_marketing_agent import ArtsMarketingAgent
        self.agent = ArtsMarketingAgent()

    def test_initialization(self):
        assert self.agent.name == "Arts Marketing Agent"
        assert len(self.agent.content_types) > 0

    def test_create_content(self):
        result = self.agent.execute_task(_task("create_content", {"type": "music", "theme": "summer"}))
        assert "content_id" in result
        assert result["type"] == "music"
        assert len(result["caption"]) > 0
        assert isinstance(result["hashtags"], list)

    def test_create_content_all_types(self):
        for ct in ("music", "visual_art", "performance", "digital_art"):
            result = self.agent.execute_task(_task("create_content", {"type": ct, "theme": "x"}))
            assert result["type"] == ct

    def test_schedule_post(self):
        result = self.agent.execute_task(_task("schedule_post", {
            "platform": "instagram",
            "content_id": "art_1",
            "schedule_time": "2026-06-01T10:00:00",
        }))
        assert result["platform"] == "instagram"
        assert result["status"] == "scheduled"

    def test_analyze_engagement(self):
        result = self.agent.execute_task(_task("analyze_engagement", {
            "platform": "twitter",
            "content_type": "music",
            "likes": 100,
            "comments": 20,
            "shares": 30,
            "views": 1000,
        }))
        assert result["engagement_rate"] == pytest.approx(0.15)
        assert result["total_engagement"] == 150
        assert result["best_performing_metric"] == "likes"

    def test_analyze_engagement_zero_views(self):
        result = self.agent.execute_task(_task("analyze_engagement", {
            "platform": "instagram",
            "content_type": "visual_art",
            "views": 0,
        }))
        assert result["engagement_rate"] == 0

    def test_collaborate(self):
        result = self.agent.execute_task(_task("collaborate", {"artist_type": "musician"}))
        assert "potential_collaborators" in result
        assert "collaboration_types" in result

    def test_learn_from_engagement_updates_analytics(self):
        task = _task("analyze_engagement", {
            "platform": "tiktok",
            "content_type": "music",
            "likes": 50, "comments": 5, "shares": 10, "views": 500,
        })
        result = self.agent.execute_task(task)
        self.agent.learn_from_result(task, result)
        assert "tiktok_music" in self.agent.engagement_analytics

    def test_get_best_platforms_default_when_empty(self):
        platforms = self.agent.get_best_platforms()
        assert platforms == self.agent.social_platforms

    def test_get_best_platforms_ranked_after_data(self):
        task = _task("analyze_engagement", {
            "platform": "youtube",
            "content_type": "performance",
            "likes": 200, "comments": 50, "shares": 100, "views": 1000,
        })
        result = self.agent.execute_task(task)
        self.agent.learn_from_result(task, result)
        platforms = self.agent.get_best_platforms()
        assert "youtube" in platforms

    def test_unknown_task_type(self):
        result = self.agent.execute_task(_task("bogus"))
        assert result["status"] == "unknown_task_type"


# ===========================================================================
# CampaignOptimizerAgent
# ===========================================================================

class TestCampaignOptimizerAgent:
    def setup_method(self):
        from agents.campaign_optimizer_agent import CampaignOptimizerAgent
        self.agent = CampaignOptimizerAgent()

    def test_initialization(self):
        assert self.agent.name == "Campaign Optimizer Agent"

    def test_analyze_campaign(self):
        result = self.agent.execute_task(_task("analyze_campaign", {
            "campaign_id": "c1",
            "channel": "instagram",
            "metrics": {
                "impressions": 10000,
                "clicks": 300,
                "conversions": 30,
                "cost": 500,
                "avg_order_value": 100,
            },
        }))
        assert result["campaign_id"] == "c1"
        assert "performance_score" in result
        assert "kpis" in result
        assert result["kpis"]["ctr"] == pytest.approx(0.03)

    def test_analyze_campaign_zero_impressions(self):
        result = self.agent.execute_task(_task("analyze_campaign", {
            "campaign_id": "c0",
            "metrics": {"impressions": 0, "clicks": 0, "conversions": 0, "cost": 0},
        }))
        assert result["kpis"]["ctr"] == 0

    def test_optimize_budget_proportional(self):
        # Pre-load performance for two campaigns
        self.agent.campaign_performance = {"c1": 80, "c2": 20}
        result = self.agent.execute_task(_task("optimize_budget", {
            "total_budget": 1000,
            "campaigns": [{"campaign_id": "c1"}, {"campaign_id": "c2"}],
        }))
        alloc = result["allocation"]
        assert alloc["c1"] > alloc["c2"]
        assert sum(alloc.values()) == pytest.approx(1000)

    def test_optimize_budget_no_campaigns(self):
        result = self.agent.execute_task(_task("optimize_budget", {
            "total_budget": 1000, "campaigns": [],
        }))
        assert result["status"] == "no_campaigns"

    def test_predict_performance(self):
        result = self.agent.execute_task(_task("predict_performance", {
            "config": {"channel": "twitter", "budget": 500},
        }))
        assert "predicted_performance_score" in result
        assert "confidence" in result

    def test_recommend_channels_no_history(self):
        result = self.agent.execute_task(_task("recommend_channels", {
            "type": "awareness", "target_audience": "general",
        }))
        assert "recommended_channels" in result
        assert len(result["recommended_channels"]) <= 3

    def test_recommend_channels_with_history(self):
        self.agent.channel_scores = {"discord": [80, 90], "twitter": [60]}
        result = self.agent.execute_task(_task("recommend_channels", {}))
        top = result["recommended_channels"][0]["channel"]
        assert top == "discord"

    def test_learn_from_campaign_updates_performance(self):
        task = _task("analyze_campaign", {
            "campaign_id": "cx",
            "channel": "discord",
            "metrics": {"impressions": 5000, "clicks": 150, "conversions": 15, "cost": 200, "avg_order_value": 80},
        })
        result = self.agent.execute_task(task)
        self.agent.learn_from_result(task, result)
        assert "cx" in self.agent.campaign_performance
        assert "discord" in self.agent.channel_scores

    def test_generate_recommendation_scale_up(self):
        rec = self.agent._generate_recommendation(performance_score=80, roi=2.0)
        assert rec == "scale_up"

    def test_generate_recommendation_pause(self):
        rec = self.agent._generate_recommendation(performance_score=20, roi=0.0)
        assert rec == "pause_or_restructure"

    def test_unknown_task_type(self):
        result = self.agent.execute_task(_task("noop"))
        assert result["status"] == "unknown_task_type"


# ===========================================================================
# InvestorRelationsAgent
# ===========================================================================

class TestInvestorRelationsAgent:
    def setup_method(self):
        from agents.investor_relations_agent import InvestorRelationsAgent
        self.agent = InvestorRelationsAgent()

    def test_initialization(self):
        assert self.agent.name == "Investor Relations Agent"
        assert self.agent.traction_metrics["users"] == 0

    def test_identify_investors(self):
        result = self.agent.execute_task(_task("identify_investors", {
            "stage": "seed", "focus": "blockchain",
        }))
        assert result["stage"] == "seed"
        assert len(result["potential_investors"]) > 0
        assert len(self.agent.investor_pool) > 0

    def test_create_pitch(self):
        result = self.agent.execute_task(_task("create_pitch", {
            "type": "deck", "funding_amount": "2M",
        }))
        assert "sections" in result
        assert result["funding_ask"] == "2M"
        assert "key_metrics" in result

    def test_track_traction(self):
        result = self.agent.execute_task(_task("track_traction", {
            "users": 500, "revenue": 5000.0, "d33j_holders": 200,
        }))
        assert result["current_metrics"]["users"] == 500
        assert result["current_metrics"]["revenue"] == 5000.0
        assert "investor_readiness_score" in result

    def test_track_traction_growth_calculation(self):
        result = self.agent.execute_task(_task("track_traction", {
            "users": 200, "previous_users": 100,
        }))
        assert self.agent.traction_metrics["monthly_growth"] == pytest.approx(1.0)

    def test_track_traction_neutral_when_no_previous(self):
        result = self.agent.execute_task(_task("track_traction", {"users": 100}))
        assert result["growth_trend"] in ("positive", "neutral")

    def test_prepare_update(self):
        result = self.agent.execute_task(_task("prepare_update", {"period": "monthly"}))
        assert result["period"] == "monthly"
        assert "highlights" in result
        assert "next_steps" in result

    def test_learn_from_traction_updates_metrics(self):
        task = _task("track_traction", {"users": 300, "revenue": 2000.0})
        result = self.agent.execute_task(task)
        self.agent.learn_from_result(task, result["current_metrics"])
        assert self.agent.traction_metrics["users"] == 300

    def test_investor_readiness_zero(self):
        score = self.agent._calculate_investor_readiness()
        assert score == 0.0

    def test_investor_readiness_partial(self):
        self.agent.traction_metrics["users"] = 200
        self.agent.traction_metrics["revenue"] = 5000
        score = self.agent._calculate_investor_readiness()
        assert 0 < score < 1.0

    def test_investor_readiness_max(self):
        self.agent.traction_metrics["users"] = 2000
        self.agent.traction_metrics["revenue"] = 20000
        self.agent.traction_metrics["monthly_growth"] = 0.3
        self.agent.traction_metrics["d33j_holders"] = 600
        score = self.agent._calculate_investor_readiness()
        assert score == pytest.approx(1.0)

    def test_unknown_task_type(self):
        result = self.agent.execute_task(_task("unknown"))
        assert result["status"] == "unknown_task_type"


# ===========================================================================
# TradingStrategyAgent
# ===========================================================================

class TestTradingStrategyAgent:
    def setup_method(self):
        from agents.trading_strategy_agent import TradingStrategyAgent
        self.agent = TradingStrategyAgent()

    def test_initialization(self):
        assert self.agent.name == "Trading Strategy Agent"
        assert self.agent.portfolio_value == pytest.approx(10000.0)
        assert self.agent.trading_engine is not None

    def test_analyze_market(self):
        market_data = {
            "symbol": "BTC",
            "price": 50000,
            "historical_prices": [49000] * 30 + [50000],
        }
        result = self.agent.execute_task(_task("analyze_market", {"market_data": market_data}))
        assert result["symbol"] == "BTC"
        assert "signals_generated" in result
        assert "recommendation" in result

    def test_analyze_market_recommendation_values(self):
        market_data = {"symbol": "ETH", "price": 3000, "historical_prices": [3000] * 31}
        result = self.agent.execute_task(_task("analyze_market", {"market_data": market_data}))
        assert result["recommendation"] in ("buy", "sell", "hold")

    def test_execute_trade_no_signal(self):
        result = self.agent.execute_task(_task("execute_trade", {}))
        assert result["success"] is False
        assert "error" in result

    def test_execute_trade_buy_signal(self):
        result = self.agent.execute_task(_task("execute_trade", {
            "signal": {
                "symbol": "BTC",
                "signal_type": "buy",
                "price": 50000.0,
                "confidence": 0.8,
                "strategy": "test",
            }
        }))
        assert result["success"] is True
        assert result["symbol"] == "BTC"

    def test_execute_trade_sell_signal(self):
        result = self.agent.execute_task(_task("execute_trade", {
            "signal": {
                "symbol": "ETH",
                "signal_type": "sell",
                "price": 3000.0,
                "confidence": 0.7,
                "strategy": "test",
            }
        }))
        assert result["success"] is True

    def test_monitor_positions(self):
        result = self.agent.execute_task(_task("monitor_positions", {
            "market_data": {"symbol": "BTC", "price": 51000},
        }))
        assert "portfolio_value" in result
        assert "open_positions" in result

    def test_rebalance_portfolio(self):
        result = self.agent.execute_task(_task("rebalance_portfolio", {
            "target_allocation": {"BTC": 0.5, "cash": 0.5},
        }))
        assert result["status"] == "completed"
        assert "previous_allocation" in result

    def test_learn_from_trade_updates_portfolio(self):
        task = _task("execute_trade", {
            "signal": {"symbol": "BTC", "signal_type": "buy", "price": 50000.0,
                       "confidence": 0.8, "strategy": "test"}
        })
        result = self.agent.execute_task(task)
        initial_value = self.agent.portfolio_value
        trade_result = {"success": True, "pnl": 200.0}
        self.agent.learn_from_result(task, trade_result)
        assert self.agent.portfolio_value == pytest.approx(initial_value + 200.0)
        assert len(self.agent.trade_history) == 1

    def test_get_performance_metrics(self):
        metrics = self.agent.get_performance_metrics()
        assert "portfolio_value" in metrics
        assert "total_trades" in metrics
        assert "win_rate" in metrics
        assert "mode" in metrics

    def test_determine_recommendation_buy(self):
        from scripts.trading_strategy import TradingSignal, SignalType
        from datetime import datetime
        signals = [
            TradingSignal("X", SignalType.BUY, 100, 0.8, datetime.now(), "s1"),
            TradingSignal("X", SignalType.BUY, 100, 0.9, datetime.now(), "s2"),
            TradingSignal("X", SignalType.SELL, 100, 0.5, datetime.now(), "s3"),
        ]
        rec = self.agent._determine_recommendation(signals)
        assert rec == "buy"

    def test_determine_recommendation_sell(self):
        from scripts.trading_strategy import TradingSignal, SignalType
        from datetime import datetime
        signals = [
            TradingSignal("X", SignalType.SELL, 100, 0.9, datetime.now(), "s1"),
            TradingSignal("X", SignalType.SELL, 100, 0.8, datetime.now(), "s2"),
        ]
        rec = self.agent._determine_recommendation(signals)
        assert rec == "sell"

    def test_determine_recommendation_hold_on_empty(self):
        rec = self.agent._determine_recommendation([])
        assert rec == "hold"

    def test_unknown_task_type(self):
        result = self.agent.execute_task(_task("invalid"))
        assert result["status"] == "unknown_task_type"
