from typing                                                                                 import Optional, Set, Dict, Any
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash    import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.files.safe_uint.Safe_UInt__FileSize           import Safe_UInt__FileSize
from osbot_utils.type_safe.primitives.domains.identifiers.safe_int.Timestamp_Now            import Timestamp_Now
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id             import Safe_Str__Id
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path           import Safe_Str__File__Path
from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe


class Schema__Memory_FS__File__Metadata(Type_Safe):
    content__hash        : Safe_Str__Cache_Hash                  = None
    content__size        : Safe_UInt__FileSize
    chain_hash           : Optional[Safe_Str__Cache_Hash]        = None
    previous_version_path: Optional[Safe_Str__File__Path]        = None         # todo: refactor this logic into a better naming convention and class structure
    tags                 : Set[Safe_Str__Id]                                         # todo: should we move this into an 'user_data' section (since this is the only part of this data object that us editable by the user
    timestamp            : Timestamp_Now
    data                 : Dict[Safe_Str__Id, Any]                                   # this is the area to store extra data about the file
