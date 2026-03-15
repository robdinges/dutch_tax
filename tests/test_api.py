#!/usr/bin/env python3
"""
Test the tax calculator API
"""

import json
import requests

BASE_URL = "http://localhost:8000"

# Test data
test_data = {
    "household_id": "TEST_001",
    "allocation_strategy": "EQUAL",
    "members": [
        {
            "full_name": "John Smith",
            "bsn": "123456789",
            "residency_status": "RESIDENT",
            "incomes": [
                {
                    "type": "EMPLOYMENT",
                    "amount": 50000,
                    "description": "Salary"
                }
            ],
            "deductions": [
                {
                    "description": "Mortgage",
                    "amount": 5000
                }
            ],
            "withheld_tax": 10000,
            "assets": [
                {
                    "type": "SAVINGS",
                    "value": 50000,
                    "description": "Savings"
                }
            ]
        }
    ]
}

print("Testing Tax Calculator API...")
print("=" * 60)

try:
    # Test 1: Check if server is running
    print("\n1. Testing server connection...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print("   ✓ Server is running")
    else:
        print(f"   ✗ Server error: {response.status_code}")
        exit(1)

    # Test 2: Get income types
    print("\n2. Testing income types endpoint...")
    response = requests.get(f"{BASE_URL}/api/income-types")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Retrieved {len(data['types'])} income types")
    else:
        print(f"   ✗ Error: {response.status_code}")

    # Test 3: Calculate taxes
    print("\n3. Testing tax calculation...")
    response = requests.post(
        f"{BASE_URL}/api/calculate",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Response status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200 and result.get('success'):
        print("   ✓ Calculation successful!")
        print(f"\n   Results:")
        print(f"     - Total Tax Due: €{result['total_tax']:,.2f}")
        print(f"     - Effective Rate: {result['effective_tax_rate']:.2f}%")
        print(f"     - Box1 Total: €{result['box1_total']:,.2f}")
        print(f"     - Box3 Total: €{result['box3_tax']:,.2f}")
        print("\n   Full Response:")
        print(json.dumps(result, indent=2))
    else:
        print(f"   ✗ Calculation failed")
        if 'error' in result:
            print(f"   Error: {result['error']}")
        print("\n   Full Response:")
        print(json.dumps(result, indent=2))

except requests.exceptions.ConnectionError:
    print("   ✗ Cannot connect to server at", BASE_URL)
    print("   Make sure Flask app is running on port 8000")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
