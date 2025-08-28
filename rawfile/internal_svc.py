from internal import internal_pb2_grpc, internal_pb2
from utils.logs import logger, log_grpc_request
import utils.rawfile
from utils.remote import is_attached
from utils.lock import VolLock
from typing import Final
import grpc

SIGNATURE_METADATA: Final[str] = "x-signature"


class SignatureInterceptor(grpc.ServerInterceptor):
    def __init__(self, signature: str | None = None):
        self.signature = signature

        def __init__(self):
            def abort(ignored_request, context):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid signature")

            self._abort_handler = grpc.unary_unary_rpc_method_handler(abort)

    def intercept_service(self, continuation, handler_call_details):
        if self.signature:
            expected_metadata = (SIGNATURE_METADATA, self.signature)

            if expected_metadata in handler_call_details.invocation_metadata:
                return continuation(handler_call_details)

            else:
                logger.debug(
                    "SignatureInterceptor: Invalid signature",
                    metadata=handler_call_details.invocation_metadata,
                )
                return self._abort_handler
        else:
            return continuation(handler_call_details)


class InternalServicer(internal_pb2_grpc.InternalServicer):
    @log_grpc_request
    def ExpandRawFile(
        self, request: internal_pb2.ExpandRawFileRequest, context
    ) -> internal_pb2.ExpandRawFileResponse:
        with VolLock(request.volume_id):
            img_file = utils.rawfile.img_file(request.volume_id)
            size_inc = (
                request.new_size - utils.rawfile.metadata(request.volume_id)["size"]
            )
            if size_inc <= 0:
                return internal_pb2.ExpandRawFileResponse(
                    is_attached=is_attached(request.volume_id),
                    status=internal_pb2.ExpandRawFileStatus.OK,
                )

            if utils.rawfile.get_capacity() < size_inc:
                return internal_pb2.ExpandRawFileResponse(
                    is_attached=is_attached(request.volume_id),
                    status=internal_pb2.ExpandRawFileStatus.RESOURCE_EXHAUSTED,
                )
            if utils.rawfile.metadata(request.volume_id).get("thin_provision", False):
                utils.rawfile.truncate(img_file, request.new_size)
            else:
                utils.rawfile.fallocate(img_file, request.new_size)
            utils.rawfile.patch_metadata(
                request.volume_id,
                {"size": request.new_size},
            )
            return internal_pb2.ExpandRawFileResponse(
                is_attached=is_attached(request.volume_id),
                status=internal_pb2.ExpandRawFileStatus.OK,
            )
