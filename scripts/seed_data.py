import sys
import os
from pathlib import Path
from datetime import datetime
import uuid

# Add project root to python path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import get_connection
from database.models import Module, Topic
from database.repositories.module_repo import ModuleRepository
from database.repositories.topic_repo import TopicRepository

def seed_data():
    print("🌱 Seeding database with default LawFlow templates...")
    
    modules_data = {
        "Land Law": ["Registration", "Co-ownership", "Leases", "Easements", "Mortgages"],
        "Tort Law": ["Negligence", "Nuisance", "Defamation", "Trespass", "Vicarious Liability"],
        "Employment Law": ["Contracts of Employment", "Unfair Dismissal", "Discrimination", "Redundancy"],
        "Legal Practice": ["Professional Conduct", "Solicitors' Accounts", "Money Laundering", "Client Care"]
    }
    
    with get_connection() as conn:
        module_repo = ModuleRepository(conn)
        topic_repo = TopicRepository(conn)
        
        for module_name, topics in modules_data.items():
            # Check if module exists
            existing = None
            try:
                # We don't have get_by_name, so we iterate or just try create and catch error if unique constraint
                # But for seeding, let's just check all
                all_modules = module_repo.get_all()
                existing = next((m for m in all_modules if m.name == module_name), None)
            except Exception:
                pass
            
            if existing:
                print(f"🔹 Module '{module_name}' already exists.")
                module_id = existing.id
            else:
                print(f"✨ Creating Module: {module_name}")
                new_module = Module.create(name=module_name)
                module_repo.create(new_module)
                module_id = new_module.id
            
            # Create Topics
            for topic_name in topics:
                # Check if topic exists for this module
                existing_topics = topic_repo.get_for_module(module_id)
                if any(t.name == topic_name for t in existing_topics):
                    continue
                    
                print(f"  - Adding Topic: {topic_name}")
                new_topic = Topic.create(module_id=module_id, name=topic_name)
                topic_repo.create(new_topic)
                
    print("✅ Seeding complete! Please refresh your app.")

if __name__ == "__main__":
    seed_data()
