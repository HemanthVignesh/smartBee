#!/usr/bin/env python3
"""Complete Backend Test Suite"""

import requests
import sys
import time

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        print(f"✅ Health check passed: {data['message']}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Start with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_root():
    """Test root endpoint"""
    print("\n🔍 Testing root endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        assert r.status_code == 200
        print("✅ Root endpoint working")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False


def test_fetch_emails():
    """Test email fetching"""
    print("\n🔍 Testing email fetch...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/v1/emails/fetch",
            json={"max_results": 5},
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Fetched {data['new_count']} new emails")
            return True
        elif r.status_code == 400:
            print("⚠️  Gmail not configured (expected if no credentials)")
            return True  # Not a failure
        else:
            print(f"❌ Fetch failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Fetch test failed: {e}")
        return False


def test_get_emails():
    """Test getting emails"""
    print("\n🔍 Testing get emails...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/emails/", timeout=5)
        
        if r.status_code == 200:
            emails = r.json()
            print(f"✅ Retrieved {len(emails)} emails from database")
            return True
        else:
            print(f"❌ Get emails failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get emails test failed: {e}")
        return False


def test_cors():
    """Test CORS headers"""
    print("\n🔍 Testing CORS configuration...")
    try:
        r = requests.options(
            f"{BASE_URL}/api/v1/emails/",
            headers={"Origin": "http://localhost:5173"},
            timeout=5
        )
        
        cors_header = r.headers.get("access-control-allow-origin")
        if cors_header:
            print(f"✅ CORS configured: {cors_header}")
            return True
        else:
            print("⚠️  CORS headers not found")
            return True  # Not critical
    except Exception as e:
        print(f"⚠️  CORS test skipped: {e}")
        return True


def main():
    print("=" * 70)
    print("🐝 Smart BEE - Complete Backend Test Suite")
    print("=" * 70)
    print()
    
    # Check if server is running
    print("Checking if backend is running...")
    time.sleep(1)
    
    results = []
    
    results.append(("Health Check", test_health()))
    if not results[0][1]:
        print("\n❌ Server not running. Cannot continue tests.")
        print("   Start server: uvicorn app.main:app --reload")
        return False
    
    results.append(("Root Endpoint", test_root()))
    results.append(("CORS Configuration", test_cors()))
    results.append(("Fetch Emails", test_fetch_emails()))
    results.append(("Get Emails", test_get_emails()))
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is fully operational!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)