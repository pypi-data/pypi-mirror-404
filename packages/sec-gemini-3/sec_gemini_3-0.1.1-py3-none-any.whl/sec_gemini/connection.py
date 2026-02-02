import grpc
from grpc import aio
import uuid
import asyncio
from typing import Optional, Dict, Any, AsyncIterator, Callable, Awaitable
from . import api_pb2, api_pb2_grpc
import logging

logger = logging.getLogger("secgemini")


class RpcClient:
    def __init__(self, host: str):
        self.host = host
        self.channel: Optional[aio.Channel] = None
        self.stub: Optional[api_pb2_grpc.ApiHubStub] = None
        self.is_running = False

        # Queue for outgoing messages to the server
        self.request_queue: asyncio.Queue[Optional[api_pb2.ClientMessage]] = (
            asyncio.Queue()
        )

        # Pending requests waiting for a response (req_id -> Future)
        self._pending_requests: Dict[str, asyncio.Future] = {}

        # Streaming queues for multi-response requests (req_id -> Queue)
        self._streaming_queues: Dict[str, asyncio.Queue] = {}

        # Callbacks for incoming messages (e.g. session updates)
        # We can have a list of observers or a specific router.
        # For now, let's allow a single primary handler or a list.
        self._message_handlers: list[
            Callable[[api_pb2.ServerMessage], Awaitable[None]]
        ] = []

        self._listener_task: Optional[asyncio.Task] = None

    async def start(self):
        """Connect to the server."""
        if (
            self.host.startswith("localhost")
            or self.host.startswith("127.0.0.1")
            or self.host.startswith("[::]")
        ):
            self.channel = aio.insecure_channel(self.host)
        else:
            self.channel = aio.secure_channel(self.host, grpc.ssl_channel_credentials())

        self.stub = api_pb2_grpc.ApiHubStub(self.channel)
        self.is_running = True
        self._listener_task = asyncio.create_task(self._listener_loop())
        logger.info(f"Connected to {self.host}")

    async def close(self):
        """Close connection."""
        self.is_running = False
        await self.request_queue.put(None)  # Signal generator to stop
        if self._listener_task:
            try:
                await asyncio.wait_for(self._listener_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                if not self._listener_task.done():
                    self._listener_task.cancel()

        if self.channel:
            await self.channel.close()

    def add_message_handler(
        self, handler: Callable[[api_pb2.ServerMessage], Awaitable[None]]
    ):
        self._message_handlers.append(handler)

    def register_streaming_queue(self, req_id: str, queue: asyncio.Queue):
        self._streaming_queues[req_id] = queue

    def unregister_streaming_queue(self, req_id: str):
        self._streaming_queues.pop(req_id, None)

    async def send_request(
        self,
        payload_type: str,
        payload: Any,
        wait_for_response: bool = False,
        session_id: Optional[str] = None,
        req_id: Optional[str] = None,
    ) -> Optional[api_pb2.ServerMessage]:
        if not req_id:
            req_id = str(uuid.uuid4())

        kwargs = {payload_type: payload}
        msg = api_pb2.ClientMessage(req_id=req_id, session_id=session_id, **kwargs)

        fut = None
        if wait_for_response:
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            self._pending_requests[req_id] = fut

        await self.request_queue.put(msg)

        if wait_for_response and fut:
            try:
                response = await asyncio.wait_for(fut, timeout=10.0)
                return response
            finally:
                self._pending_requests.pop(req_id, None)
        return None

    async def _request_generator(self) -> AsyncIterator[api_pb2.ClientMessage]:
        while self.is_running:
            item = await self.request_queue.get()
            if item is None:
                break
            yield item

    async def _listener_loop(self):
        try:
            if not self.stub:
                raise RuntimeError("Stub not initialized")

            responses = self.stub.Connect(
                self._request_generator(), wait_for_ready=True
            )

            async for msg in responses:
                await self._dispatch_message(msg)

        except aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                logger.debug("gRPC connection cancelled")
            else:
                logger.error(f"gRPC connection error: {e}")
        except Exception as e:
            logger.error(f"Listener loop error: {e}")
        finally:
            self.is_running = False
            logger.debug("Disconnected")

    async def _dispatch_message(self, msg: api_pb2.ServerMessage):
        if msg is None:
            return
        # 1. Resolve pending requests
        if msg.req_id and msg.req_id in self._pending_requests:
            fut = self._pending_requests[msg.req_id]
            if not fut.done():
                fut.set_result(msg)
            return

        # 2. Dispatch to streaming queues
        if msg.req_id and msg.req_id in self._streaming_queues:
            await self._streaming_queues[msg.req_id].put(msg)
            # We don't return here because maybe we also want to notify global handlers?
            # But usually if it's a specific request response stream, we might want to keep it exclusive.
            # Client.py logic:
            # if msg.req_id in self._streaming_queues: await ...
            # AND THEN it continues to "Handle Session State Changes"
            # So pass through is correct.
            pass

        # 3. Dispatch to handlers
        for handler in self._message_handlers:
            try:
                await handler(msg)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
