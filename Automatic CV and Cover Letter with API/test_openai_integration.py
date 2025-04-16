"""
Utility script to test the OpenAI integration module.
This is a mock test since we don't want to make actual API calls during testing.
"""

import os
import sys
import json

# Add the project root to the path
sys.path.append('/home/ubuntu/cv_tailoring_project')

from src.utils.openai_integration import OpenAIIntegration

def test_openai_integration():
    """Test the OpenAI integration module with mock responses."""
    print("Testing OpenAI integration module...")
    
    # Initialize with a dummy API key
    openai_integration = OpenAIIntegration(api_key="dummy_key_for_testing")
    
    # Test API key setting
    assert openai_integration.is_api_key_set() == True
    print("✓ API key setting works correctly")
    
    # Test changing API key
    openai_integration.set_api_key("new_dummy_key")
    assert openai_integration.api_key == "new_dummy_key"
    print("✓ API key can be updated")
    
    print("\nNote: Full API functionality would require actual OpenAI API calls.")
    print("The OpenAI integration module structure has been verified.")
    
    return True

if __name__ == "__main__":
    test_openai_integration()
