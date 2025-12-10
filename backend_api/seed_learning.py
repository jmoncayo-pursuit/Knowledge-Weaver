"""
Seed Learning Data for Knowledge-Weaver
Populates learning_events.json and learning_stats.json with sample data.
"""
import json
import os
import datetime

DATA_DIR = "backend_api/data"
EVENTS_FILE = os.path.join(DATA_DIR, "learning_events.json")
STATS_FILE = os.path.join(DATA_DIR, "learning_stats.json")

def seed_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Create Sample Events
    # Simulating the "Clip 3" correction: Uncategorized -> Policy, added #StrictPolicy_QLE
    events = [
        {
            "id": "evt_1",
            "entry_id": "demo_scenario1_seed",
            "timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat(),
            "summary": "Correction for Demo Scenario 1",
            "source": "user_correction",
            "changes": [
                {
                    "field": "category",
                    "old": "Uncategorized",
                    "new": "Policy / Enrollment Denied",
                    "type": "correction"
                },
                {
                    "field": "tags",
                    "added": ["#StrictPolicy_QLE", "denied"],
                    "type": "refinement"
                }
            ],
            "impact_score": 1.0,
            "ai_prediction": {
                "tags": ["marriage", "insurance"],
                "category": "Uncategorized"
            },
            "human_correction": {
                "tags": ["marriage", "insurance", "#StrictPolicy_QLE", "denied"],
                "category": "Policy / Enrollment Denied"
            }
        },
        {
             "id": "evt_0", # Older event
            "entry_id": "demo_scenario2_seed",
            "timestamp": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
            "summary": "Technical Support Correction",
            "source": "user_correction",
            "changes": [
                {
                    "field": "category",
                    "old": "Uncategorized",
                    "new": "Technical Support",
                    "type": "correction"
                }
            ],
            "impact_score": 0.5,
             "ai_prediction": {
                "tags": ["wifi"],
                "category": "Uncategorized"
            },
            "human_correction": {
                "tags": ["wifi", "network"],
                "category": "Technical Support"
            }
        }
    ]
    
    # 2. Create Sample Stats
    # Generate history (last 7 days)
    history = []
    base_error_rate = 0.05
    for i in range(7):
        # Days 0 to 6 (0 is today, 6 is 7 days ago, reversed in list usually or handled by chart)
        # We want correct chronological order for the chart (oldest to newest)
        day_offset = 6 - i
        date = (datetime.datetime.now() - datetime.timedelta(days=day_offset))
        
        # Simulate some fluctuation
        fluctuation = (day_offset % 3) * 0.01
        rate = base_error_rate + fluctuation
        if day_offset == 0: # Today
            rate = 0.02 # Improvement
            
        history.append({
            "timestamp": date.isoformat(),
            "error_rate": round(rate, 3),
            "accuracy_rate": round(1.0 - rate, 3)
        })

    stats = {
        "total_corrections": 12,
        "learnings_applied": 8,
        "accuracy_rate": 0.98,
        "top_learned_tags": [
             {"tag": "Policy", "count": 15},
             {"tag": "Compliance", "count": 12},
             {"tag": "Enrollment", "count": 8},
             {"tag": "HIPAA", "count": 6},
             {"tag": "Technical", "count": 4},
             {"tag": "Dental", "count": 3}
        ],
        "errors_over_time": history
    }
    
    # Write files
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events, f, indent=2)
        
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
        
    print(f"Seeded {len(events)} events and stats to {DATA_DIR}")

    # 3. Seed Vector DB with the Entry (so it can be edited)
    try:
        import sys
        # Add the current directory to path so we can import services
        # Assuming we are running from project root, backend_api is in path?
        # No, let's just make sure backend_api is in path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
            
        from services.vector_db import VectorDatabase
        
        # Determine persist directory relative to this script
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        persist_dir = os.path.join(project_root, "chroma_db")
        
        print(f"Seeding Vector DB in: {persist_dir}")
        vector_db = VectorDatabase(persist_directory=persist_dir)
        vector_db.initialize()
        
        # Define the entry
        entry_id = "demo_scenario1_seed"
        content = "Employee requesting to add spouse to insurance outside of open enrollment period. Denied due to strict policy on QLE timing."
        metadata = {
                "source": "seed_script",
                "category": "Uncategorized", 
                "tags": "marriage, insurance", # Store as string for Chroma metadata? Or stringified list
                "timestamp": datetime.datetime.now().isoformat(),
                "summary": "Employee spouse addition request (Denied)",
                "verification_status": "unverified",
                "type": "email"
        }

        # Create a dummy embedding (768 dimensions is common)
        # Verify dimension from vector_db if possible, but 768 is fine for text-embedding-004 usually
        dummy_embedding = [0.1] * 768 
        
        # Delete if exists to ensure clean state
        try:
             vector_db.collection.delete(ids=[entry_id])
        except:
             pass

        # Add to collection directly
        vector_db.collection.add(
            ids=[entry_id],
            documents=[content],
            metadatas=[metadata],
            embeddings=[dummy_embedding]
        )
        print(f"Successfully injected entry '{entry_id}' into Vector DB.")
        
    except ImportError:
        print("Could not import VectorDatabase, skipping DB seed.")
    except Exception as e:
        print(f"Failed to seed VectorDB: {e}")

    print(f"Seeded {len(events)} events and stats to {DATA_DIR}")

if __name__ == "__main__":
    seed_data()
