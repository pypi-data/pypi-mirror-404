# stream_fixture.py
"""
Record live Solana program logs, replay via local WS server.

Usage:
    # Record 50 events from mainnet
    python stream_fixture.py record --count 50 --out fixtures/pump_fun.jsonl
    
    # Serve those events on ws://localhost:8765
    python stream_fixture.py serve --fixture fixtures/pump_fun.jsonl --port 8765
"""

import asyncio
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Protocol
from queue import Queue
from threading import Thread

import websockets
from websockets.server import serve as ws_serve


# =============================================================================
# SCHEMA (schemas over ad-hoc objects)
# =============================================================================

@dataclass(frozen=True, slots=True)
class ProgramLogEvent:
    signature: str
    slot: int
    program_id: str
    logs_b64: list[str]
    captured_at: str  # ISO8601

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "ProgramLogEvent":
        d = json.loads(raw)
        return cls(**d)


@dataclass(frozen=True, slots=True)
class SolanaLogsSubscription:
    program_id: str
    commitment: str = "confirmed"

    def to_rpc_params(self) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {"mentions": [self.program_id]},
                {"commitment": self.commitment}
            ]
        }


# =============================================================================
# ENV CONFIG (explicit environment wiring over smart defaults)
# =============================================================================

@dataclass(frozen=True, slots=True)
class RecordConfig:
    ws_url: str
    program_id: str
    output_path: Path
    max_events: int
    commitment: str = "confirmed"

    @classmethod
    def from_env(cls, output: str, count: int) -> "RecordConfig":
        return cls(
            ws_url=os.environ.get("WS_URL", "wss://api.mainnet-beta.solana.com"),
            program_id=os.environ.get(
                "PROGRAM_ID",
                "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
            ),
            output_path=Path(output),
            max_events=count,
        )


@dataclass(frozen=True, slots=True)
class ServeConfig:
    fixture_path: Path
    host: str
    port: int
    loop: bool  # restart from beginning when exhausted

    @classmethod
    def from_args(cls, fixture: str, port: int, loop: bool = True) -> "ServeConfig":
        return cls(
            fixture_path=Path(fixture),
            host="0.0.0.0",
            port=port,
            loop=loop,
        )


# =============================================================================
# RECORDER (queue-backed capture)
# =============================================================================

class EventRecorder:
    def __init__(self, config: RecordConfig):
        self._config = config
        self._queue: asyncio.Queue[ProgramLogEvent] = asyncio.Queue()
        self._captured = 0

    async def _subscribe(self, ws) -> None:
        sub = SolanaLogsSubscription(
            program_id=self._config.program_id,
            commitment=self._config.commitment,
        )
        await ws.send(json.dumps(sub.to_rpc_params()))
        ack = await ws.recv()
        print(f"Subscription ack: {ack}")

    def _parse_notification(self, raw: str) -> ProgramLogEvent | None:
        msg = json.loads(raw)
        if msg.get("method") != "logsNotification":
            return None

        value = msg["params"]["result"]["value"]
        return ProgramLogEvent(
            signature=value["signature"],
            slot=msg["params"]["result"]["context"]["slot"],
            program_id=self._config.program_id,
            logs_b64=value["logs"],  # raw logs, your code handles b64
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

    async def _receiver(self, ws) -> None:
        async for raw in ws:
            event = self._parse_notification(raw)
            if event:
                await self._queue.put(event)

    async def _writer(self) -> None:
        self._config.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self._config.output_path.open("w") as f:
            while self._captured < self._config.max_events:
                event = await self._queue.get()
                f.write(event.to_json() + "\n")
                f.flush()
                self._captured += 1
                print(f"[{self._captured}/{self._config.max_events}] {event.signature}")

    async def run(self) -> None:
        async with websockets.connect(self._config.ws_url) as ws:
            await self._subscribe(ws)
            receiver_task = asyncio.create_task(self._receiver(ws))
            writer_task = asyncio.create_task(self._writer())

            # Wait for writer to finish (hit max_events)
            await writer_task
            receiver_task.cancel()

        print(f"Wrote {self._captured} events to {self._config.output_path}")


# =============================================================================
# REPLAY SERVER (deterministic playback)
# =============================================================================

class FixtureServer:
    def __init__(self, config: ServeConfig):
        self._config = config
        self._events: list[ProgramLogEvent] = []
        self._load_fixture()

    def _load_fixture(self) -> None:
        with self._config.fixture_path.open() as f:
            for line in f:
                if line.strip():
                    self._events.append(ProgramLogEvent.from_json(line))
        print(f"Loaded {len(self._events)} events from {self._config.fixture_path}")

    def _event_iterator(self) -> AsyncIterator[ProgramLogEvent]:
        async def gen():
            idx = 0
            while True:
                if idx >= len(self._events):
                    if self._config.loop:
                        idx = 0
                        print("Looping fixture from start")
                    else:
                        break
                yield self._events[idx]
                idx += 1
        return gen()

    async def _handle_client(self, websocket) -> None:
        print(f"Client connected: {websocket.remote_address}")

        # Wait for subscription request (mirror Solana protocol)
        sub_msg = await websocket.recv()
        print(f"Subscription request: {sub_msg}")

        # Send ack
        await websocket.send(json.dumps({"jsonrpc": "2.0", "result": 1, "id": 1}))

        # Stream events
        async for event in self._event_iterator():
            notification = {
                "jsonrpc": "2.0",
                "method": "logsNotification",
                "params": {
                    "result": {
                        "context": {"slot": event.slot},
                        "value": {
                            "signature": event.signature,
                            "logs": event.logs_b64,
                        }
                    },
                    "subscription": 1
                }
            }
            try:
                await websocket.send(json.dumps(notification))
                await asyncio.sleep(0.1)  # Throttle for realistic pacing
            except websockets.ConnectionClosed:
                print("Client disconnected")
                return

    async def run(self) -> None:
        async with ws_serve(self._handle_client, self._config.host, self._config.port):
            print(f"Fixture server running on ws://{self._config.host}:{self._config.port}")
            await asyncio.Future()  # run forever


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Solana log stream fixture tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_p = subparsers.add_parser("record", help="Record live events to fixture file")
    record_p.add_argument("--count", type=int, default=50, help="Number of events to capture")
    record_p.add_argument("--out", required=True, help="Output JSONL file path")

    serve_p = subparsers.add_parser("serve", help="Serve fixture via WebSocket")
    serve_p.add_argument("--fixture", required=True, help="Path to JSONL fixture file")
    serve_p.add_argument("--port", type=int, default=8765, help="WebSocket port")
    serve_p.add_argument("--no-loop", action="store_true", help="Stop after exhausting fixture")

    args = parser.parse_args()

    if args.command == "record":
        config = RecordConfig.from_env(args.out, args.count)
        asyncio.run(EventRecorder(config).run())

    elif args.command == "serve":
        config = ServeConfig.from_args(args.fixture, args.port, loop=not args.no_loop)
        asyncio.run(FixtureServer(config).run())


if __name__ == "__main__":
    main()
