import os
import importlib.util

from src import binary_waterfall

if '_PYIBoot_SPLASH' in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash
    pyi_splash.close()

if __name__ == "__main__":
    binary_waterfall.run()
