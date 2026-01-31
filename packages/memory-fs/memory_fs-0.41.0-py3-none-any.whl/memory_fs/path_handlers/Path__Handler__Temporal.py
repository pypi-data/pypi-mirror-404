from datetime                                                                       import datetime
from typing                                                                         import List
from memory_fs.path_handlers.Path__Handler                                          import Path__Handler
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                   import Safe_Str__Id
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path   import Safe_Str__File__Path

DEFAULT__PATH_HANDLER__TEMPORAL__TIME_PATH = "%Y/%m/%d/%H"


class Path__Handler__Temporal(Path__Handler):                                           # Handler that stores files in temporal directory structure
    areas             : List[Safe_Str__Id]
    name              : Safe_Str__Id       = Safe_Str__Id("temporal")
    time_path_pattern : str           = DEFAULT__PATH_HANDLER__TEMPORAL__TIME_PATH

    def generate_path(self, file_id  : Safe_Str__Id              = None,                     # not used by this path handler
                            file_key : Safe_Str__File__Path = None                      # not used by this path handler
                       ) -> Safe_Str__File__Path:                                       # Generate temporal path with areas
        middle_segments = []

        # Add temporal component
        middle_segments.append(self.path_now())

        # Add areas if defined
        if self.areas:
            areas_path = "/".join(str(area) for area in self.areas)
            middle_segments.append(areas_path)

        return self.combine_paths(*middle_segments)

    def path_now(self) -> str:                                                           # Generate current time path
        now       = datetime.now()
        time_path = now.strftime(self.time_path_pattern)
        return time_path