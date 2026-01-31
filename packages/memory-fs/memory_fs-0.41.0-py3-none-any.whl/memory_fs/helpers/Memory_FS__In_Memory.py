from memory_fs.Memory_FS                               import Memory_FS
from memory_fs.storage_fs.providers.Storage_FS__Memory import Storage_FS__Memory


class Memory_FS__In_Memory(Memory_FS):
    storage_fs : Storage_FS__Memory