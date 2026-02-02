from dremio_cli.config import ProfileManager
from typing import Dict, Any, Optional

class DremioConfig:
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self._manager = ProfileManager()
        self.profile_data = self._load_profile(profile_name)

    def _load_profile(self, name: str) -> Dict[str, Any]:
        """Loads profile using various fallbacks."""
        # 1. Try explicit profile name
        profile = self._manager.get_profile(name)
        if profile:
            return profile
            
        # 2. If 'default' requested but not found, try getting system default
        if name == "default":
             # ProfileManager doesn't expose logic to get "the default" easily?
             # Let's check `get_default_profile`
             default_name = self._manager.get_default_profile()
             if default_name:
                 return self._manager.get_profile(default_name)
        
        # 3. Fallback: Check if there is only ONE profile and just use it? 
        # (Maybe unsafe, better to error if name explicit)
        
        raise ValueError(f"Profile '{name}' not found.")

    def get_dict(self) -> Dict[str, Any]:
        """Returns the raw profile dictionary expected by create_client."""
        return self.profile_data
