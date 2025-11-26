import sys
import os

# Ensure the parent directory is in the path to import gem_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from gem_core.gem import Gem
except ImportError as e:
    print(f"DEBUG: Failed to import Gem from gem_core: {e}")
    # Fallback if running from a different context or if installed as a package where gem_core is a sibling
    try:
        from ..gem_core.gem import Gem
    except ImportError as e2:
        print(f"DEBUG: Failed to import Gem from ..gem_core: {e2}")
        raise ImportError(f"Could not import Gem from gem_core. Ensure gem_core is in the python path. Original error: {e}")
