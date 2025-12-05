import sys
import os

# Add backend_api to path
sys.path.append(os.path.abspath("backend_api"))

try:
    from services.vision_service import VisionService
    print("Successfully imported VisionService")
    
    # Check methods
    service = VisionService(api_key="test_key")
    if hasattr(service, 'analyze_image_for_pii') and hasattr(service, 'redact_image'):
        print("VisionService has required methods")
    else:
        print("VisionService missing methods")
        sys.exit(1)
        
except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
