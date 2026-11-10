"""LAN TCP relay used by the gateway UI.

Bytes are copied unchanged to the local VPN/proxy port (default 127.0.0.1:9674).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Optional


LogFn = Callable[[str], None]


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError, OSError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except OSError:
            pass


async def _handle(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    target_host: str,
    target_port: int,
    log: LogFn,
) -> None:
    peer = client_writer.get_extra_info("peername")
    try:
        remote_reader, remote_writer = await asyncio.open_connection(target_host, target_port)
    except OSError as exc:
        log(f"reject {peer}: {exc}")
        client_writer.close()
        return

    log(f"open {peer}")
    upstream = asyncio.create_task(_pipe(client_reader, remote_writer))
    downstream = asyncio.create_task(_pipe(remote_reader, client_writer))
    _done, pending = await asyncio.wait(
        {upstream, downstream},
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    for writer in (client_writer, remote_writer):
        try:
            writer.close()
        except OSError:
            pass
    log(f"close {peer}")


class RelayServer:
    def __init__(
        self,
        listen_host: str = "0.0.0.0",
        listen_port: int = 17890,
        target_host: str = "127.0.0.1",
        target_port: int = 9674,
        log: Optional[LogFn] = None,
    ) -> None:
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self._log = log or (lambda _msg: None)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server: Optional[asyncio.AbstractServer] = None
        self._task: Optional[asyncio.Task] = None

    @property
    def running(self) -> bool:
        return self._server is not None

    def start_blocking(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except asyncio.CancelledError:
            pass
        finally:
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()
            if pending:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self._loop.close()
            self._loop = None
            self._server = None

    def stop(self) -> None:
        loop = self._loop
        if loop is None:
            return

        def _close() -> None:
            if self._server is not None:
                self._server.close()
            if self._task is not None:
                self._task.cancel()

        loop.call_soon_threadsafe(_close)

    async def _serve(self) -> None:
        self._server = await asyncio.start_server(
            lambda reader, writer: _handle(
                reader,
                writer,
                self.target_host,
                self.target_port,
                self._log,
            ),
            self.listen_host,
            self.listen_port,
        )
        bound = ", ".join(str(sock.getsockname()) for sock in self._server.sockets or [])
        self._log(f"listening {bound} -> {self.target_host}:{self.target_port}")
        async with self._server:
            self._task = asyncio.create_task(self._server.serve_forever())
            try:
                await self._task
            except asyncio.CancelledError:
                self._log("relay stopped")
                raise
