"""
Setup script for real-time Pathway and News API integration
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

async def setup_realtime_system():
    """Setup the real-time system with proper configuration"""
    
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Checking Environment Configuration...")
    
    required_env_vars = {
        'GROQ_API_KEY': 'Groq API for AI analysis',
        'NEWSAPI_KEY': 'News API for real-time news',
        'PATHWAY_KEY': 'Pathway license for streaming (required for real-time)'
    }
    
    missing_vars = []
    for var, description in required_env_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Configured ({description})")
        else:
            print(f"❌ {var}: Missing ({description})")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("\nTo set up environment variables:")
        print("1. Create a .env file in the project root")
        print("2. Add the following variables:")
        print("   GROQ_API_KEY=your_groq_api_key")
        print("   NEWSAPI_KEY=your_news_api_key")
        print("   PATHWAY_KEY=your_pathway_license_key (optional)")
        print("\nGet your API keys from:")
        print("- Groq API: https://console.groq.com/keys")
        print("- News API: https://newsapi.org/register")
        print("- Pathway: https://pathway.com/developers (free license)")
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    
    dependencies = {
        'pathway': 'Real-time streaming framework',
        'groq': 'Groq AI integration',
        'newsapi': 'News API client',
        'fastapi': 'Web framework',
        'pandas': 'Data processing',
        'aiohttp': 'Async HTTP client'
    }
    
    missing_deps = []
    for dep, description in dependencies.items():
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep}: Available ({description})")
        except ImportError:
            print(f"❌ {dep}: Missing ({description})")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirements.txt")
    
    # Create necessary directories
    print("\n📁 Creating Directory Structure...")
    
    base_path = Path(__file__).parent
    directories = [
        base_path / "pathway_data",
        base_path / "pathway_data" / "streams",
        base_path / "pathway_data" / "pathway_state"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # Test services
    print("\n🧪 Testing Services...")
    
    try:
        from app.realtime_news_service import realtime_news_service
        from app.realtime_pathway_service import realtime_pathway_service
        
        # Test News API
        if realtime_news_service.api_key:
            print("✅ News API: Configured and ready")
        else:
            print("❌ News API: Not configured - real news fetching will be disabled")
        
        # Test Pathway
        if realtime_pathway_service.pathway_key:
            print("✅ Pathway: Licensed and ready for real-time streaming")
        else:
            print("❌ Pathway: Missing PATHWAY_KEY - real-time streaming requires a license")
        
        # Test news fetching
        print("\n🔄 Testing News Fetching...")
        async with realtime_news_service:
            test_articles = await realtime_news_service.fetch_top_headlines(page_size=1)
            print(f"✅ Fetched {len(test_articles)} headline(s)")
        
        print("\n✅ All services tested successfully!")
        
    except Exception as e:
        print(f"\n❌ Error testing services: {e}")
        return False
    
    # Create sample configuration
    print("\n⚙️  Creating Sample Configuration...")
    
    config_content = """# ReguChain Real-time Configuration
# Copy this to .env and fill in your API keys

# Groq API (Required for AI analysis)
GROQ_API_KEY=your_groq_api_key_here

# News API (Required for real-time news)
NEWSAPI_KEY=your_news_api_key_here

# Pathway License (Required - for real-time streaming)
PATHWAY_KEY=your_pathway_license_key_here

# Database Configuration
DATABASE_URL=sqlite:///./reguchain.db

# Pathway Configuration
PATHWAY_STREAMING_MODE=realtime
PATHWAY_PERSISTENCE_BACKEND=filesystem
PATHWAY_PERSISTENCE_PATH=./pathway_data
PATHWAY_MONITORING_LEVEL=info

# Vector Store Configuration
VECTOR_DB_TYPE=faiss
FAISS_INDEX_PATH=./faiss_index
EMBEDDINGS_PROVIDER=huggingface
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDINGS_DIMENSION=384

# LLM Configuration
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
LLM_TEMPERATURE=0.3
"""
    
    config_file = base_path.parent / ".env.example"
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Sample configuration created: {config_file}")
    
    # Success message
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Set up your API keys in .env file")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Start the server: python -m app.main")
    print("4. Test real-time endpoints:")
    print("   - GET /api/realtime/status")
    print("   - POST /api/realtime/start")
    print("   - GET /api/realtime/dashboard")
    print("   - GET /api/realtime/news/headlines")
    
    return True

def create_startup_script():
    """Create a startup script for the real-time system"""
    
    startup_content = '''"""
Real-time ReguChain Startup Script
"""
import asyncio
import uvicorn
from app.main import app
from app.realtime_pathway_service import realtime_pathway_service

async def startup():
    """Start the real-time system"""
    print("🚀 Starting ReguChain Real-time System...")
    
    # Start the Pathway pipeline
    success = await realtime_pathway_service.start_realtime_pipeline()
    
    if success:
        print("✅ Real-time pipeline started successfully")
    else:
        print("❌ Failed to start real-time pipeline (ensure PATHWAY_KEY is set)")
    
    print("🌐 Starting web server...")
    
    # Start the web server
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(startup())
'''
    
    startup_file = Path(__file__).parent / "start_realtime.py"
    with open(startup_file, 'w', encoding='utf-8') as f:
        f.write(startup_content)
    
    print(f"✅ Startup script created: {startup_file}")

async def main():
    """Main setup function"""
    success = await setup_realtime_system()
    
    if success:
        create_startup_script()
        print("\n🎯 Ready to go! Run 'python start_realtime.py' to start the system.")
    else:
        print("\n❌ Setup incomplete. Please resolve the issues above.")

if __name__ == "__main__":
    asyncio.run(main())
