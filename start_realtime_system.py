"""
Complete startup script for ReguChain Real-time System
"""
import asyncio
import os
import sys
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def main():
    """Main startup function"""
    
    print("🚀 Starting ReguChain Real-time System")
    print("=" * 50)
    
    # Check environment
    print("📋 Environment Check:")
    api_keys = {
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY'),
        'PATHWAY_KEY': os.getenv('PATHWAY_KEY')
    }
    
    configured_apis = []
    for key, value in api_keys.items():
        if value:
            configured_apis.append(f"✅ {key}")
        else:
            configured_apis.append(f"❌ {key}")
    
    print("   " + " | ".join(configured_apis))
    
    if not any(api_keys.values()):
        print("\n⚠️  No API keys configured!")
        print("Create a .env file with your API keys:")
        print("GOOGLE_API_KEY=your_gemini_key")
        print("NEWSAPI_KEY=your_news_api_key")
        print("PATHWAY_KEY=your_pathway_key")
        return
    
    # Import and start services
    try:
        from app.main import app
        from app.realtime_pathway_service import realtime_pathway_service
        
        print("\n🔄 Starting real-time pipeline...")
        
        # Start Pathway pipeline in background
        if realtime_pathway_service.pathway_key:
            asyncio.create_task(realtime_pathway_service.start_realtime_pipeline())
            print("✅ Pathway pipeline starting...")
        else:
            print("⚠️  Pathway running in simulation mode")
        
        print("\n🌐 Starting web server...")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("📊 Real-time Dashboard: http://localhost:8000/api/realtime/dashboard")
        print("🔍 Health Check: http://localhost:8000/api/realtime/health")
        
        # Start the server
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        print("Run 'python backend/setup_realtime.py' first")

if __name__ == "__main__":
    asyncio.run(main())
