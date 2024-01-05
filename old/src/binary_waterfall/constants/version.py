import os
import yaml

from . import paths

# Read program version file
VERSION_FILE = os.path.join(paths.PATH, "version.yml")
with open(VERSION_FILE, "r") as f:
    version_file_dict = yaml.safe_load(f)

    VERSION = version_file_dict["Version"]
    DESCRIPTION = version_file_dict["FileDescription"]
    TITLE = version_file_dict["InternalName"]
    LONG_TITLE = version_file_dict["ProductName"]
    COPYRIGHT = version_file_dict["LegalCopyright"]
