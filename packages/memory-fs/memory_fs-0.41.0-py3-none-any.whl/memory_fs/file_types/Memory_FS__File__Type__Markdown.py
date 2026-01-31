from memory_fs.schemas.Enum__Memory_FS__File__Content_Type import Enum__Memory_FS__File__Content_Type
from memory_fs.schemas.Enum__Memory_FS__File__Encoding     import Enum__Memory_FS__File__Encoding
from memory_fs.schemas.Enum__Memory_FS__Serialization      import Enum__Memory_FS__Serialization
from memory_fs.schemas.Schema__Memory_FS__File__Type       import Schema__Memory_FS__File__Type
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id                           import Safe_Str__Id


class Memory_FS__File__Type__Markdown(Schema__Memory_FS__File__Type):
    name           = Safe_Str__Id("markdown")
    content_type   = Enum__Memory_FS__File__Content_Type.MARKDOWN
    file_extension = Safe_Str__Id("md")
    alt_extensions = [Safe_Str__Id("markdown")]
    encoding       = Enum__Memory_FS__File__Encoding.UTF_8
    serialization  = Enum__Memory_FS__Serialization.STRING