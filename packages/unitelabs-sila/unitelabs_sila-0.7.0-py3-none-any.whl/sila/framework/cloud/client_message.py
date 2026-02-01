import dataclasses
import uuid

import typing_extensions as typing

from ..binary_transfer import (
    DeleteBinaryRequest,
    DownloadChunkRequest,
    GetBinaryInfoRequest,
    UploadChunkRequest,
)
from ..protobuf import Message, Reader, WireType, Writer
from .cancel_request import CancelRequest
from .command_execution_request import CommandExecutionRequest
from .command_response_request import CommandResponseRequest
from .create_binary_upload_request import CreateBinaryUploadRequest
from .metadata_request import MetadataRequest
from .property_request import PropertyRequest


@dataclasses.dataclass
class ClientMessage(Message):
    """
    Message sent from client to server through the cloud stream.

    Attributes:
      request_uuid: Unique ID used to map responses to requests.
    """

    request_uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    unobservable_command_execution: CommandExecutionRequest | None = None
    observable_command_initiation: CommandExecutionRequest | None = None
    observable_command_execution_info: CommandResponseRequest | None = None
    observable_command_intermediate_response: CommandResponseRequest | None = None
    observable_command_response: CommandResponseRequest | None = None
    metadata_request: MetadataRequest | None = None
    unobservable_property_read: PropertyRequest | None = None
    observable_property_subscription: PropertyRequest | None = None
    cancel_observable_command_execution_info: CancelRequest | None = None
    cancel_observable_command_intermediate_response: CancelRequest | None = None
    cancel_observable_property: CancelRequest | None = None
    create_binary_upload_request: CreateBinaryUploadRequest | None = None
    delete_uploaded_binary_request: DeleteBinaryRequest | None = None
    upload_chunk_request: UploadChunkRequest | None = None
    get_binary_info_request: GetBinaryInfoRequest | None = None
    download_chunk_request: DownloadChunkRequest | None = None
    delete_downloaded_binary_request: DeleteBinaryRequest | None = None

    @typing.override
    @classmethod
    def decode(cls, reader: Reader | bytes | bytearray, length: int | None = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = cls(request_uuid="")
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.LEN)
                message.request_uuid = reader.read_string()
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message.unobservable_command_execution = CommandExecutionRequest.decode(reader, reader.read_uint32())
            elif field_number == 3:
                reader.expect_type(tag, WireType.LEN)
                message.observable_command_initiation = CommandExecutionRequest.decode(reader, reader.read_uint32())
            elif field_number == 4:
                reader.expect_type(tag, WireType.LEN)
                message.observable_command_execution_info = CommandResponseRequest.decode(reader, reader.read_uint32())
            elif field_number == 5:
                reader.expect_type(tag, WireType.LEN)
                message.observable_command_intermediate_response = CommandResponseRequest.decode(
                    reader, reader.read_uint32()
                )
            elif field_number == 6:
                reader.expect_type(tag, WireType.LEN)
                message.observable_command_response = CommandResponseRequest.decode(reader, reader.read_uint32())
            elif field_number == 7:
                reader.expect_type(tag, WireType.LEN)
                message.metadata_request = MetadataRequest.decode(reader, reader.read_uint32())
            elif field_number == 8:
                reader.expect_type(tag, WireType.LEN)
                message.unobservable_property_read = PropertyRequest.decode(reader, reader.read_uint32())
            elif field_number == 9:
                reader.expect_type(tag, WireType.LEN)
                message.observable_property_subscription = PropertyRequest.decode(reader, reader.read_uint32())
            elif field_number == 10:
                reader.expect_type(tag, WireType.LEN)
                message.cancel_observable_command_execution_info = CancelRequest.decode(reader, reader.read_uint32())
            elif field_number == 11:
                reader.expect_type(tag, WireType.LEN)
                message.cancel_observable_command_intermediate_response = CancelRequest.decode(
                    reader, reader.read_uint32()
                )
            elif field_number == 12:
                reader.expect_type(tag, WireType.LEN)
                message.cancel_observable_property = CancelRequest.decode(reader, reader.read_uint32())
            elif field_number == 13:
                reader.expect_type(tag, WireType.LEN)
                message.create_binary_upload_request = CreateBinaryUploadRequest.decode(reader, reader.read_uint32())
            elif field_number == 14:
                reader.expect_type(tag, WireType.LEN)
                message.delete_uploaded_binary_request = DeleteBinaryRequest.decode(reader, reader.read_uint32())
            elif field_number == 15:
                reader.expect_type(tag, WireType.LEN)
                message.upload_chunk_request = UploadChunkRequest.decode(reader, reader.read_uint32())
            elif field_number == 16:
                reader.expect_type(tag, WireType.LEN)
                message.get_binary_info_request = GetBinaryInfoRequest.decode(reader, reader.read_uint32())
            elif field_number == 17:
                reader.expect_type(tag, WireType.LEN)
                message.download_chunk_request = DownloadChunkRequest.decode(reader, reader.read_uint32())
            elif field_number == 18:
                reader.expect_type(tag, WireType.LEN)
                message.delete_downloaded_binary_request = DeleteBinaryRequest.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: Writer | None = None, number: int | None = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.request_uuid:
            writer.write_uint32(10).write_string(self.request_uuid)

        if self.unobservable_command_execution is not None:
            self.unobservable_command_execution.encode(writer, 2)

        if self.observable_command_initiation is not None:
            self.observable_command_initiation.encode(writer, 3)

        if self.observable_command_execution_info is not None:
            self.observable_command_execution_info.encode(writer, 4)

        if self.observable_command_intermediate_response is not None:
            self.observable_command_intermediate_response.encode(writer, 5)

        if self.observable_command_response is not None:
            self.observable_command_response.encode(writer, 6)

        if self.metadata_request is not None:
            self.metadata_request.encode(writer, 7)

        if self.unobservable_property_read is not None:
            self.unobservable_property_read.encode(writer, 8)

        if self.observable_property_subscription is not None:
            self.observable_property_subscription.encode(writer, 9)

        if self.cancel_observable_command_execution_info is not None:
            self.cancel_observable_command_execution_info.encode(writer, 10)

        if self.cancel_observable_command_intermediate_response is not None:
            self.cancel_observable_command_intermediate_response.encode(writer, 11)

        if self.cancel_observable_property is not None:
            self.cancel_observable_property.encode(writer, 12)

        if self.create_binary_upload_request is not None:
            self.create_binary_upload_request.encode(writer, 13)

        if self.delete_uploaded_binary_request is not None:
            self.delete_uploaded_binary_request.encode(writer, 14)

        if self.upload_chunk_request is not None:
            self.upload_chunk_request.encode(writer, 15)

        if self.get_binary_info_request is not None:
            self.get_binary_info_request.encode(writer, 16)

        if self.download_chunk_request is not None:
            self.download_chunk_request.encode(writer, 17)

        if self.delete_downloaded_binary_request is not None:
            self.delete_downloaded_binary_request.encode(writer, 18)

        if number:
            writer.ldelim()

        return writer.finish()
