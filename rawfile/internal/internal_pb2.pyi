from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
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
