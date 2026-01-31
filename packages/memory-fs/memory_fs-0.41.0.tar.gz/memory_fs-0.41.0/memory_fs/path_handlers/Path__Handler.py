from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path   import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                   import Safe_Str__Id
from osbot_utils.type_safe.Type_Safe                                                import Type_Safe


class Path__Handler(Type_Safe):
    name        : Safe_Str__Id               = None
    prefix_path : Safe_Str__File__Path = None                                           # Optional prefix path
    suffix_path : Safe_Str__File__Path = None                                           # Optional suffix path

    def generate_path(self, file_id:Safe_Str__Id                = None                       # allow the file_id to be used by overwritten methods
                          , file_key: Safe_Str__File__Path = None                       # allow the file_key to be used by overwritten methods
                       ) -> Safe_Str__File__Path:
        return self.combine_paths()

    def combine_paths(self, *middle_segments : str                                      # Combines prefix + middle + suffix
                     ) -> Safe_Str__File__Path:
        path_segments = []

        if self.prefix_path:                                                            # Add prefix if exists
            path_segments.append(str(self.prefix_path))

        for segment in middle_segments:                                                 # Add middle segments
            if segment:
                path_segments.append(str(segment))

        if self.suffix_path:                                                            # Add suffix if exists
            path_segments.append(str(self.suffix_path))

        if path_segments:                                                               # Combine all segments
            return Safe_Str__File__Path("/".join(path_segments))
        return Safe_Str__File__Path("")