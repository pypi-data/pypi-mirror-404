from memory_fs.path_handlers.Path__Handler                                         import Path__Handler
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                  import Safe_Str__Id
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path  import Safe_Str__File__Path


class Path__Handler__Custom(Path__Handler):                                             # Handler that uses a custom path
    custom_path : Safe_Str__File__Path
    name        : Safe_Str__Id = Safe_Str__Id("custom")

    def generate_path(self, file_id  : Safe_Str__Id              = None,                     # not used by this path handler
                            file_key : Safe_Str__File__Path = None                      # not used by this path handler
                       ) -> Safe_Str__File__Path:                                       # Generate custom path
        if self.custom_path:
            return self.combine_paths(str(self.custom_path))
        return self.combine_paths()