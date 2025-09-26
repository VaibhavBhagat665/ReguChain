# ReguChain Watch - Real-time Regulatory Compliance with AI-powered RAG

A production-ready real-time Retrieval-Augmented Generation (RAG) application for regulatory compliance monitoring. The system continuously ingests regulatory sources (OFAC, SEC, CFTC, FINRA, NewsAPI), indexes them with Google Gemini embeddings, and provides explainable AI-powered compliance assessments.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Query   │  │   Risk   │  │   Live   │  │   Evidence   │   │
│  │   Box    │  │  Gauge   │  │   Feed   │  │   Explorer   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
┌─────────────────────────────┴───────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                          │  │
│  │  /api/query  /api/ingest/simulate  /api/status  /health  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   RAG    │  │   Risk   │  │  Vector  │  │   Ingestion  │  │
│  │  Engine  │  │  Engine  │  │   Store  │  │   Pipeline   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Data Sources & Storage                       │  │
│  │  FAISS Index │ SQLite DB │ Gemini API │ External APIs    │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Features

- **Real-time RAG**: Continuous ingestion and indexing of regulatory data
- **Multi-source Integration**: OFAC SDN, SEC/CFTC/FINRA RSS feeds, NewsAPI
- **AI-powered Analysis**: Google Gemini for embeddings and text generation
- **Risk Assessment**: Automated risk scoring (0-100) with explainable factors
- **Vector Search**: FAISS-based similarity search with persistent storage
- **Live Updates**: Real-time feed showing latest regulatory changes
- **Simulation Mode**: Demo capability to inject sanctions for testing
- **Production Ready**: Docker support, health checks, error handling

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional but recommended)

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/reguchain-watch.git
cd reguchain-watch
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Update `.env` with your API keys:
```env
GOOGLE_API_KEY=your_gemini_api_key
NEWSAPI_KEY=your_newsapi_key  # Optional
```

4. Start services:
```bash
docker-compose up --build
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Demo Walkthrough

Run the interactive demo:
```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

### Demo Steps:

1. **Initial Query** (Before simulation)
   - Question: "Is wallet 0xDEMO0001 involved in any sanctions?"
   - Target: "0xDEMO0001"
   - Result: Low/Medium risk

2. **Simulate Ingestion**
   - Click "Simulate Ingestion" button
   - Injects new OFAC sanctions for the target
   - Watch Live Feed update in real-time

3. **Re-run Query** (After simulation)
   - Same question and target
   - Result: HIGH RISK (70+ score)
   - New evidence shows simulated sanctions

## Deployment

### Deploy to Render

1. Push code to GitHub
2. Connect GitHub repo to Render
3. Use `render.yaml` for configuration
4. Set environment variables in Render dashboard:
   - `GOOGLE_API_KEY`
   - `NEWSAPI_KEY`

### Deploy to Vercel (Frontend)

1. Push code to GitHub
2. Import project in Vercel
3. Set root directory to `frontend`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = Your Render backend URL

### Deploy with Docker

```bash
# Build and run backend
docker build -t reguchain-backend ./backend
docker run -p 8000:8000 --env-file .env reguchain-backend

# Frontend can be deployed to Vercel/Netlify
```

## API Endpoints

### POST /api/query
Query the RAG system for compliance assessment
```json
{
  "question": "Is wallet 0xABC sanctioned?",
  "target": "0xABC123..."
}
```

### POST /api/ingest/simulate
Simulate new sanction entry for demo
```json
{
  "target": "0xDEMO0001"
}
```

### GET /api/status
Get system status and recent updates

### GET /health
Health check endpoint

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `NEWSAPI_KEY` | NewsAPI key for news ingestion | No |
| `DATABASE_URL` | SQLite database path | Yes |
| `FAISS_INDEX_PATH` | Path for FAISS index storage | Yes |
| `LLM_MODEL` | Gemini model (default: gemini-pro) | No |
| `RISK_SCORE_THRESHOLD` | Risk score threshold (default: 50) | No |

## Testing

Run backend tests:
```bash
cd backend
pytest tests/
```

## Technology Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **AI/ML**: Google Gemini, FAISS, NumPy
- **Database**: SQLite, SQLAlchemy
- **Deployment**: Docker, Render, Vercel

## Free API Tiers

The system works with free API tiers:
- **Google Gemini**: 1,500 requests/day (no credit card required)
- **NewsAPI**: 200 requests/day (optional, falls back to RSS)
- **RSS Feeds**: Unlimited (SEC, CFTC, FINRA)

## Architecture Details

### Real-time RAG Pipeline
1. **Ingestion**: Continuous polling of regulatory sources
2. **Embedding**: Google Gemini converts text to vectors
3. **Indexing**: FAISS stores and indexes embeddings
4. **Retrieval**: Semantic search finds relevant documents
5. **Generation**: Gemini synthesizes compliance assessment
6. **Risk Scoring**: Rule-based engine calculates 0-100 score

### Data Flow
1. User submits compliance query
2. System searches vector store for relevant documents
3. Risk engine analyzes evidence and blockchain data
4. Gemini generates explainable assessment
5. Frontend displays risk gauge, evidence, and recommendations

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/reguchain-watch/issues)
- Documentation: See `/docs` folder

## Acknowledgments

- Google Gemini for AI capabilities
- FAISS for vector search
- Regulatory data sources (OFAC, SEC, CFTC, FINRA)

---

**Built for hackathon demonstration** - Always verify critical compliance decisions with official sources.
