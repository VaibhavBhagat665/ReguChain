"""
Quick API test script to verify all endpoints are working
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_status():
    """Test status endpoint"""
    print("\n=== Testing /api/status ===")
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status API working")
            print(f"   Total documents: {data.get('total_documents', 0)}")
            print(f"   Active conversations: {data.get('active_conversations', 0)}")
            if data.get('last_updates'):
                print(f"   Recent updates: {len(data['last_updates'])} items")
            return True
        else:
            print(f"❌ Status API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat():
    """Test chat endpoint"""
    print("\n=== Testing /api/agent/chat ===")
    try:
        payload = {
            "message": "What are the latest cryptocurrency regulations from the SEC?",
            "conversation_id": None,
            "context": {}
        }
        response = requests.post(
            f"{BASE_URL}/api/agent/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat API working")
            print(f"   Response: {data['message'][:150]}...")
            print(f"   Confidence: {data.get('confidence', 0)}")
            print(f"   Conversation ID: {data.get('conversation_id', 'N/A')}")
            return True
        else:
            print(f"❌ Chat API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_wallet_analysis():
    """Test wallet analysis endpoint"""
    print("\n=== Testing /api/wallet/analyze ===")
    try:
        # Use a known Ethereum address (Vitalik's address for demo)
        payload = {
            "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        }
        response = requests.post(
            f"{BASE_URL}/api/wallet/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Wallet Analysis API working")
            print(f"   Address: {data['address'][:20]}...")
            print(f"   Risk Score: {data.get('risk_score', 0)}/100")
            print(f"   Compliance Status: {data.get('compliance_status', 'Unknown')}")
            print(f"   Total Transactions: {data.get('total_transactions', 0)}")
            return True
        else:
            print(f"❌ Wallet Analysis API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_capabilities():
    """Test capabilities endpoint"""
    print("\n=== Testing /api/agent/capabilities ===")
    try:
        response = requests.get(f"{BASE_URL}/api/agent/capabilities")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Capabilities API working")
            print(f"   Available capabilities:")
            for cap in data:
                status = "✅" if cap.get('enabled') else "❌"
                print(f"   {status} {cap['name']}: {cap['description']}")
            return True
        else:
            print(f"❌ Capabilities API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all API tests"""
    print("=" * 50)
    print("ReguChain Watch API Tests")
    print("=" * 50)
    
    results = {
        "Status": test_status(),
        "Capabilities": test_capabilities(),
        "Chat": test_chat(),
        "Wallet Analysis": test_wallet_analysis()
    }
    
    print("\n" + "=" * 50)
    print("Test Results")
    print("=" * 50)
    
    for endpoint, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {endpoint}")
    
    success_count = sum(1 for status in results.values() if status)
    total_count = len(results)
    
    print(f"\nTotal: {success_count}/{total_count} endpoints working")
    
    if success_count == total_count:
        print("\n🎉 All API endpoints are working!")
        print("\n📱 You can now:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Chat with the AI agent about regulations")
        print("3. Analyze blockchain wallets for compliance")
        print("4. View real-time regulatory updates")
    else:
        print("\n⚠️ Some endpoints need attention")

if __name__ == "__main__":
    main()
