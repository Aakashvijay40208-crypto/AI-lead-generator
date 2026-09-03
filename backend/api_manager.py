import os
import logging
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)
logger = logging.getLogger(__name__)

# Usage records for tracking api calls dynamically
key_metrics = {
    "serpapi": {"keys": [], "index": 0, "usage": {}, "disabled": set()},
    "ollama": {"keys": ["local"], "index": 0, "usage": {"local": 0}, "disabled": set()}
}

def _initialize_keys():
    """Parse comma-separated keys from environment variables."""
    # SerpAPI
    serpapi_raw = os.getenv("SERPAPI_API_KEY", "")
    # Check if there is a comma-separated list or fallback to singular
    serpapi_keys = [k.strip() for k in serpapi_raw.split(",") if k.strip()]
    key_metrics["serpapi"]["keys"] = serpapi_keys
    
    # Initialize usage metrics
    for provider in ["serpapi"]:
        for key in key_metrics[provider]["keys"]:
            if key not in key_metrics[provider]["usage"]:
                key_metrics[provider]["usage"][key] = 0

# Init keys
_initialize_keys()

def get_api_key(provider):
    """
    Get the next available API key for a provider in a round-robin fashion.
    If no key is available or valid, returns None (signal for mock/simulated fallback).
    """
    provider = provider.lower()
    if provider not in key_metrics:
        logger.error(f"Unknown API provider: {provider}")
        return None
        
    metrics = key_metrics[provider]
    keys = metrics["keys"]
    disabled = metrics["disabled"]
    
    # Filter keys that are not disabled
    available_keys = [k for k in keys if k not in disabled]
    
    if not available_keys:
        logger.warning(f"No active keys found for provider: {provider}. Fallback to simulated mode.")
        return None
        
    # Round robin increment
    metrics["index"] = (metrics["index"] + 1) % len(available_keys)
    selected_key = available_keys[metrics["index"]]
    
    # Increment usage counter
    metrics["usage"][selected_key] = metrics["usage"].get(selected_key, 0) + 1
    logger.info(f"API Key rotated for {provider}. Current usage of key: {metrics['usage'][selected_key]}")
    
    return selected_key

def disable_key(provider, key):
    """Disable a key if it encounters a quota, authentication, or rate limit error."""
    provider = provider.lower()
    if provider in key_metrics and key:
        key_metrics[provider]["disabled"].add(key)
        logger.warning(f"API Key {key[:6]}... disabled for provider: {provider} due to failure.")

def reset_metrics():
    """Reset usage counts and disabled states (e.g. for a new cycle)."""
    for provider in key_metrics:
        key_metrics[provider]["disabled"].clear()
        for key in key_metrics[provider]["usage"]:
            key_metrics[provider]["usage"][key] = 0
    logger.info("API Key metrics and disabled lists reset.")

def get_provider_status():
    """Return statuses of API keys for dashboard transparency."""
    status = {}
    for provider, data in key_metrics.items():
        total = len(data["keys"])
        active = total - len(data["disabled"])
        status[provider] = {
            "total_keys": total,
            "active_keys": active,
            "total_calls": sum(data["usage"].values()),
            "status": "Active" if active > 0 else "Error"
        }
    return status
