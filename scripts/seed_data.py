import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import _demo_seed_users

if __name__ == '__main__':
    _demo_seed_users(n=20)