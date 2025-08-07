#!/usr/bin/env python3
"""
Simple script to run the Hello Heart AI Assistant demo.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting Hello Heart AI Assistant Demo...")

try:
    from app.main import demo_health_assistant
    print("✓ Successfully imported demo function")
    
    print("\n" + "="*60)
    print("RUNNING HELLO HEART AI ASSISTANT DEMO")
    print("="*60)
    
    demo_health_assistant()
    
    print("\n" + "="*60)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("="*60)
    
except Exception as e:
    print(f"❌ Error running demo: {e}")
    import traceback
    traceback.print_exc() 