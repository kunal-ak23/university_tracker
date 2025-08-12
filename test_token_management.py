#!/usr/bin/env python
"""
Test script for Microsoft Graph Token Management System

This script tests the token management functionality without requiring
a full Django environment setup.

Usage:
    python test_token_management.py
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datagami_university_tracker.settings')
django.setup()

from core.graph_token_service import MicrosoftGraphTokenService
from core.models import MicrosoftGraphToken
from django.utils import timezone

def test_token_service():
    """Test the token management service"""
    print("Testing Microsoft Graph Token Management System")
    print("=" * 50)
    
    # Test 1: Check configuration
    print("\n1. Checking configuration...")
    from django.conf import settings
    
    config_status = {
        'GRAPH_CLIENT_ID': bool(settings.GRAPH_CLIENT_ID),
        'GRAPH_CLIENT_SECRET': bool(settings.GRAPH_CLIENT_SECRET),
        'GRAPH_TENANT': bool(settings.GRAPH_TENANT),
        'GRAPH_GROUP_ID': bool(settings.GRAPH_GROUP_ID),
    }
    
    for key, value in config_status.items():
        status = "✓" if value else "✗"
        print(f"   {status} {key}: {'Configured' if value else 'Not configured'}")
    
    if not all(config_status.values()):
        print("\n   ⚠️  Some configuration is missing. Token acquisition may fail.")
    
    # Test 2: Get token status
    print("\n2. Getting token status...")
    try:
        status = MicrosoftGraphTokenService.get_token_status()
        for key, value in status.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
    except Exception as e:
        print(f"   ✗ Error getting token status: {str(e)}")
    
    # Test 3: Try to acquire token
    print("\n3. Testing token acquisition...")
    try:
        token = MicrosoftGraphTokenService.get_access_token('client_credentials')
        if token:
            print("   ✓ Successfully acquired token")
            
            # Test 4: Validate token
            print("\n4. Testing token validation...")
            is_valid = MicrosoftGraphTokenService.validate_token(token)
            if is_valid:
                print("   ✓ Token is valid")
            else:
                print("   ✗ Token validation failed")
        else:
            print("   ✗ Failed to acquire token")
    except Exception as e:
        print(f"   ✗ Error acquiring token: {str(e)}")
    
    # Test 5: Check database tokens
    print("\n5. Checking database tokens...")
    try:
        tokens = MicrosoftGraphToken.objects.all()
        print(f"   Total tokens in database: {tokens.count()}")
        
        for token in tokens:
            status = "Active" if token.is_active else "Inactive"
            expired = "Expired" if token.is_expired() else "Valid"
            print(f"   Token {token.id}: {status}, {expired}, Expires: {token.expires_at}")
    except Exception as e:
        print(f"   ✗ Error checking database tokens: {str(e)}")
    
    # Test 6: Cleanup test
    print("\n6. Testing token cleanup...")
    try:
        cleaned_count = MicrosoftGraphTokenService.cleanup_old_tokens()
        print(f"   Cleaned up {cleaned_count} tokens")
    except Exception as e:
        print(f"   ✗ Error during cleanup: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

def test_token_model():
    """Test the token model functionality"""
    print("\nTesting Token Model Functionality")
    print("=" * 50)
    
    # Create a test token
    print("\n1. Creating test token...")
    try:
        test_token = MicrosoftGraphToken.objects.create(
            token_type='client_credentials',
            access_token='test_token_123',
            expires_at=timezone.now() + timedelta(hours=1),
            scopes='https://graph.microsoft.com/.default',
            tenant_id='test_tenant'
        )
        print(f"   ✓ Created test token with ID: {test_token.id}")
        
        # Test model methods
        print("\n2. Testing model methods...")
        print(f"   Is valid: {test_token.is_valid()}")
        print(f"   Is expired: {test_token.is_expired()}")
        
        # Test error handling
        print("\n3. Testing error handling...")
        test_token.mark_error("Test error")
        print(f"   Error count: {test_token.error_count}")
        print(f"   Last error: {test_token.last_error}")
        
        # Test error reset
        test_token.reset_error_count()
        print(f"   Error count after reset: {test_token.error_count}")
        
        # Test deactivation
        test_token.deactivate()
        print(f"   Is active after deactivation: {test_token.is_active}")
        
        # Clean up test token
        test_token.delete()
        print("\n   ✓ Test token cleaned up")
        
    except Exception as e:
        print(f"   ✗ Error testing token model: {str(e)}")

if __name__ == "__main__":
    try:
        test_token_service()
        test_token_model()
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        sys.exit(1) 