from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id import Safe_Str__Id
from memory_fs.file_types.Memory_FS__File__Type__Json                           import Memory_FS__File__Type__Json

# todo: look at adding support for
class Memory_FS__File__Type__Json__Single(Memory_FS__File__Type__Json):     # JSON file type that only creates content file (no .config or .metadata)"""
    name = Safe_Str__Id("json_single")