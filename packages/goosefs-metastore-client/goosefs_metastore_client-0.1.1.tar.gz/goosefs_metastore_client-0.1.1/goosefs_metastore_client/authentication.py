"""GooseFS SASL authentication implementation."""
import uuid
import logging
import threading
import queue
from typing import Optional

import grpc
from grpc_files.sasl_server_pb2 import (
    SaslMessage,
    SaslMessageType,
    ChannelAuthenticationScheme,
)
from grpc_files.sasl_server_pb2_grpc import SaslAuthenticationServiceStub


logger = logging.getLogger(__name__)


class ChannelAuthenticator:
    """Handles SASL authentication for GooseFS channels."""

    def __init__(
        self,
        channel: grpc.Channel,
        channel_id: uuid.UUID,
        username: Optional[str] = None,
        impersonation_user: Optional[str] = None,
    ):
        """
        Initialize the authenticator.

        :param channel: gRPC channel to authenticate
        :param channel_id: Unique UUID for this channel
        :param username: Username for authentication (defaults to OS user)
        :param impersonation_user: Optional user to impersonate
        """
        self.channel = channel
        self.channel_id = channel_id
        self.username = username or self._get_os_username()
        self.impersonation_user = impersonation_user or ""
        self.stub = SaslAuthenticationServiceStub(channel)

    @staticmethod
    def _get_os_username() -> str:
        """Get the current OS username."""
        import getpass
        return getpass.getuser()

    def _create_plain_sasl_payload(self) -> bytes:
        """
        Create PLAIN SASL mechanism payload.

        Format: authorizationId\0authenticationId\0password
        - authorizationId: impersonation user (empty for no impersonation)
        - authenticationId: actual username
        - password: placeholder password (required by PlainSaslServer, not validated in SIMPLE mode)
        """
        authorization_id = self.impersonation_user
        authentication_id = self.username
        password = "dummy"

        payload = f"{authorization_id}\x00{authentication_id}\x00{password}"
        return payload.encode("utf-8")

    def authenticate(self) -> None:
        """
        Perform SASL authentication with the server.
        
        Note: This keeps the authentication stream open (long poll) after successful
        authentication, similar to the Java client implementation. The stream should
        only be closed when the channel is closed.

        Raises:
            grpc.RpcError: If authentication fails
        """
        logger.debug(
            f"Starting SASL authentication for channel {self.channel_id} "
            f"with username '{self.username}'"
        )

        authenticated_event = threading.Event()
        auth_exception = [None]
        
        # Create a queue to manage the request stream
        request_queue = queue.Queue()
        
        def request_iterator():
            """Generator that yields messages from the queue."""
            while True:
                msg = request_queue.get()
                if msg is None:  # None signals end of stream
                    break
                yield msg

        class AuthResponseHandler:
            def __init__(self, request_iterator, channel_id):
                self.request_iterator = request_iterator
                self.channel_id = channel_id
                
            def handle_responses(self):
                try:
                    for response in self.request_iterator:
                        logger.debug(f"Received auth response: {response.messageType}")
                        if response.messageType == SaslMessageType.SUCCESS:
                            logger.info(
                                f"Authentication successful for channel {self.channel_id}"
                            )
                            authenticated_event.set()
                            # Keep the stream open - do not return here
                            # The stream will be closed when the channel is closed
                        elif response.messageType == SaslMessageType.CHALLENGE:
                            auth_exception[0] = Exception(
                                "Unexpected CHALLENGE from server during authentication"
                            )
                            authenticated_event.set()
                            return
                    
                    # Stream closed by server without SUCCESS
                    if not authenticated_event.is_set():
                        auth_exception[0] = Exception(
                            "Authentication stream ended without SUCCESS"
                        )
                        authenticated_event.set()
                        
                except Exception as e:
                    # Ignore CANCELLED error - it's expected when connection closes
                    if hasattr(e, 'code') and hasattr(e.code, '__call__'):
                        import grpc
                        if e.code() != grpc.StatusCode.CANCELLED:
                            logger.error(f"Error in authentication response handler: {e}")
                            auth_exception[0] = e
                    else:
                        logger.error(f"Error in authentication response handler: {e}")
                        auth_exception[0] = e
                    authenticated_event.set()

        try:
            initial_message = SaslMessage(
                messageType=SaslMessageType.CHALLENGE,
                authenticationScheme=ChannelAuthenticationScheme.SIMPLE,
                clientId=str(self.channel_id),
                channelRef=f"channel-{self.channel_id}",
                message=self._create_plain_sasl_payload(),
            )

            # Start bidirectional stream with a generator that can stay open
            response_iterator = self.stub.authenticate(request_iterator())
            
            # Send initial message
            request_queue.put(initial_message)
            
            # Handle responses in background thread to keep stream alive
            handler = AuthResponseHandler(response_iterator, self.channel_id)
            response_thread = threading.Thread(
                target=handler.handle_responses,
                daemon=True,
                name=f"auth-{self.channel_id}"
            )
            response_thread.start()

            # Wait for authentication to complete
            if not authenticated_event.wait(timeout=30):
                raise Exception("Authentication timed out")

            if auth_exception[0]:
                raise auth_exception[0]

            logger.info(
                f"Authentication established for channel {self.channel_id}, "
                "stream remains open"
            )
            
            # Do NOT close the stream here - keep it alive for the connection lifetime

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            # Close the stream on error
            request_queue.put(None)
            raise


class ChannelIdInjector(grpc.UnaryUnaryClientInterceptor, grpc.UnaryStreamClientInterceptor):
    """gRPC interceptor that injects Channel ID into request metadata."""

    CHANNEL_ID_KEY = "channel-id"

    def __init__(self, channel_id: uuid.UUID):
        """
        Initialize the interceptor.

        :param channel_id: UUID to inject into metadata
        """
        self.channel_id = str(channel_id)

    def _add_channel_id(self, client_call_details):
        """Add channel ID to metadata."""
        metadata = []
        if client_call_details.metadata is not None:
            metadata = list(client_call_details.metadata)
        metadata.append((self.CHANNEL_ID_KEY, self.channel_id))

        client_call_details = grpc._interceptor._ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            metadata,
            client_call_details.credentials,
            client_call_details.wait_for_ready,
            client_call_details.compression,
        )
        return client_call_details

    def intercept_unary_unary(self, continuation, client_call_details, request):
        """Intercept unary-unary calls."""
        client_call_details = self._add_channel_id(client_call_details)
        return continuation(client_call_details, request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        """Intercept unary-stream calls."""
        client_call_details = self._add_channel_id(client_call_details)
        return continuation(client_call_details, request)
