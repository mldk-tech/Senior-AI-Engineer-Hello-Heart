#!/usr/bin/env python3
"""
Simple test to check if imports work correctly.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    print("1. Testing config import...")
    from app.core.config import get_settings
    print("✓ Config import successful")
    
    print("2. Testing schemas import...")
    from app.models.schemas import HealthAssistantState
    print("✓ Schemas import successful")
    
    print("3. Testing base agent import...")
    from app.agents.base import BaseHealthAgent
    print("✓ Base agent import successful")
    
    print("4. Testing workflow import...")
    from app.orchestration.workflow import HealthAIAssistant
    print("✓ Workflow import successful")
    
    print("5. Testing main import...")
    from app.main import demo_health_assistant
    print("✓ Main import successful")
    
    print("\nAll imports successful! Ready to run demo.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.") 