from memory_fs.schemas.Enum__Memory_FS__File__Content_Type                       import Enum__Memory_FS__File__Content_Type
from memory_fs.schemas.Enum__Memory_FS__Serialization                            import Enum__Memory_FS__Serialization
from memory_fs.schemas.Schema__Memory_FS__File__Type                             import Schema__Memory_FS__File__Type
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id  import Safe_Str__Id


class Memory_FS__File__Type__Binary(Schema__Memory_FS__File__Type):
    name           = Safe_Str__Id("binary")
    content_type   = Enum__Memory_FS__File__Content_Type.BINARY
    file_extension = Safe_Str__Id("bin")                              # Generic binary extension
    encoding       = None                                        # No encoding for raw binary
    serialization  = Enum__Memory_FS__Serialization.BINARY       # Raw bytes