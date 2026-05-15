"""
Investor Relations Agent
Autonomous AI agent for identifying and engaging potential investors
"""

import asyncio
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import random


@dataclass
class InvestorProfile:
    """Profile of a potential investor"""
    id: str
    name: str
    investor_type: str  # angel, vc, strategic, crypto_fund
    focus_areas: List[str]
    investment_range: str
    portfolio: List[str]
    contact_info: Dict
    interest_score: float
    last_interaction: Optional[datetime]
    meeting_status: str  # cold, contacted, meeting_scheduled, pitched, negotiating
    metadata: Dict


@dataclass
class Investment:
    """Investment deal tracking"""
    id: str
    investor_id: str
    amount: float
    stage: str
    terms: Dict
    status: str
    created_at: datetime


class InvestorRelationsAgent:
    """
    AI Agent for Investor Relations and Outreach

    Features:
    - Investor identification and profiling
    - Automated outreach and relationship building
    - Pitch optimization based on investor preferences
    - Deal pipeline management
    - Network event identification and preparation
    """

    def __init__(self, config: Dict):
        self.config = config
        self.investors: List[InvestorProfile] = []
        self.investments: List[Investment] = []
        self.pitch_versions: Dict = {}
        self.performance_metrics = {
            'investors_identified': 0,
            'outreach_sent': 0,
            'meetings_scheduled': 0,
            'pitches_delivered': 0,
            'investments_secured': 0,
            'total_raised': 0.0,
            'avg_meeting_conversion': 0.0
        }

    async def initialize(self):
        """Initialize agent and load investor intelligence"""
        print("💼 Initializing Investor Relations Agent...")
        await self._load_investor_databases()
        await self._prepare_pitch_materials()
        print("✅ Agent initialized successfully")

    async def _load_investor_databases(self):
        """Connect to investor databases and intelligence sources"""
        sources = [
            'Crunchbase',
            'AngelList',
            'LinkedIn',
            'Crypto VC Database',
            'Pitchbook'
        ]
        print(f"📊 Loading investor data from: {', '.join(sources)}")

    async def _prepare_pitch_materials(self):
        """Prepare customizable pitch materials"""
        self.pitch_versions = {
            'angel': {
                'focus': 'Vision and market opportunity',
                'key_points': ['Founder story', 'Market gap', 'Early traction'],
                'deck_slides': 12
            },
            'vc': {
                'focus': 'Scalability and returns',
                'key_points': ['TAM/SAM/SOM', 'Unit economics', 'Growth metrics', '10x potential'],
                'deck_slides': 15
            },
            'crypto_fund': {
                'focus': 'Tokenomics and Web3 innovation',
                'key_points': ['D33J utility', 'Blockchain value prop', 'Decentralization roadmap'],
                'deck_slides': 14
            },
            'strategic': {
                'focus': 'Partnership synergies',
                'key_points': ['Strategic fit', 'Market access', 'Technology integration'],
                'deck_slides': 10
            }
        }

    async def identify_potential_investors(self, target_amount: float, stage: str = 'seed') -> List[InvestorProfile]:
        """
        Identify potential investors matching criteria
        """
        print(f"\n🔍 Identifying investors for ${target_amount:,.0f} {stage} round...")

        investors = []

        # Angel investors
        if stage in ['pre-seed', 'seed']:
            angels = await self._find_angel_investors()
            investors.extend(angels)

        # Venture capital firms
        if stage in ['seed', 'series_a']:
            vcs = await self._find_vc_firms()
            investors.extend(vcs)

        # Crypto/Web3 focused funds
        crypto_funds = await self._find_crypto_funds()
        investors.extend(crypto_funds)

        # Strategic investors
        strategic = await self._find_strategic_investors()
        investors.extend(strategic)

        # Score and qualify investors
        qualified_investors = await self._qualify_investors(investors, target_amount)

        self.investors.extend(qualified_investors)
        self.performance_metrics['investors_identified'] += len(qualified_investors)

        print(f"✅ Identified {len(qualified_investors)} qualified investors")
        return qualified_investors

    async def _find_angel_investors(self) -> List[InvestorProfile]:
        """Find angel investors in blockchain/gaming space"""
        sample_investors = [
            InvestorProfile(
                id="angel_001",
                name="Alex Chen",
                investor_type="angel",
                focus_areas=["Web3", "Gaming", "DeFi"],
                investment_range="$25K-$100K",
                portfolio=["GameFi Startup", "NFT Platform", "DeFi Protocol"],
                contact_info={
                    'email': 'alex@web3angels.com',
                    'linkedin': 'linkedin.com/in/alexchen',
                    'twitter': '@alexweb3'
                },
                interest_score=0.0,
                last_interaction=None,
                meeting_status="cold",
                metadata={'deals_per_year': 5, 'check_size': 50000}
            ),
            InvestorProfile(
                id="angel_002",
                name="Sarah Martinez",
                investor_type="angel",
                focus_areas=["Blockchain", "Social", "Creator Economy"],
                investment_range="$50K-$200K",
                portfolio=["Social Token Platform", "Creator Tools", "Blockchain Network"],
                contact_info={
                    'email': 'sarah.m@investors.com',
                    'linkedin': 'linkedin.com/in/sarahmartinez'
                },
                interest_score=0.0,
                last_interaction=None,
                meeting_status="cold",
                metadata={'deals_per_year': 8, 'check_size': 100000}
            )
        ]
        return sample_investors

    async def _find_vc_firms(self) -> List[InvestorProfile]:
        """Find VC firms investing in blockchain/gaming"""
        sample_investors = [
            InvestorProfile(
                id="vc_001",
                name="BlockChain Ventures",
                investor_type="vc",
                focus_areas=["Blockchain Infrastructure", "DeFi", "Gaming"],
                investment_range="$500K-$5M",
                portfolio=["Major DeFi Protocol", "Gaming Platform", "Layer 2 Solution"],
                contact_info={
                    'email': 'partners@blockchainvc.com',
                    'website': 'blockchainvc.com'
                },
                interest_score=0.0,
                last_interaction=None,
                meeting_status="cold",
                metadata={
                    'fund_size': 100000000,
                    'stage_focus': 'seed_to_series_a',
                    'check_size': 2000000
                }
            )
        ]
        return sample_investors

    async def _find_crypto_funds(self) -> List[InvestorProfile]:
        """Find crypto-native investment funds"""
        sample_investors = [
            InvestorProfile(
                id="crypto_001",
                name="Crypto Gaming Fund",
                investor_type="crypto_fund",
                focus_areas=["GameFi", "Play-to-Earn", "Metaverse"],
                investment_range="$250K-$3M",
                portfolio=["Top GameFi Projects", "Metaverse Platform", "NFT Marketplace"],
                contact_info={
                    'email': 'investments@cryptogaming.fund',
                    'telegram': '@cryptogamingfund'
                },
                interest_score=0.0,
                last_interaction=None,
                meeting_status="cold",
                metadata={
                    'thesis': 'blockchain_gaming_infrastructure',
                    'sweet_spot': 1000000
                }
            ),
            InvestorProfile(
                id="crypto_002",
                name="Web3 Africa Fund",
                investor_type="crypto_fund",
                focus_areas=["African Tech", "Web3", "Infrastructure"],
                investment_range="$100K-$1M",
                portfolio=["African Fintech", "Web3 Platform", "Blockchain Startup"],
                contact_info={
                    'email': 'team@web3africa.fund',
                    'linkedin': 'linkedin.com/company/web3africafund'
                },
                interest_score=0.0,
                last_interaction=None,
                meeting_status="cold",
                metadata={
                    'geography_focus': 'africa',
                    'local_presence': True
                }
            )
        ]
        return sample_investors

    async def _find_strategic_investors(self) -> List[InvestorProfile]:
        """Find strategic investors and corporate venture arms"""
        sample_investors = [
            InvestorProfile(
                id="strategic_001",
                name="Gaming Corp Strategic Investments",
                investor_type="strategic",
                focus_areas=["Gaming", "Technology", "Web3"],
                investment_range="$500K-$10M",
                portfolio=["Gaming Studios", "Technology Partners"],
                contact_info={
                    'email': 'corp.dev@gamingcorp.com'
                },
                interest_score=0.0,
                last_interaction=None,
                meeting_status="cold",
                metadata={
                    'strategic_value': 'distribution_partnership',
                    'market_access': 'global_gaming_audience'
                }
            )
        ]
        return sample_investors

    async def _qualify_investors(self, investors: List[InvestorProfile], target_amount: float) -> List[InvestorProfile]:
        """Qualify and score investors based on fit"""
        qualified = []

        for investor in investors:
            score = self._calculate_investor_fit_score(investor, target_amount)
            investor.interest_score = score

            # Qualify if score >= 0.65
            if score >= 0.65:
                qualified.append(investor)

        return sorted(qualified, key=lambda x: x.interest_score, reverse=True)

    def _calculate_investor_fit_score(self, investor: InvestorProfile, target_amount: float) -> float:
        """Calculate fit score for investor"""
        score = 0.0

        # Focus area alignment (40%)
        our_focus = ["Blockchain", "Gaming", "Web3", "DeFi", "Social"]
        alignment = len(set(our_focus) & set(investor.focus_areas)) / len(our_focus)
        score += alignment * 0.4

        # Investment range fit (30%)
        # Parse investment range and check if target is within
        if self._check_investment_range(investor.investment_range, target_amount):
            score += 0.3
        else:
            score += 0.1

        # Portfolio relevance (20%)
        relevant_keywords = ['Gaming', 'Blockchain', 'Web3', 'DeFi', 'NFT', 'Token']
        portfolio_text = ' '.join(investor.portfolio)
        relevance = sum(1 for kw in relevant_keywords if kw in portfolio_text) / len(relevant_keywords)
        score += relevance * 0.2

        # Investor type bonus (10%)
        if investor.investor_type == 'crypto_fund':
            score += 0.1  # Perfect fit for our Web3 focus
        elif investor.investor_type == 'strategic':
            score += 0.08  # Good for partnerships
        else:
            score += 0.05

        return min(score, 1.0)

    def _check_investment_range(self, range_str: str, target: float) -> bool:
        """Check if target amount fits investor range"""
        # Simplified - in production, parse range properly
        return True

    async def create_outreach_campaign(self, investors: List[InvestorProfile]) -> Dict:
        """
        Create personalized outreach campaign for investors
        """
        print(f"\n📧 Creating outreach campaign for {len(investors)} investors...")

        campaign = {
            'id': f"ir_campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'targets': len(investors),
            'sent': 0,
            'opened': 0,
            'responded': 0,
            'meetings_booked': 0
        }

        for investor in investors:
            message = self._generate_investor_message(investor)
            success = await self._send_investor_outreach(investor, message)

            if success:
                campaign['sent'] += 1
                investor.meeting_status = "contacted"
                investor.last_interaction = datetime.now()
                self.performance_metrics['outreach_sent'] += 1

        print(f"✅ Outreach sent to {campaign['sent']} investors")
        return campaign

    def _generate_investor_message(self, investor: InvestorProfile) -> str:
        """Generate personalized message for investor"""

        # Customize based on investor type
        templates = {
            'angel': """
Subject: DeeJae LeEtta Network - Web3 Professional Networking Platform

Hi {name},

I'm reaching out because of your investments in {portfolio_example} and focus on {focus_areas}.

We're building DeeJae LeEtta Network - a decentralized professional networking platform powered by Ethereum and our D33J token. Think LinkedIn meets Web3 with:

🎮 Integrated MMO gaming economy
🪙 D33J token utility and governance
🌍 Focus on African markets (starting with Nigeria)
💼 B2B e-commerce integration

**Traction:**
- D33J token deployed on Ethereum
- 24K+ community members across platforms
- Beta MMO in development
- Pilot e-commerce clients onboarded

**Ask:** ${amount} to scale AI-driven user acquisition and launch MMO beta

Available for a quick call this week to share our deck and vision?

Best,
DeeJae LeEtta Team
            """,
            'vc': """
Subject: DeeJae LeEtta Network - Series Seed for Web3 Professional Platform

Dear {name} / {firm},

{firm}'s investments in {portfolio_example} align perfectly with our vision at DeeJae LeEtta Network.

**The Opportunity:**
We're building decentralized professional networking infrastructure with blockchain-powered gaming integration - a $15B TAM combining professional networking and GameFi.

**Why Now:**
- LinkedIn controls professional data without user ownership
- GameFi market growing 40% YoY
- African Web3 adoption accelerating (Nigeria #1 in P2P crypto)

**Our Solution:**
- Ethereum-based professional identity (verifiable, portable)
- D33J token economy (utility + governance)
- Integrated MMO with play-to-earn mechanics
- AI-driven customer acquisition system

**Traction & Metrics:**
- 24K community members (organic)
- D33J token: 5K+ holders
- Beta MMO: 1K+ waitlist
- E-commerce pilot: $50K GMV

**The Round:**
Raising ${amount} seed to:
1. Scale AI agent infrastructure
2. Launch MMO beta (Q3 2026)
3. Expand African market presence

Let's schedule time to walk through our deck and unit economics?

Best regards,
DeeJae LeEtta Team
            """,
            'crypto_fund': """
Subject: D33J Token - GameFi + Professional Networking Infrastructure

GM {name},

Your fund's thesis on {focus_areas} caught my attention.

**DeeJae LeEtta Network** is building crypto-native professional networking with integrated GameFi:

**Token Utility (D33J):**
🔹 Governance for network decisions
🔹 In-game currency for MMO
🔹 Staking for premium features
🔹 P2P rewards between professionals
🔹 DeFi integrations (planned)

**Why D33J Token Will Accrue Value:**
1. Growing user base (24K → 500K target)
2. Multi-use case utility (not single-purpose)
3. Burn mechanisms via platform fees
4. Staking rewards driving token lockup

**Differentiation:**
- Only professional network with gaming integration
- Strong African market focus (underpenetrated)
- AI-powered autonomous growth system

**Round Terms:**
${amount} at {valuation} valuation
Token allocation available for strategic partners

Interested in reviewing our tokenomics deck?

LFG,
DeeJae LeEtta Team
            """,
            'strategic': """
Subject: Partnership Opportunity - DeeJae LeEtta Network

Hi {name},

Given {firm}'s position in {focus_areas}, I wanted to explore a potential strategic partnership.

**DeeJae LeEtta Network** offers:
- 24K+ engaged professional community
- D33J token ecosystem for user rewards
- Upcoming MMO launch (gaming distribution)
- E-commerce marketplace infrastructure

**Potential Synergies:**
✓ Distribution: Access our community for your products/services
✓ Technology: Integrate blockchain identity/tokens
✓ Content: Co-marketing and cross-promotion
✓ Strategic investment to align long-term

**What We're Looking For:**
- ${amount} strategic investment
- Market access and distribution support
- Technical/operational guidance

Would love to discuss how we can create mutual value. Available for a call?

Best,
DeeJae LeEtta Team
            """
        }

        template = templates.get(investor.investor_type, templates['angel'])

        return template.format(
            name=investor.name,
            firm=investor.name,
            portfolio_example=investor.portfolio[0] if investor.portfolio else "Web3 projects",
            focus_areas=', '.join(investor.focus_areas[:2]),
            amount="250K-500K" if investor.investor_type == 'angel' else "2M",
            valuation="$20M" if investor.investor_type == 'crypto_fund' else ""
        )

    async def _send_investor_outreach(self, investor: InvestorProfile, message: str) -> bool:
        """Send outreach message to investor"""
        # Simulate sending with 70% delivery success
        await asyncio.sleep(0.05)
        return random.random() > 0.3

    async def schedule_investor_meeting(self, investor_id: str) -> Dict:
        """Schedule meeting with investor"""
        investor = next((i for i in self.investors if i.id == investor_id), None)
        if not investor:
            return {'error': 'Investor not found'}

        investor.meeting_status = "meeting_scheduled"
        self.performance_metrics['meetings_scheduled'] += 1

        # Prepare customized materials
        meeting_prep = {
            'investor_id': investor_id,
            'investor_name': investor.name,
            'meeting_type': 'introductory_call',
            'duration': '30 minutes',
            'pitch_version': self.pitch_versions[investor.investor_type],
            'key_talking_points': self._generate_talking_points(investor),
            'questions_to_ask': self._generate_investor_questions(investor),
            'materials': [
                'Pitch Deck (customized)',
                'One-pager',
                'Financial Projections',
                'D33J Tokenomics'
            ]
        }

        print(f"📅 Meeting scheduled with {investor.name}")
        return meeting_prep

    def _generate_talking_points(self, investor: InvestorProfile) -> List[str]:
        """Generate customized talking points for investor"""
        points = [
            "Market opportunity in decentralized professional networking",
            "D33J token utility across platform and gaming",
            "AI-driven customer acquisition system",
            "Traction: 24K community, token holders, pilot clients"
        ]

        # Customize based on investor focus
        if "Africa" in investor.focus_areas or investor.metadata.get('geography_focus') == 'africa':
            points.append("Strategic focus on African markets (Nigeria solar farm & data center)")

        if "Gaming" in investor.focus_areas or "GameFi" in investor.focus_areas:
            points.append("MMO integration with play-to-earn mechanics")

        if investor.investor_type == "strategic":
            points.append("Partnership opportunities and synergies")

        return points

    def _generate_investor_questions(self, investor: InvestorProfile) -> List[str]:
        """Generate questions to ask investor"""
        return [
            f"What attracted you to {investor.focus_areas[0]}?",
            "What's your typical investment timeline and process?",
            "Are there specific metrics or milestones you look for?",
            "How do you typically support portfolio companies?",
            f"Any portfolio companies in {investor.focus_areas[0]} we should connect with?"
        ]

    async def track_investment(self, investor_id: str, amount: float, terms: Dict) -> Investment:
        """Track investment deal"""
        investment = Investment(
            id=f"inv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            investor_id=investor_id,
            amount=amount,
            stage="negotiating",
            terms=terms,
            status="pending",
            created_at=datetime.now()
        )

        self.investments.append(investment)
        self.performance_metrics['investments_secured'] += 1
        self.performance_metrics['total_raised'] += amount

        print(f"💰 Investment tracked: ${amount:,.0f} from investor {investor_id}")
        return investment

    def get_performance_report(self) -> Dict:
        """Generate investor relations performance report"""
        meeting_conversion = 0.0
        if self.performance_metrics['meetings_scheduled'] > 0:
            meeting_conversion = (
                self.performance_metrics['investments_secured'] /
                self.performance_metrics['meetings_scheduled']
            ) * 100

        return {
            'agent_type': 'Investor Relations',
            'metrics': self.performance_metrics,
            'meeting_conversion_rate': f"{meeting_conversion:.1f}%",
            'total_investors': len(self.investors),
            'pipeline': self._get_pipeline_breakdown(),
            'top_investors': self._get_top_investors(),
            'recommendations': self._generate_ir_recommendations()
        }

    def _get_pipeline_breakdown(self) -> Dict:
        """Get breakdown of investor pipeline by stage"""
        breakdown = {
            'cold': 0,
            'contacted': 0,
            'meeting_scheduled': 0,
            'pitched': 0,
            'negotiating': 0
        }

        for investor in self.investors:
            if investor.meeting_status in breakdown:
                breakdown[investor.meeting_status] += 1

        return breakdown

    def _get_top_investors(self) -> List[Dict]:
        """Get top potential investors by fit score"""
        sorted_investors = sorted(self.investors, key=lambda x: x.interest_score, reverse=True)[:5]

        return [
            {
                'name': i.name,
                'type': i.investor_type,
                'fit_score': round(i.interest_score, 2),
                'status': i.meeting_status
            }
            for i in sorted_investors
        ]

    def _generate_ir_recommendations(self) -> List[str]:
        """Generate recommendations for investor relations"""
        recommendations = []

        if self.performance_metrics['meetings_scheduled'] < 5:
            recommendations.append("Increase outreach volume to get more meetings")

        if self.performance_metrics['total_raised'] < 500000:
            recommendations.append("Focus on crypto funds - highest alignment with D33J token")

        recommendations.append("Leverage Web3 Africa Fund connection for local market expertise")
        recommendations.append("Prepare case study of early e-commerce clients for social proof")
        recommendations.append("Consider token-based fundraising (SAFT) for crypto-native investors")

        return recommendations


# CLI Interface
async def main():
    """Main execution function"""

    config = {
        'fundraising': {
            'target_amount': 2000000,  # $2M
            'stage': 'seed',
            'valuation': 20000000  # $20M
        }
    }

    # Initialize agent
    agent = InvestorRelationsAgent(config)
    await agent.initialize()

    # Run investor relations cycle
    print("\n" + "="*60)
    print("🚀 Starting Investor Relations Cycle")
    print("="*60)

    # Identify investors
    investors = await agent.identify_potential_investors(
        target_amount=config['fundraising']['target_amount'],
        stage=config['fundraising']['stage']
    )

    # Create outreach campaign
    if investors:
        top_investors = investors[:10]
        campaign = await agent.create_outreach_campaign(top_investors)

    # Simulate some meetings
    if len(investors) >= 2:
        await agent.schedule_investor_meeting(investors[0].id)
        await agent.schedule_investor_meeting(investors[1].id)

        # Simulate investment
        await agent.track_investment(
            investors[0].id,
            amount=500000,
            terms={'equity': '5%', 'valuation': 10000000}
        )

    # Show performance report
    print("\n" + "="*60)
    print("📊 PERFORMANCE REPORT")
    print("="*60)
    report = agent.get_performance_report()
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
