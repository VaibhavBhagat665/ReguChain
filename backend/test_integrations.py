"""
Test script to verify all API integrations
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

async def test_google_gemini():
    """Test Google Gemini API"""
    print("\n=== Testing Google Gemini API ===")
    try:
        import google.generativeai as genai
        from app.config import GOOGLE_API_KEY
        
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content("What is blockchain compliance?")
        print(f"✅ Gemini API working: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return False

async def test_newsdata_api():
    """Test NewsData.io API"""
    print("\n=== Testing NewsData.io API ===")
    try:
        from app.news_service import news_service
        
        articles = await news_service.fetch_newsdata_articles(
            query="cryptocurrency",
            category="business"
        )
        
        if articles:
            print(f"✅ NewsData API working: Found {len(articles)} articles")
            print(f"   Sample: {articles[0]['title'][:80]}...")
            return True
        else:
            print("⚠️ NewsData API returned no articles")
            return False
    except Exception as e:
        print(f"❌ NewsData API error: {e}")
        return False

async def test_rss_feeds():
    """Test RSS feed ingestion"""
    print("\n=== Testing RSS Feeds ===")
    try:
        from app.news_service import news_service
        
        articles = await news_service.fetch_rss_feeds()
        
        if articles:
            print(f"✅ RSS feeds working: Found {len(articles)} articles from regulatory sources")
            sources = set(article['source'] for article in articles)
            print(f"   Sources: {', '.join(sources)}")
            return True
        else:
            print("⚠️ RSS feeds returned no articles")
            return False
    except Exception as e:
        print(f"❌ RSS feeds error: {e}")
        return False

async def test_langchain():
    """Test LangChain integration"""
    print("\n=== Testing LangChain ===")
    try:
        from app.langchain_agent import langchain_agent
        
        # Test a simple query
        response = langchain_agent.query("What is AML compliance?")
        
        if response.get("success"):
            print(f"✅ LangChain working: {response['response'][:100]}...")
            return True
        else:
            print(f"⚠️ LangChain query failed: {response.get('error')}")
            return False
    except Exception as e:
        print(f"❌ LangChain error: {e}")
        return False

async def test_vector_store():
    """Test FAISS vector store"""
    print("\n=== Testing FAISS Vector Store ===")
    try:
        from app.vector_store import vector_store
        
        # Add a test document
        test_text = "This is a test document about blockchain compliance and regulations."
        doc_id = vector_store.add_documents([test_text], [{"source": "test"}])
        
        # Search for similar documents
        results = vector_store.search("blockchain compliance", k=1)
        
        if results:
            print(f"✅ FAISS working: Added document and found {len(results)} similar results")
            return True
        else:
            print("⚠️ FAISS search returned no results")
            return False
    except Exception as e:
        print(f"❌ FAISS error: {e}")
        return False

async def test_pathway():
    """Test Pathway integration"""
    print("\n=== Testing Pathway ===")
    try:
        from app.pathway_service import pathway_service
        
        if pathway_service.pathway_key:
            print(f"✅ Pathway key configured")
            print(f"   Mode: {pathway_service.mode}")
            print(f"   Streaming: {pathway_service.streaming_mode}")
            return True
        else:
            print("⚠️ Pathway key not configured")
            return False
    except Exception as e:
        print(f"❌ Pathway error: {e}")
        return False

async def test_database():
    """Test database connection"""
    print("\n=== Testing Database ===")
    try:
        from app.database import init_db, get_recent_documents
        
        init_db()
        docs = get_recent_documents(limit=5)
        
        print(f"✅ Database working: Found {len(docs)} recent documents")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 50)
    print("ReguChain Backend Integration Tests")
    print("=" * 50)
    
    # Check environment variables
    print("\n=== Environment Variables ===")
    from app.config import GOOGLE_API_KEY, NEWSAPI_KEY, PATHWAY_KEY
    
    print(f"GOOGLE_API_KEY: {'✅ Set' if GOOGLE_API_KEY else '❌ Not set'}")
    print(f"NEWSAPI_KEY: {'✅ Set' if NEWSAPI_KEY else '❌ Not set'}")
    print(f"PATHWAY_KEY: {'✅ Set' if PATHWAY_KEY else '❌ Not set'}")
    
    # Run tests
    results = {
        "Database": await test_database(),
        "Google Gemini": await test_google_gemini(),
        "NewsData API": await test_newsdata_api(),
        "RSS Feeds": await test_rss_feeds(),
        "LangChain": await test_langchain(),
        "FAISS Vector Store": await test_vector_store(),
        "Pathway": await test_pathway()
    }
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}")
    
    success_count = sum(1 for status in results.values() if status)
    total_count = len(results)
    
    print(f"\nTotal: {success_count}/{total_count} services working")
    
    if success_count == total_count:
        print("\n🎉 All integrations working successfully!")
    elif success_count > total_count / 2:
        print("\n⚠️ Some integrations need attention")
    else:
        print("\n❌ Multiple integrations failing - check configuration")

if __name__ == "__main__":
    asyncio.run(main())
