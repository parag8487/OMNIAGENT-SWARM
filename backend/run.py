"""
OmniAgent Swarm Backend Entry Point
"""

import os
import sys

# Resolve Windows console encoding issues: set UTF-8 before all imports
if sys.platform == 'win32':
    # Set environment variable to ensure Python uses UTF-8
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    # Reconfigure standard output streams to UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    """Main entry point for Gunicorn or other WSGI servers"""
    # Validate configuration
    errors = Config.validate()
    if errors:
        print("Configuration Errors:")
        for err in errors:
            print(f"  - {err}")
        print("\nPlease check your .env file configuration")
        if __name__ == '__main__':
            sys.exit(1)
    
    # Create application
    app = create_app()
    return app


if __name__ == '__main__':
    # This block only runs when executing directly: python run.py
    app = main()
    
    # Get execution configuration
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = Config.DEBUG
    
    # Start service
    print(f"Starting OmniAgent Swarm Backend on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug, threaded=True)
