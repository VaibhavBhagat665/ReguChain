# 🔗 ReguChain

**AI-Powered Regulatory Compliance Intelligence Platform**

Real-time regulatory monitoring with AI-driven risk assessment for blockchain and financial compliance.

## 🎯 **What It Does**

- 🔍 **Monitors** OFAC, SEC, CFTC, FINRA in real-time
- 🧠 **Analyzes** compliance risks using AI + vector search  
- ⚡ **Delivers** instant risk scores with evidence
- 📊 **Visualizes** regulatory changes through dashboard

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js UI    │───▶│   FastAPI        │───▶│  OpenRouter     │
│   Dashboard     │    │   Backend        │    │  Mistral LLM    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────┼────────┐
                       ▼        ▼        ▼
                ┌─────────┐ ┌────────┐ ┌──────────┐
                │ FAISS   │ │ SQLite │ │ Pathway  │
                │ Vector  │ │   DB   │ │ Streams  │
                └─────────┘ └────────┘ └──────────┘
                       ▲
                ┌──────┼──────┐
                ▼      ▼      ▼
        ┌─────────┐ ┌─────┐ ┌──────────┐
        │  OFAC   │ │ SEC │ │NewsData  │
        │Sanctions│ │ RSS │ │   API    │
        └─────────┘ └─────┘ └──────────┘
```

## 🛠️ **Tech Stack**

**Backend:** FastAPI + OpenRouter + FAISS + Pathway  
**Frontend:** Next.js + TailwindCSS  
**AI:** Mistral-7B + text-embedding-3-small  
**Data:** OFAC, SEC, CFTC, FINRA, NewsData.io

## 🚀 **Quick Start**

### **1. Setup Environment**
```bash
git clone <your-repo>
cd ReguChain
cp .env.example .env
```

### **2. Add API Keys to .env**
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key
NEWSAPI_KEY=pub_your-newsdata-key  
ETHERSCAN_API_KEY=your-etherscan-key
```

### **3. Run Backend**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### **4. Run Frontend**
```bash
cd frontend
npm install && npm run dev
```

### **5. Access**
- **App:** http://localhost:3000
- **API:** http://localhost:8000/docs

## 🔧 **Key API Endpoints**

| Endpoint | Purpose |
|----------|---------|
| `POST /api/agent/chat` | AI compliance chat |
| `POST /api/wallet/analyze` | Wallet risk analysis |
| `GET /api/status` | System health + data |
| `GET /api/alerts` | Recent alerts |

## 🎯 **Use Cases**

- **🏦 Financial Institutions**: AML/KYC compliance monitoring
- **🔗 Blockchain Projects**: Address risk assessment  
- **⚖️ Legal Teams**: Regulatory change tracking
- **🏢 Enterprises**: Compliance automation

## 📊 **Data Flow**

1. **Ingest** → OFAC, SEC, CFTC, FINRA, NewsData.io
2. **Process** → OpenRouter embeddings → FAISS vector store
3. **Analyze** → Mistral LLM + retrieved context → Risk scores
4. **Alert** → Real-time monitoring → Dashboard notifications

## 🔑 **Required API Keys**

- **OpenRouter**: [openrouter.ai](https://openrouter.ai/keys) - LLM access
- **NewsData.io**: [newsdata.io](https://newsdata.io/register) - Regulatory news  
- **Etherscan**: [etherscan.io](https://etherscan.io/register) - Blockchain data

## 🚀 **Deployment**

**Render (Backend)** + **Vercel (Frontend)**

Set environment variables in respective dashboards:
- Backend: All API keys + config
- Frontend: `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`

---

*AI-powered compliance intelligence for the modern financial world*
