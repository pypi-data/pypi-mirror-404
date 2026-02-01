import os
import yaml
from typing import Dict, Any, Optional

def load_profiles(path: str = None) -> Dict[str, Any]:
    """
    Load profiles from YAML file.
    Default path: ~/.dremio/profiles.yaml
    """
    if path is None:
        home = os.path.expanduser("~")
        path = os.path.join(home, ".dremio", "profiles.yaml")
        
    if not os.path.exists(path):
        return {}
        
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            return data or {}
    except Exception as e:
        print(f"Warning: Failed to load profiles from {path}: {e}")
        return {}

def get_profile_config(profile_name: str, profiles_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific profile.
    If profiles_data is not provided, it loads from default location.
    """
    if profiles_data is None:
        profiles_data = load_profiles()
        
    # Structure is usually:
    # profiles:
    #   profile_name: ...
    
    profiles = profiles_data.get("profiles", {})
    return profiles.get(profile_name)

def get_default_profile__name(profiles_data: Dict[str, Any] = None) -> Optional[str]:
    """
    Get the default profile name if specified.
    """
    if profiles_data is None:
        profiles_data = load_profiles()
        
    return profiles_data.get("default_profile")
