"""
Entry point for running the app as a module.
Usage: python -m app [demo|interactive|status]
"""

import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import demo_health_assistant, run_interactive_mode, get_system_info

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "demo":
            demo_health_assistant()
        elif mode == "interactive":
            run_interactive_mode()
        elif mode == "status":
            info = get_system_info()
            print(f"System Info: {info}")
        else:
            print("Usage: python -m app [demo|interactive|status]")
            print("  demo: Run demonstration scenarios")
            print("  interactive: Run in interactive mode")
            print("  status: Show system information")
    else:
        # Default to demo mode
        demo_health_assistant() 