"""Forward a LAN TCP port to the local mihomo mixed port.

Linux speaks HTTP or SOCKS5 to this process. Bytes are copied unchanged to
127.0.0.1:9674, which already accepts both protocols. No proxy protocol is
implemented here.

The listen port is 17890 so it does not collide with mihomo on 9674.
Linux must use this Windows machine's physical LAN address, not 127.0.0.1
and not the virtual-NIC address.
"""

from __future__ import annotations

import argparse
import asyncio


def split_host_port(value: str) -> tuple[str, int]:
    host, separator, port = value.rpartition(":")
    if not separator or not host or not port.isdigit():
        raise argparse.ArgumentTypeError(f"expected host:port, got {value}")
    return host, int(port)


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
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


async def handle(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    target_host: str,
    target_port: int,
) -> None:
    peer = client_writer.get_extra_info("peername")
    try:
        remote_reader, remote_writer = await asyncio.open_connection(target_host, target_port)
    except OSError as exc:
        print(f"reject {peer}: {exc}", flush=True)
        client_writer.close()
        return

    print(f"open {peer}", flush=True)
    upstream = asyncio.create_task(pipe(client_reader, remote_writer))
    downstream = asyncio.create_task(pipe(remote_reader, client_writer))
    done, pending = await asyncio.wait(
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
    print(f"close {peer}", flush=True)


async def serve(listen_host: str, listen_port: int, target_host: str, target_port: int) -> None:
    server = await asyncio.start_server(
        lambda reader, writer: handle(reader, writer, target_host, target_port),
        listen_host,
        listen_port,
    )
    bound = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    print(f"listening {bound} -> {target_host}:{target_port}", flush=True)
    async with server:
        await server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Relay LAN TCP to local mihomo")
    parser.add_argument("--listen", default="0.0.0.0:17890", type=split_host_port)
    parser.add_argument("--target", default="127.0.0.1:9674", type=split_host_port)
    args = parser.parse_args()
    listen_host, listen_port = args.listen
    target_host, target_port = args.target
    try:
        asyncio.run(serve(listen_host, listen_port, target_host, target_port))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
