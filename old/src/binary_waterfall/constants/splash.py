import os
import importlib.util

if '_PYIBoot_SPLASH' in os.environ and importlib.util.find_spec("pyi_splash"):
    HAS_SPLASH = True
else:
    HAS_SPLASH = False
