import sys
import os
from dataclasses import asdict

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import persistence
from services.sample_data import make_users

if __name__ == '__main__':
    users = [asdict(u) for u in make_users(20)]
    persistence.replace_all('users', users)
    print("Successfully seeded 20 users directly to data/users.json")