#!/usr/bin/env python3
"""
Test script for SIPCall API endpoints
Run this to verify the backend is working correctly
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test basic health check endpoint"""
    print("🔍 Testing health check...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def test_authentication():
    """Test authentication endpoint with mock data"""
    print("\n🔍 Testing authentication...")
    
    async with httpx.AsyncClient() as client:
        try:
            auth_data = {
                "code": "mock_oauth_code",
                "redirect_uri": "http://localhost:3000"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/auth",
                json=auth_data
            )
            
            if response.status_code == 200:
                print("✅ Authentication test passed")
                data = response.json()
                print(f"   Access token received: {data['access_token'][:20]}...")
                return data['access_token']
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None

async def test_call_initiation(token):
    """Test call initiation endpoint"""
    print("\n🔍 Testing call initiation...")
    
    if not token:
        print("❌ No token available for call test")
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            call_data = {
                "destination_number": "+1234567890",
                "caller_id": "+0987654321",
                "privacy_mode": False
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/call",
                json=call_data,
                headers=headers
            )
            
            if response.status_code == 201:
                print("✅ Call initiation test passed")
                data = response.json()
                print(f"   Call ID: {data['call_id']}")
                print(f"   Status: {data['status']}")
                return data['call_id']
            else:
                print(f"❌ Call initiation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Call initiation error: {e}")
            return None

async def test_call_status(token, call_id):
    """Test call status endpoint"""
    print("\n🔍 Testing call status...")
    
    if not token or not call_id:
        print("❌ No token or call_id available for status test")
        return
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await client.get(
                f"{BASE_URL}/api/v1/call-status/{call_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ Call status test passed")
                data = response.json()
                print(f"   Status: {data['status']}")
                print(f"   Last updated: {data['last_updated']}")
            else:
                print(f"❌ Call status failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Call status error: {e}")

async def test_call_history(token):
    """Test call history endpoint"""
    print("\n🔍 Testing call history...")
    
    if not token:
        print("❌ No token available for history test")
        return
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await client.get(
                f"{BASE_URL}/api/v1/call-history",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ Call history test passed")
                data = response.json()
                print(f"   Total calls: {data['total_count']}")
                print(f"   Calls returned: {len(data['calls'])}")
            else:
                print(f"❌ Call history failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Call history error: {e}")

async def main():
    """Run all API tests"""
    print("🚀 Starting SIPCall API Integration Tests")
    print("=" * 50)
    
    # Test health check
    health_ok = await test_health_check()
    if not health_ok:
        print("\n❌ Backend server is not responding. Please start the server first.")
        return
    
    # Test authentication
    token = await test_authentication()
    
    # Test call initiation
    call_id = await test_call_initiation(token)
    
    # Test call status
    await test_call_status(token, call_id)
    
    # Test call history
    await test_call_history(token)
    
    print("\n" + "=" * 50)
    print("🏁 API Integration Tests Complete")

if __name__ == "__main__":
    asyncio.run(main())