import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

try:
    from app.config import GROQ_API_KEY
    from groq import AsyncGroq
except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)

async def test_groq():
    print("🚀 Testing Groq Connection...")
    
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not found in environment variables.")
        return

    print(f"🔑 API Key found: {GROQ_API_KEY[:5]}...{GROQ_API_KEY[-5:]}")
    
    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
        completion = await client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "user", "content": "Hello, explain what you are in one sentence."}
            ],
        )
        print(f"✅ Connection Successful!")
        print(f"🤖 Response: {completion.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_groq())
