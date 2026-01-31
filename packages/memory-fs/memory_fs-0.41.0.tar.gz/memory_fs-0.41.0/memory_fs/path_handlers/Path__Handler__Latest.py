from memory_fs.path_handlers.Path__Handler                                      import Path__Handler
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id              import Safe_Str__Id
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path  import Safe_Str__File__Path


class Path__Handler__Latest(Path__Handler):                                             # Handler that stores files in a 'latest' directory
    latest_folder : Safe_Str__File__Path = Safe_Str__File__Path("latest")                # Configurable latest folder name
    name          : Safe_Str__Id               = Safe_Str__Id("latest")

    def generate_path(self, file_id  : Safe_Str__Id              = None,                     # not used by this path handler
                            file_key : Safe_Str__File__Path = None                      # not used by this path handler
                       ) -> Safe_Str__File__Path:                                       # Generate path with latest folder
        return self.combine_paths(str(self.latest_folder))