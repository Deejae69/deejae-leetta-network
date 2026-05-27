# Deployment Guide - DeeJae LeEtta Network

## Overview

This guide provides step-by-step instructions for deploying the DeeJae LeEtta Network self-learning AI agency system to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Blockchain Deployment](#blockchain-deployment)
4. [Backend Services](#backend-services)
5. [AI Agents Configuration](#ai-agents-configuration)
6. [Dashboard Deployment](#dashboard-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Node.js** v18+ and npm
- **Python** 3.9+
- **Docker** & Docker Compose
- **Git**
- **PostgreSQL** 14+
- **Redis** 6+
- **Ethereum wallet** with ETH for gas fees

### Required Accounts/Keys

- Ethereum wallet (MetaMask recommended)
- Infura or Alchemy API key
- OpenAI API key (for AI agents)
- Social media API keys:
  - Discord Bot Token
  - Reddit API credentials
  - Twitter API credentials
  - LinkedIn API key
- Email service (SendGrid/Mailgun)
- Cloud provider account (AWS/GCP/Azure)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/Deejae69/deejae-leetta-network.git
cd deejae-leetta-network
```

### 2. Install Dependencies

#### Python Dependencies

```bash
cd agents
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `requirements.txt`:
```
fastapi==0.104.1
uvicorn==0.24.0
web3==6.11.1
aiohttp==3.9.0
numpy==1.24.3
pydantic==2.5.0
python-dotenv==1.0.0
redis==5.0.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
```

#### Node.js Dependencies (for blockchain)

```bash
cd contracts
npm install
```

Create `package.json`:
```json
{
  "name": "deejaeleetta-contracts",
  "version": "1.0.0",
  "dependencies": {
    "@openzeppelin/contracts": "^5.0.0",
    "hardhat": "^2.19.0",
    "@nomiclabs/hardhat-ethers": "^2.2.3",
    "ethers": "^6.9.0",
    "dotenv": "^16.3.1"
  }
}
```

### 3. Environment Variables

Create `.env` file in project root:

```bash
# Blockchain
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_wallet_private_key
D33J_TOKEN_ADDRESS=0x...  # After deployment
AI_COORDINATOR_ADDRESS=0x...  # After deployment

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/deejaeleetta
REDIS_URL=redis://localhost:6379

# API Keys
OPENAI_API_KEY=your_openai_key
DISCORD_BOT_TOKEN=your_discord_token
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
TWITTER_API_KEY=your_twitter_key
LINKEDIN_API_KEY=your_linkedin_key

# Email
SENDGRID_API_KEY=your_sendgrid_key
FROM_EMAIL=noreply@deejaeleetta.network

# Security
JWT_SECRET=your_random_secret_key_here
API_SECRET_KEY=your_api_secret_key

# Application
ENVIRONMENT=production
DEBUG=false
API_PORT=8000
DASHBOARD_URL=https://dashboard.deejaeleetta.network
```

---

## Blockchain Deployment

### 1. Compile Smart Contracts

```bash
cd contracts
npx hardhat compile
```

### 2. Deploy D33J Token

Create `scripts/deploy.js`:

```javascript
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying D33J Token...");

  const D33JToken = await ethers.getContractFactory("D33JToken");
  const d33j = await D33JToken.deploy();
  await d33j.deployed();

  console.log("D33J Token deployed to:", d33j.address);

  return d33j.address;
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

Deploy:

```bash
npx hardhat run scripts/deploy.js --network mainnet
```

**Important**: Save the deployed contract address!

### 3. Deploy AI Agent Coordinator

```bash
# Update deploy script with D33J token address
npx hardhat run scripts/deploy-coordinator.js --network mainnet
```

### 4. Verify Contracts on Etherscan

```bash
npx hardhat verify --network mainnet DEPLOYED_ADDRESS
```

### 5. Fund Contract with D33J Tokens

Transfer D33J tokens to the AIAgentCoordinator contract for reward distribution:

```javascript
// Using ethers.js
const amount = ethers.utils.parseEther("100000"); // 100K D33J
await d33jToken.transfer(coordinatorAddress, amount);
```

---

## Backend Services

### 1. Database Setup

#### Initialize PostgreSQL

```bash
# Create database
createdb deejaeleetta

# Run migrations
cd api
python manage.py migrate
```

Database schema:
```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(50),
    platform VARCHAR(50),
    score DECIMAL(3,2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(50),
    status VARCHAR(20),
    targets INT,
    sent INT,
    converted INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE rewards (
    id UUID PRIMARY KEY,
    agent_address VARCHAR(42),
    amount DECIMAL(18,2),
    task_id VARCHAR(100),
    distributed_at TIMESTAMP DEFAULT NOW()
);
```

#### Setup Redis

```bash
# Start Redis
redis-server

# Test connection
redis-cli ping  # Should return PONG
```

### 2. API Server Deployment

#### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - db
      - redis
    restart: always

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: deejaeleetta
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:6-alpine
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: always

volumes:
  postgres_data:
```

Deploy:

```bash
docker-compose up -d
```

#### Using PM2 (Alternative)

```bash
npm install -g pm2

# Start API
pm2 start "uvicorn api.main:app --host 0.0.0.0 --port 8000" --name deejaeleetta-api

# Save configuration
pm2 save
pm2 startup
```

---

## AI Agents Configuration

### 1. Configure Agent Settings

Create `config/agents.yaml`:

```yaml
agents:
  mmo_customer:
    enabled: true
    scan_interval: 3600  # 1 hour
    max_leads_per_scan: 100
    platforms:
      - discord
      - reddit
      - twitter
      - twitch

  ecommerce_client:
    enabled: true
    scan_interval: 7200  # 2 hours
    max_leads_per_scan: 50
    target_industries:
      - fashion
      - beauty
      - art
      - lifestyle

  arts_marketing:
    enabled: true
    posting_frequency: daily
    platforms:
      - instagram
      - twitter
      - tiktok
      - youtube
      - soundcloud

  investor_relations:
    enabled: true
    scan_interval: 86400  # 24 hours
    target_types:
      - angel
      - vc
      - crypto_fund
      - strategic
```

### 2. Start AI Agents

#### Using Systemd Services

Create `/etc/systemd/system/deejaeleetta-agents.service`:

```ini
[Unit]
Description=DeeJae LeEtta AI Agents
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/deejaeleetta/agents
Environment="PATH=/opt/deejaeleetta/venv/bin"
ExecStart=/opt/deejaeleetta/venv/bin/python agent_coordinator.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable deejaeleetta-agents
sudo systemctl start deejaeleetta-agents
```

#### Using Supervisor (Alternative)

```ini
[program:deejaeleetta-agents]
command=/opt/deejaeleetta/venv/bin/python agent_coordinator.py
directory=/opt/deejaeleetta/agents
autostart=true
autorestart=true
stderr_logfile=/var/log/deejaeleetta/agents.err.log
stdout_logfile=/var/log/deejaeleetta/agents.out.log
```

### 3. Create Agent Coordinator

Create `agents/agent_coordinator.py`:

```python
import asyncio
from mmo_customer_agent import MMOCustomerAgent
from ecommerce_client_agent import ECommerceClientAgent
from arts_marketing_agent import ArtsMarketingAgent
from investor_relations_agent import InvestorRelationsAgent

async def main():
    # Load configuration
    config = load_config()

    # Initialize agents
    agents = {
        'mmo': MMOCustomerAgent(config['mmo_customer']),
        'ecommerce': ECommerceClientAgent(config['ecommerce_client']),
        'arts': ArtsMarketingAgent(config['arts_marketing']),
        'investor': InvestorRelationsAgent(config['investor_relations'])
    }

    # Initialize all agents
    for agent in agents.values():
        await agent.initialize()

    # Run agents in parallel
    tasks = [
        run_agent_cycle(agents['mmo'], interval=3600),
        run_agent_cycle(agents['ecommerce'], interval=7200),
        run_agent_cycle(agents['arts'], interval=86400),
        run_agent_cycle(agents['investor'], interval=86400)
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Dashboard Deployment

### 1. Build Frontend

```bash
cd dashboard
# If using build tools
npm run build
```

### 2. Deploy to CDN or Static Hosting

#### Option A: AWS S3 + CloudFront

```bash
# Upload to S3
aws s3 sync ./dashboard s3://deejaeleetta-dashboard --acl public-read

# Create CloudFront distribution
aws cloudfront create-distribution --origin-domain-name deejaeleetta-dashboard.s3.amazonaws.com
```

#### Option B: Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd dashboard
netlify deploy --prod
```

#### Option C: Nginx

```nginx
server {
    listen 80;
    server_name dashboard.deejaeleetta.network;

    root /var/www/deejaeleetta/dashboard;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring & Maintenance

### 1. Setup Logging

#### Centralized Logging with ELK Stack

```yaml
# docker-compose.yml addition
elasticsearch:
  image: elasticsearch:8.5.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"

kibana:
  image: kibana:8.5.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch

logstash:
  image: logstash:8.5.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  depends_on:
    - elasticsearch
```

### 2. Setup Monitoring

#### Prometheus + Grafana

```yaml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  depends_on:
    - prometheus
```

### 3. Health Checks

Create monitoring script:

```bash
#!/bin/bash
# health_check.sh

# Check API
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $API_STATUS -ne 200 ]; then
    echo "API is down! Status: $API_STATUS"
    # Send alert
fi

# Check agents
systemctl is-active --quiet deejaeleetta-agents || echo "Agents service is down!"

# Check database
pg_isready -h localhost -p 5432 || echo "Database is down!"
```

### 4. Backup Strategy

#### Database Backups

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
pg_dump deejaeleetta > /backups/db_backup_$DATE.sql
gzip /backups/db_backup_$DATE.sql

# Upload to S3
aws s3 cp /backups/db_backup_$DATE.sql.gz s3://deejaeleetta-backups/

# Keep only last 30 days
find /backups -name "*.sql.gz" -mtime +30 -delete
```

Run daily:
```bash
0 2 * * * /opt/deejaeleetta/scripts/backup.sh
```

---

## Troubleshooting

### Common Issues

#### 1. Agent Not Finding Leads

**Symptom**: No leads being generated

**Solutions**:
- Check API keys are valid
- Verify rate limits not exceeded
- Check agent logs: `tail -f /var/log/deejaeleetta/agents.out.log`
- Test API connections manually

#### 2. Blockchain Transaction Failures

**Symptom**: Rewards not distributing

**Solutions**:
- Check wallet has sufficient ETH for gas
- Verify contract addresses are correct
- Check gas price settings
- View transaction on Etherscan

#### 3. High Memory Usage

**Symptom**: Server running out of memory

**Solutions**:
- Increase server resources
- Optimize agent scan intervals
- Add memory limits in Docker:
  ```yaml
  deploy:
    resources:
      limits:
        memory: 2G
  ```

#### 4. Database Connection Issues

**Symptom**: API cannot connect to database

**Solutions**:
- Check PostgreSQL is running
- Verify connection string in `.env`
- Check firewall rules
- Test connection: `psql $DATABASE_URL`

### Logs Location

- API Logs: `/var/log/deejaeleetta/api.log`
- Agent Logs: `/var/log/deejaeleetta/agents.log`
- Nginx Logs: `/var/log/nginx/access.log`
- Docker Logs: `docker logs <container_name>`

### Support Contacts

- Technical Support: tech@deejaeleetta.network
- Emergency: emergency@deejaeleetta.network
- Discord: #tech-support channel

---

## Security Checklist

- [ ] All private keys stored securely (not in repo)
- [ ] API endpoints have authentication
- [ ] Rate limiting configured
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Firewall rules configured
- [ ] Database credentials rotated regularly
- [ ] Smart contracts audited
- [ ] Backup system tested
- [ ] Monitoring alerts configured
- [ ] Log retention policy set

---

## Production Readiness

Before going live, ensure:

1. ✅ All smart contracts deployed and verified
2. ✅ API thoroughly tested
3. ✅ Agents producing quality leads
4. ✅ Dashboard accessible and functional
5. ✅ Monitoring and alerting active
6. ✅ Backup system operational
7. ✅ Security audit completed
8. ✅ Documentation updated
9. ✅ Team trained on operations
10. ✅ Incident response plan in place

---

**Next Steps**: After deployment, monitor system for 24-48 hours and optimize based on real-world performance data.

For updates and detailed technical docs, visit: https://docs.deejaeleetta.network
