from typing                                                         import List
from memory_fs.path_handlers.Path__Handler__Temporal                import Path__Handler__Temporal
from osbot_utils.type_safe.primitives.domains.identifiers.safe_str.Safe_Str__Id  import Safe_Str__Id
from memory_fs.Memory_FS                                            import Memory_FS


class Memory_FS__Temporal(Memory_FS):                                                   # Temporal-only pattern
    handler__temporal : Path__Handler__Temporal = None

    def __init__(self, storage_fs = None  ,
                       areas      : List[Safe_Str__Id] = None,
                       **kwargs ):                                                      # params for Path__Handler
        super().__init__(storage_fs=storage_fs)
        self.handler__temporal = self.add_handler__temporal(areas=areas, **kwargs)
