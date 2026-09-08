from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Mapping
import json

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()

def digest(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()

@dataclass(frozen=True)
class RunManifest:
    git_revision: str
    python_version: str
    seed: int
    parameters: Mapping[str, Any]
    native_library_hash: str | None = None
    image_digest: str | None = None

    @property
    def run_id(self) -> str:
        return digest(asdict(self))

@dataclass(frozen=True)
class Event:
    sequence: int
    kind: str
    payload: Mapping[str, Any]
    parent_hash: str
    event_hash: str

@dataclass
class EventLedger:
    events: list[Event] = field(default_factory=list)

    @property
    def head_hash(self) -> str:
        return self.events[-1].event_hash if self.events else '0' * 64

    def append(self, kind: str, payload: Mapping[str, Any]) -> Event:
        body = {'sequence': len(self.events) + 1, 'kind': kind, 'payload': payload, 'parent_hash': self.head_hash}
        event = Event(event_hash=sha256(bytes.fromhex(self.head_hash) + canonical_bytes(body)).hexdigest(), **body)
        self.events.append(event)
        return event

    def verify(self) -> bool:
        parent = '0' * 64
        for sequence, event in enumerate(self.events, 1):
            if event.sequence != sequence or event.parent_hash != parent:
                return False
            body = {'sequence': event.sequence, 'kind': event.kind, 'payload': event.payload, 'parent_hash': parent}
            if sha256(bytes.fromhex(parent) + canonical_bytes(body)).hexdigest() != event.event_hash:
                return False
            parent = event.event_hash
        return True

@dataclass(frozen=True)
class ExecutionClosure:
    target: Mapping[str, str]
    payload: Mapping[str, Any]
    git_revision: str
    dependency_hashes: tuple[str, ...]
    run_id: str

    @property
    def closure_hash(self) -> str:
        return digest(asdict(self))
