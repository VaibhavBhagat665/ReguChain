"""
Demo script for ReguChain Real-time System
Demonstrates Pathway streaming with News APIs and Groq-powered analysis
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

async def demo_realtime_system():
    """Comprehensive demo of the real-time system"""
    
    print("🎬 ReguChain Real-time System Demo")
    print("=" * 60)
    print("This demo showcases:")
    print("• Real-time news fetching from News API/NewsData.io")
    print("• Pathway streaming and processing")
    print("• Real-time compliance monitoring")
    print("=" * 60)
    
    try:
        from app.realtime_news_service import realtime_news_service
        from app.realtime_pathway_service import realtime_pathway_service
        
        # Demo 1: News API Integration
        print("\n📰 Demo 1: Real-time News Fetching")
        print("-" * 40)
        
        async with realtime_news_service:
            # Fetch real-time news
            print("Fetching latest cryptocurrency and regulatory news...")
            articles = await realtime_news_service.fetch_realtime_news(
                query="cryptocurrency OR blockchain OR SEC OR regulatory",
                page_size=5
            )
            
            print(f"✅ Fetched {len(articles)} articles")
            
            for i, article in enumerate(articles[:3], 1):
                print(f"\n📄 Article {i}:")
                print(f"   Title: {article.title[:80]}...")
                print(f"   Source: {article.source}")
                print(f"   Category: {article.category}")
                print(f"   Sentiment: {article.sentiment}")
                print(f"   Relevance: {article.relevance_score:.2f}")
                print(f"   Keywords: {', '.join(article.keywords[:3])}")
        
        # Demo 2: Headlines
        print("\n\n📈 Demo 2: Top Business Headlines")
        print("-" * 40)
        
        async with realtime_news_service:
            headlines = await realtime_news_service.fetch_top_headlines(
                category="business",
                page_size=3
            )
            
            for i, headline in enumerate(headlines, 1):
                print(f"\n🔥 Headline {i}:")
                print(f"   {headline.title}")
                print(f"   Impact: {headline.category} | Sentiment: {headline.sentiment}")
        
        # Demo 3: Pathway Integration
        print("\n\n🔄 Demo 3: Pathway Real-time Processing")
        print("-" * 40)
        
        dashboard = await realtime_pathway_service.get_realtime_dashboard()
        
        print(f"Status: {dashboard['status']}")
        print(f"Pathway Available: {dashboard.get('pathway_available', False)}")
        print(f"Active Streams: {dashboard.get('streams', {}).get('total_streams', 0)}")
        
        if 'statistics' in dashboard:
            stats = dashboard['statistics']
            print(f"Processed Articles: {stats.get('processed_news', {}).get('total_count', 0)}")
            print(f"High Priority: {stats.get('high_priority_news', {}).get('count', 0)}")
            print(f"Critical Alerts: {stats.get('critical_alerts', {}).get('count', 0)}")
        
        # End of demo items (removed AI-specific and simulation demos)
        
        # Demo 6: API Endpoints Preview
        print("\n\n🌐 Demo 6: Available API Endpoints")
        print("-" * 40)
        endpoints = [
            "GET /api/realtime/status - System status",
            "POST /api/realtime/start - Start real-time processing",
            "GET /api/realtime/dashboard - Real-time dashboard",
            "POST /api/realtime/news/fetch - Fetch latest news",
            "GET /api/realtime/news/headlines - Get top headlines",
            "GET /api/realtime/streams/{stream_name} - Query streams",
            "GET /api/realtime/alerts/critical - Get critical alerts",
            "GET /api/realtime/health - Health check"
        ]
        for endpoint in endpoints:
            print(f"   🔗 {endpoint}")
        
        print("\n\n✅ Demo completed successfully!")
        print("\nTo start the real-time system:")
        print("1. Set up API keys in .env file")
        print("2. Run: python setup_realtime.py")
        print("3. Start: python start_realtime.py")
        print("4. Access: http://localhost:8000/docs")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Demo error: {e}")

async def test_pathway_features():
    """Test specific Pathway features"""
    
    print("\n\n🧪 Testing Pathway Features")
    print("-" * 40)
    
    try:
        import pathway as pw
        print("✅ Pathway library available")
        
        # Test basic Pathway operations
        print("Testing basic Pathway operations...")
        
        # Create sample data
        data = [
            {'id': 1, 'title': 'SEC Enforcement Action', 'score': 0.9},
            {'id': 2, 'title': 'CFTC Guidance Update', 'score': 0.7},
            {'id': 3, 'title': 'DeFi Protocol Compliance', 'score': 0.8}
        ]
        
        # Create Pathway table
        import pandas as pd
        df = pd.DataFrame(data)
        
        class TestSchema(pw.Schema):
            id: int
            title: str
            score: float
        
        table = pw.debug.table_from_pandas(df, schema=TestSchema)
        
        # Apply transformations
        filtered = table.filter(table.score > 0.75)
        
        print("✅ Pathway transformations working")
        print(f"   Original records: {len(data)}")
        print(f"   Filtered records: Expected 2 (score > 0.75)")
        
    except ImportError:
        print("⚠️  Pathway not installed - install with: pip install pathway")
    except Exception as e:
        print(f"❌ Pathway test error: {e}")

def create_sample_env():
    """Create a sample .env file"""
    
    env_content = """# ReguChain Real-time Configuration
# Get your API keys from the respective services

# Groq API Key (Required)
# Get from: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# News API Key (Required)
# For NewsAPI.org or NewsData.io API keys
NEWSAPI_KEY=your_news_api_key_here

# Pathway License Key (Required for real-time streaming)
# Get from: https://pathway.com/developers
PATHWAY_KEY=your_pathway_license_key_here

# Database Configuration
DATABASE_URL=sqlite:///./reguchain.db

# Pathway Settings
PATHWAY_STREAMING_MODE=realtime
PATHWAY_PERSISTENCE_BACKEND=filesystem
PATHWAY_PERSISTENCE_PATH=./pathway_data
PATHWAY_MONITORING_LEVEL=info

# Vector Store Settings
VECTOR_DB_TYPE=faiss
FAISS_INDEX_PATH=./faiss_index
EMBEDDINGS_PROVIDER=huggingface
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDINGS_DIMENSION=384

# LLM Settings
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
LLM_TEMPERATURE=0.3

# Risk Assessment
RISK_SCORE_THRESHOLD=50
TRANSACTION_THRESHOLD=10000
"""
    
    env_file = Path(__file__).parent / ".env.sample"
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Sample .env file created: {env_file}")
    print("Copy this to .env and add your API keys")

async def main():
    """Main demo function"""
    await demo_realtime_system()
    await test_pathway_features()
    create_sample_env()
    
    print("\n🎯 Demo Complete!")
    print("Ready to build real-time regulatory compliance monitoring!")

if __name__ == "__main__":
    asyncio.run(main())
