# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
import io
from typing import Dict, List, Tuple

from UM.VersionUpgrade import VersionUpgrade

_renamed_settings = {
    "support_minimal_diameter": "support_tower_maximum_supported_diameter"
} #type: Dict[str, str]

##  Upgrades configurations from the state they were in at version 4.1 to the
#   state they should be in at version 4.2.
class VersionUpgrade41to42(VersionUpgrade):
    ##  Gets the version number from a CFG file in Uranium's 4.1 format.
    #
    #   Since the format may change, this is implemented for the 4.1 format only
    #   and needs to be included in the version upgrade system rather than
    #   globally in Uranium.
    #
    #   \param serialised The serialised form of a CFG file.
    #   \return The version number stored in the CFG file.
    #   \raises ValueError The format of the version number in the file is
    #   incorrect.
    #   \raises KeyError The format of the file is incorrect.
    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version")) #Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

    ##  Upgrades instance containers to have the new version
    #   number.
    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "8"

        #Rename settings.
        if "values" in parser:
            for old_name, new_name in _renamed_settings.items():
                if old_name in parser["values"]:
                    parser[new_name] = parser[old_name]
                    del parser[old_name]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "8"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
