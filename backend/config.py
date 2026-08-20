import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Depot Location (Central Base for Trucks)
    DEPOT_LATITUDE = float(os.getenv("DEPOT_LATITUDE", "10.0150"))
    DEPOT_LONGITUDE = float(os.getenv("DEPOT_LONGITUDE", "76.3450"))
    
    # Models directory
    MODELS_DIR = os.getenv(
        "MODELS_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "smart-waste-management", "models")
    )
    
    # Server port
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
