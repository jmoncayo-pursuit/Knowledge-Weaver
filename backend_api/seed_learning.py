
import os
import json
import datetime
import random

def seed_learning_history():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(backend_dir, 'learning_history.jsonl')
    
    # Define scenarios where Human teaches AI
    scenarios = [
        {
            "ai_tags": ["General"],
            "human_tags": ["HR Policy", "Benefits"],
            "category": "Policy",
            "summary": "Added partner key benefits info"
        },
        {
            "ai_tags": ["IT"], 
            "human_tags": ["IT Security", "VPN", "Access Control"],
            "category": "Procedure",
            "summary": "Corrected VPN access tagging"
        },
        {
            "ai_tags": ["Finance"],
            "human_tags": ["Payroll", "Tax", "Compliance"],
            "category": "Policy",
            "summary": "Clarified tax withholding rules"
        },
        {
            "ai_tags": ["General", "Workplace"],
            "human_tags": ["Remote Work", "Compliance"],
            "category": "Policy",
            "summary": "Remote work state compliance"
        },
        {
            "ai_tags": ["Benefits"],
            "human_tags": ["Dental", "Vision", "Orthodontia"],
            "category": "Benefits",
            "summary": "Specific dental coverage details"
        }
    ]
    
    print(f"Seeding learning history to {log_file}...")
    
    entries = []
    
    # Generate 20 events
    for i in range(20):
        scenario = random.choice(scenarios)
        
        # Randomize timestamp within last 7 days
        days_ago = random.randint(0, 7)
        minutes_ago = random.randint(0, 1440)
        timestamp = (datetime.datetime.utcnow() - datetime.timedelta(days=days_ago, minutes=minutes_ago)).isoformat()
        
        event = {
            "timestamp": timestamp,
            "summary": scenario["summary"],
            "ai_prediction": {
                "tags": scenario["ai_tags"],
                "category": "Uncategorized" # AI usually gets it wrong in this story
            },
            "human_correction": {
                "tags": scenario["human_tags"],
                "category": scenario["category"]
            }
        }
        entries.append(event)
        
    # Append to file
    with open(log_file, 'a', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')
            
    print(f"Successfully added {len(entries)} learning events.")

if __name__ == "__main__":
    seed_learning_history()
