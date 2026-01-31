from typing                                                                        import Dict, List
from osbot_utils.utils.Json                                                        import bytes_to_json
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                     import type_safe
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path  import Safe_Str__File__Path
from memory_fs.storage_fs.Storage_FS                                               import Storage_FS

# todo: see if this class shouldn't be leveraging the Serialisation and DeSerialisation classes/logic

class Storage_FS__Memory(Storage_FS):
    content_data: Dict[Safe_Str__File__Path, bytes]

    def clear(self):
        self.content_data.clear()
        return True

    @type_safe
    def file__bytes(self, path: Safe_Str__File__Path):
        return self.content_data.get(path)

    @type_safe
    def file__delete(self, path: Safe_Str__File__Path) -> bool:
        if path in self.content_data:
            del self.content_data[path]
            return True
        return False

    @type_safe
    def file__exists(self, path: Safe_Str__File__Path):
        return path in self.content_data

    @type_safe
    def file__json(self, path: Safe_Str__File__Path):
        file_bytes = self.file__bytes(path)
        if file_bytes:
            return bytes_to_json(file_bytes)

    @type_safe
    def file__save(self, path: Safe_Str__File__Path, data: bytes) -> bool:
        self.content_data[path] = data
        return True

    @type_safe
    def file__str(self, path: Safe_Str__File__Path):
        file_bytes = self.file__bytes(path)
        if file_bytes:
            return file_bytes.decode()                  # todo: add content type to this decode


    def files__paths(self):
        return self.content_data.keys()

    def folder__folders(self, parent_folder: Safe_Str__File__Path,
                              return_full_path: bool = True
                         ) -> List[Safe_Str__File__Path]:
        subfolders = set()
        prefix = str(parent_folder)

        # Normalize prefix - empty or '/' means root
        is_root = not prefix or prefix == '/'
        if not is_root and not prefix.endswith('/'):
            prefix += '/'

        for path_str in self.content_data.keys():
            path_str = str(path_str)

            # Skip if not under this prefix (unless root)
            if not is_root and not path_str.startswith(prefix):
                continue

            # Get the relevant path portion
            if is_root:
                remainder = path_str
            else:
                remainder = path_str[len(prefix):]

            # Extract first folder from remainder
            parts = remainder.split('/')
            if parts and parts[0]:  # Has at least one folder component
                if is_root or len(parts) > 1:  # Root level or has subfolder
                    folder_name = parts[0]
                    if return_full_path and not is_root:
                        folder_path = prefix + folder_name
                    else:
                        folder_path = folder_name
                    subfolders.add(Safe_Str__File__Path(folder_path))

        return sorted(subfolders)

    # todo: add unit tests for this method
    def folder__files__all(self, parent_folder: Safe_Str__File__Path) -> List[Safe_Str__File__Path]:         # Get all files under a specific folder
        matching_files = []
        prefix         = str(parent_folder)
        if not prefix.endswith('/'):
            prefix += '/'

        for path in self.content_data.keys():
            if str(path).startswith(prefix):
                matching_files.append(path)

        return matching_files

    def folder__files(self, folder_path     : Safe_Str__File__Path,
                            return_full_path: bool = False
                       ) -> List[Safe_Str__File__Path]:                 # List files in a specific folder (not including subfolders)
        files = []
        prefix = str(folder_path)

        is_root = not prefix or prefix == '/'                           # Normalize prefix - empty or '/' means root
        if not is_root and not prefix.endswith('/'):
            prefix += '/'

        for path_str in self.content_data.keys():
            path_str = str(path_str)

            if not is_root and not path_str.startswith(prefix):         # Skip if not under this prefix (unless root)
                continue

            if is_root:                                                 # Get the relevant path portion
                remainder = path_str
            else:
                remainder = path_str[len(prefix):]


            if '/' not in remainder and remainder:                      # Only include files directly in this folder (no '/' in remainder)
                if return_full_path:
                    files.append(Safe_Str__File__Path(path_str))
                else:
                    files.append(Safe_Str__File__Path(remainder))

        return sorted(files)