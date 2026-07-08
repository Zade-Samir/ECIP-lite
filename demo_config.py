"""
Demo script to verify the Profile-based Configuration Management system.
Shows active profiles and domain specific settings.
"""
import os
from ecip_core.config.loader import load_settings

def print_settings(s):
    print(f"🌍 Active Profile  : {s.ECIP_PROFILE.upper()}")
    print("-" * 50)
    print(f"📁 Database Path   : {s.database.db_path}")
    print(f"📦 FAISS Index     : {s.faiss.index_path}")
    print(f"📝 Log Level       : {s.logging.level}")
    print(f"🌐 API URL         : http://{s.api.host}:{s.api.port}")
    print(f"🎨 CLI ANSI Colors : {s.cli.ansi_colors}")
    print(f"⚡ Cache Enabled   : {s.cache.enabled}")
    print(f"🔧 LLM Model       : {s.inference.model}")
    print(f"🧠 Embed Model     : {s.embedding.model}")
    print("=" * 50 + "\n")

print("\n" + "="*50)
print("     ECIP Lite — Configuration Profile Demo")
print("="*50)

# Scenario 1: Load development profile (default)
print("1. Loading Default Profile (Development):")
os.environ.pop("ECIP_PROFILE", None)
s_dev = load_settings()
print_settings(s_dev)

# Scenario 2: Load testing profile
print("2. Loading Testing Profile (ECIP_PROFILE=testing):")
os.environ["ECIP_PROFILE"] = "testing"
s_test = load_settings()
print_settings(s_test)

# Scenario 3: Load production profile
print("3. Loading Production Profile (ECIP_PROFILE=production):")
os.environ["ECIP_PROFILE"] = "production"
s_prod = load_settings()
print_settings(s_prod)

# Scenario 4: Env Overrides on top of Development profile
print("4. Environment variable overrides on top of Development profile:")
os.environ["ECIP_PROFILE"] = "development"
os.environ["DB_PATH"] = "custom_path/custom_db.db"
os.environ["MODEL_NAME"] = "custom-deepseek:8b"
os.environ["API_PORT"] = "9090"
s_override = load_settings()
print_settings(s_override)

# Clean up env variables after demo
os.environ.pop("ECIP_PROFILE", None)
os.environ.pop("DB_PATH", None)
os.environ.pop("MODEL_NAME", None)
os.environ.pop("API_PORT", None)

print("Demo complete!")
