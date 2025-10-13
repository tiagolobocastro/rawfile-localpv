from google.protobuf import any_pb2 as _any_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExpandRawFileStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OK: _ClassVar[ExpandRawFileStatus]
    RESOURCE_EXHAUSTED: _ClassVar[ExpandRawFileStatus]
OK: ExpandRawFileStatus
RESOURCE_EXHAUSTED: ExpandRawFileStatus

class ExpandRawFileRequest(_message.Message):
    __slots__ = ("volume_id", "new_size")
    VOLUME_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_SIZE_FIELD_NUMBER: _ClassVar[int]
    volume_id: str
    new_size: int
    def __init__(self, volume_id: _Optional[str] = ..., new_size: _Optional[int] = ...) -> None: ...

class ExpandRawFileResponse(_message.Message):
    __slots__ = ("is_attached", "status")
    IS_ATTACHED_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    is_attached: bool
    status: ExpandRawFileStatus
    def __init__(self, is_attached: bool = ..., status: _Optional[_Union[ExpandRawFileStatus, str]] = ...) -> None: ...

class GetRawFileRequest(_message.Message):
    __slots__ = ("volume_id", "with_data", "snapshot_id")
    VOLUME_ID_FIELD_NUMBER: _ClassVar[int]
    WITH_DATA_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
    volume_id: str
    with_data: bool
    snapshot_id: str
    def __init__(self, volume_id: _Optional[str] = ..., with_data: bool = ..., snapshot_id: _Optional[str] = ...) -> None: ...

class GetRawFileResponse(_message.Message):
    __slots__ = ("metadata", "data")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _any_pb2.Any
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    metadata: _containers.MessageMap[str, _any_pb2.Any]
    data: bytes
    def __init__(self, metadata: _Optional[_Mapping[str, _any_pb2.Any]] = ..., data: _Optional[bytes] = ...) -> None: ...
