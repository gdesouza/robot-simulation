"""Bounded handoff to an isolated asyncio WebSocket thread; no Webots calls."""
import asyncio
import logging
import queue
import threading
from websockets.asyncio.server import serve

LOG = logging.getLogger(__name__)


def latest(q, item):
    try:
        q.put_nowait(item)
    except (queue.Full, asyncio.QueueFull):
        q.get_nowait()
        q.put_nowait(item)


class ScanServer:
    def __init__(self, host='127.0.0.1', port=8765):
        self.host, self.port = host, port
        self.inbox = queue.Queue(maxsize=2)
        self.clients = set()
        self.stopping = threading.Event()
        self.ready = threading.Event()
        self.error = None
        self.bound_port = None
        self.thread = threading.Thread(target=self._run, daemon=True,
                                       name='lidar-websocket')

    def start(self):
        self.thread.start()

    def publish(self, text):
        latest(self.inbox, text)

    def close(self):
        self.stopping.set()
        self.thread.join(timeout=2)

    def _run(self):
        try:
            asyncio.run(self._serve())
        except Exception as exc:
            self.error = exc
            LOG.exception('LiDAR stream unavailable; driving remains active')
        finally:
            self.ready.set()

    async def _client(self, socket):
        pending = asyncio.Queue(maxsize=1)
        self.clients.add(pending)
        async def send():
            while True:
                payload = await pending.get()
                try:
                    await asyncio.wait_for(socket.send(payload), timeout=0.5)
                except asyncio.TimeoutError:
                    await socket.close(code=1013, reason='Slow client; reconnect')
                    return
        sender = asyncio.create_task(send())
        closed = asyncio.create_task(socket.wait_closed())
        try:
            await asyncio.wait({sender, closed}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            self.clients.discard(pending)
            sender.cancel()
            closed.cancel()
            await asyncio.gather(sender, closed, return_exceptions=True)

    async def _serve(self):
        async with serve(self._client, self.host, self.port, compression=None,
                         max_queue=1, max_size=1024, write_limit=8192,
                         close_timeout=0.5) as server:
            self.bound_port = server.sockets[0].getsockname()[1]
            print(f'LiDAR WebSocket: ws://{self.host}:{self.bound_port}')
            self.ready.set()
            while not self.stopping.is_set():
                # Drain at most the bounded producer queue, once per loop tick.
                newest = None
                for _ in range(2):
                    try:
                        newest = self.inbox.get_nowait()
                    except queue.Empty:
                        break
                if newest is not None:
                    for pending in tuple(self.clients):
                        latest(pending, newest)
                await asyncio.sleep(0.005)
