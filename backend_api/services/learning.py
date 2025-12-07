"""
Learning Service for Knowledge-Weaver
Tracks corrections and updates to calculate 'Active Learning' metrics.
"""
import logging
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class LearningService:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Robust path finding: backend_api/services/../data -> backend_api/data
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        else:
            self.data_dir = data_dir
            
        self.learning_log_path = os.path.join(self.data_dir, "learning_events.json")
        self.stats_path = os.path.join(self.data_dir, "learning_stats.json")
        
        # Ensure directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing data or initialize
        self.events = self._load_json(self.learning_log_path, [])
        self.stats = self._load_json(self.stats_path, {
            "total_corrections": 0,
            "accuracy_rate": 0.95, # Initial baseline
            "errors_over_time": [] 
        })
        
        logger.info("LearningService initialized")

    def _load_json(self, path, default):
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
        return default

    def _save_json(self, path, data):
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {path}: {e}")

    def log_learning_event(self, entry_id: str, old_data: dict, new_data: dict, source: str = "user_correction"):
        """
        Log a learning event when a human corrects AI data.
        """
        timestamp = datetime.now().isoformat()
        
        # Detect changes
        changes = []
        
        # Category Change
        old_cat = old_data.get('category', 'Uncategorized')
        new_cat = new_data.get('category', old_cat)
        if old_cat != new_cat:
            changes.append({
                "field": "category",
                "old": old_cat,
                "new": new_cat,
                "type": "correction"
            })
            
        # Tag Changes
        old_tags = set(old_data.get('tags', '').split(',')) if old_data.get('tags') else set()
        new_tags = set(new_data.get('tags', '').split(',')) if new_data.get('tags') else set()
        
        added_tags = new_tags - old_tags
        if added_tags:
            changes.append({
                "field": "tags",
                "added": list(added_tags),
                "type": "refinement"
            })
            
        if not changes:
            return None

        event = {
            "id": f"evt_{len(self.events) + 1}",
            "entry_id": entry_id,
            "timestamp": timestamp,
            "source": source,
            "changes": changes,
            "impact_score": len(changes) * 0.5 # Simple scoring
        }
        
        self.events.insert(0, event) # Newest first
        self.events = self.events[:100] # Keep last 100
        self._save_json(self.learning_log_path, self.events)
        
        # Update Stats
        self._update_stats(changes)
        
        return event

    def _update_stats(self, changes):
        """Update aggregate learning statistics"""
        correction_count = sum(1 for c in changes if c.get('type') == 'correction')
        
        self.stats["total_corrections"] += correction_count
        
        # Simulate Error Rate calculation (Exponential Moving Average)
        # If we have corrections, error rate spikes slightly, then decays
        current_error_rate = 1.0 - self.stats.get("accuracy_rate", 0.95)
        
        if correction_count > 0:
            # Error observed
            new_error_rate = min(current_error_rate + 0.05, 1.0)
        else:
            # Recovery/Learning
            new_error_rate = max(current_error_rate * 0.9, 0.01)
            
        self.stats["accuracy_rate"] = 1.0 - new_error_rate
        
        # Log timeline point
        point = {
            "timestamp": datetime.now().isoformat(),
            "error_rate": round(new_error_rate, 4),
            "accuracy": round(self.stats["accuracy_rate"], 4)
        }
        self.stats.setdefault("errors_over_time", []).append(point)
        # Keep last 50 points
        self.stats["errors_over_time"] = self.stats["errors_over_time"][-50:]
        
        self._save_json(self.stats_path, self.stats)

    def get_learning_log(self, limit=10):
        """Get recent learning events, merging from both sources"""
        all_events = list(self.events)  # Start with existing events
        
        # Also read from the JSONL history file (written by update endpoint)
        jsonl_path = os.path.join(os.path.dirname(self.data_dir), "learning_history.jsonl")
        
        if os.path.exists(jsonl_path):
            try:
                with open(jsonl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                            # Transform to expected format
                            ai_pred = event.get("ai_prediction", {})
                            human_corr = event.get("human_correction", {})
                            
                            formatted_event = {
                                "id": f"evt_{len(all_events) + 1}",
                                "entry_id": "manual_edit",
                                "timestamp": event.get("timestamp", datetime.now().isoformat()),
                                "source": "user_correction",
                                "summary": event.get("summary", "Manual edit correction"),
                                "changes": [],
                                "ai_prediction": ai_pred,
                                "human_correction": human_corr
                            }
                            
                            # Add change entries
                            if ai_pred.get("category") != human_corr.get("category"):
                                formatted_event["changes"].append({
                                    "field": "category",
                                    "old": ai_pred.get("category"),
                                    "new": human_corr.get("category"),
                                    "type": "correction"
                                })
                            
                            if ai_pred.get("tags") != human_corr.get("tags"):
                                formatted_event["changes"].append({
                                    "field": "tags", 
                                    "old": ai_pred.get("tags", []),
                                    "added": human_corr.get("tags", []),
                                    "type": "refinement"
                                })
                            
                            all_events.append(formatted_event)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"Error reading learning history JSONL: {e}")
        
        # Sort by timestamp descending (newest first)
        all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return all_events[:limit]

    def get_stats(self):
        return self.stats
