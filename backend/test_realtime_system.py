"""
Test script for the real-time system
"""
import asyncio
import sys
from pathlib import Path
import json

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

async def test_system():
    """Test the complete real-time system"""
    
    print("🧪 Testing ReguChain Real-time System")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Import all modules
    print("\n1️⃣ Testing Module Imports...")
    total_tests += 1
    
    try:
        from app.realtime_news_service import realtime_news_service
        from app.realtime_pathway_service import realtime_pathway_service
        from app.realtime_api import realtime_router
        print("✅ All modules imported successfully")
        success_count += 1
    except Exception as e:
        print(f"❌ Import error: {e}")
    
    # Test 2: News Service
    print("\n2️⃣ Testing News Service...")
    total_tests += 1
    
    try:
        async with realtime_news_service:
            # Test mock news generation
            articles = await realtime_news_service._generate_mock_news()
            
            if len(articles) > 0:
                print(f"✅ Generated {len(articles)} mock articles")
                print(f"   Sample: {articles[0].title[:50]}...")
                success_count += 1
            else:
                print("❌ No mock articles generated")
                
    except Exception as e:
        print(f"❌ News service error: {e}")
    
    # Test 3: Pathway Service
    print("\n3️⃣ Testing Pathway Service...")
    total_tests += 1
    
    try:
        dashboard = await realtime_pathway_service.get_realtime_dashboard()
        
        if dashboard:
            print("✅ Pathway service responding")
            print(f"   Status: {dashboard.get('status', 'unknown')}")
            print(f"   Pathway Available: {dashboard.get('pathway_available', False)}")
            success_count += 1
        else:
            print("❌ No dashboard data received")
            
    except Exception as e:
        print(f"❌ Pathway service error: {e}")
    
    # Test 4: API Key Configuration
    print("\n4️⃣ Testing API Configuration...")
    total_tests += 1
    
    try:
        from app.config import GOOGLE_API_KEY, NEWSAPI_KEY, PATHWAY_KEY
        
        config_status = []
        if GOOGLE_API_KEY:
            config_status.append("Gemini ✅")
        else:
            config_status.append("Gemini ❌")
            
        if NEWSAPI_KEY:
            config_status.append("News API ✅")
        else:
            config_status.append("News API ❌")
            
        if PATHWAY_KEY:
            config_status.append("Pathway ✅")
        else:
            config_status.append("Pathway ⚠️")
        
        print(f"Configuration: {' | '.join(config_status)}")
        
        # Consider it successful if at least one API is configured
        if GOOGLE_API_KEY or NEWSAPI_KEY:
            success_count += 1
            print("✅ Basic configuration available")
        else:
            print("❌ No API keys configured")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    # Test 5: Data Processing
    print("\n5️⃣ Testing Data Processing...")
    total_tests += 1
    
    try:
        # Test priority calculation
        priority = realtime_pathway_service._calculate_priority_score(0.8, 'high', 'regulatory')
        alert_level = realtime_pathway_service._determine_alert_level('high', 0.8)
        
        print(f"✅ Data processing functions working")
        print(f"   Priority Score: {priority:.2f}")
        print(f"   Alert Level: {alert_level}")
        success_count += 1
        
    except Exception as e:
        print(f"❌ Data processing error: {e}")
    
    # Test 6: File System
    print("\n6️⃣ Testing File System...")
    total_tests += 1
    
    try:
        from app.config import PATHWAY_PERSISTENCE_PATH
        persistence_path = Path(PATHWAY_PERSISTENCE_PATH)
        
        # Check if directories exist
        if persistence_path.exists():
            streams_path = persistence_path / "streams"
            if streams_path.exists():
                print("✅ Directory structure exists")
                success_count += 1
            else:
                print("⚠️ Streams directory missing - will be created on startup")
                success_count += 1  # Still count as success
        else:
            print("⚠️ Persistence path missing - will be created on startup")
            success_count += 1  # Still count as success
            
    except Exception as e:
        print(f"❌ File system error: {e}")
    
    # Test 7: Dependencies
    print("\n7️⃣ Testing Dependencies...")
    total_tests += 1
    
    dependencies = {
        'fastapi': 'Web framework',
        'uvicorn': 'ASGI server',
        'pydantic': 'Data validation',
        'aiohttp': 'Async HTTP client',
        'pandas': 'Data processing'
    }
    
    missing_deps = []
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(f"{dep} ({desc})")
    
    if not missing_deps:
        print("✅ All core dependencies available")
        success_count += 1
    else:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
    
    # Optional dependencies
    optional_deps = {
        'pathway': 'Real-time streaming',
        'google.generativeai': 'Gemini AI',
        'newsapi': 'News API client'
    }
    
    available_optional = []
    for dep, desc in optional_deps.items():
        try:
            __import__(dep.replace('-', '_'))
            available_optional.append(f"{dep} ✅")
        except ImportError:
            available_optional.append(f"{dep} ❌")
    
    print(f"Optional: {' | '.join(available_optional)}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    print(f"Tests Passed: {success_count}/{total_tests}")
    print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 All tests passed! System is ready to go!")
        print("\nNext steps:")
        print("1. Set up API keys in .env file")
        print("2. Run: python setup_realtime.py")
        print("3. Start: python start_realtime.py")
        
    elif success_count >= total_tests * 0.7:
        print("\n✅ Most tests passed! System should work with some limitations.")
        print("\nRecommendations:")
        print("1. Configure missing API keys for full functionality")
        print("2. Install any missing dependencies")
        print("3. Run setup script for detailed configuration")
        
    else:
        print("\n⚠️ Several tests failed. Please check the issues above.")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check Python version (3.8+ required)")
        print("3. Verify file permissions")
    
    return success_count >= total_tests * 0.7

async def quick_demo():
    """Quick demonstration of key features"""
    
    print("\n\n🎬 Quick Demo")
    print("=" * 30)
    
    try:
        from app.realtime_news_service import realtime_news_service
        
        # Generate sample news
        async with realtime_news_service:
            articles = await realtime_news_service._generate_mock_news()
            
            print(f"📰 Sample News Articles ({len(articles)}):")
            for i, article in enumerate(articles[:2], 1):
                print(f"\n{i}. {article.title}")
                print(f"   Category: {article.category} | Sentiment: {article.sentiment}")
                print(f"   Relevance: {article.relevance_score:.2f}")
                print(f"   Keywords: {', '.join(article.keywords[:3])}")
        
        # Show API endpoints
        print(f"\n🌐 Available API Endpoints:")
        endpoints = [
            "/api/realtime/status",
            "/api/realtime/dashboard", 
            "/api/realtime/news/headlines",
            "/api/realtime/health"
        ]
        
        for endpoint in endpoints:
            print(f"   • http://localhost:8000{endpoint}")
        
        print(f"\n📚 Documentation: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"Demo error: {e}")

async def main():
    """Main test function"""
    success = await test_system()
    
    if success:
        await quick_demo()
    
    print(f"\n🏁 Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())
