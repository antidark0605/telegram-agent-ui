from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True)
class Destination:
    chat_id: int | str
    message_thread_id: int | None = None

    def __post_init__(self):
        if type(self.chat_id) not in (int, str) or not str(self.chat_id).strip():
            raise ValueError('chat_id must be a nonempty string or integer')
        if self.message_thread_id is not None and (
            type(self.message_thread_id) is not int or self.message_thread_id <= 0
        ):
            raise ValueError('message_thread_id must be a positive integer or None')


@dataclass(frozen=True)
class Document:
    """An already authorized, immutable staged file, opened by its application.

    The application owns the stream, its position, lifetime and accurate byte
    count. Delivery does not seek, read, close, delete, or reopen it itself.
    """
    filename: str
    stream: BinaryIO
    size_bytes: int
    caption: str | None = None

    def __post_init__(self):
        if not isinstance(self.filename, str) or not self.filename or self.filename in ('.', '..'):
            raise ValueError('filename must be a nonempty basename')
        if any(c in self.filename for c in '/\\') or any(ord(c) < 32 or ord(c) == 127 for c in self.filename):
            raise ValueError('filename must not contain paths or control characters')
        if type(self.size_bytes) is not int or self.size_bytes <= 0:
            raise ValueError('size_bytes must be a positive byte count')
        if not callable(getattr(self.stream, 'read', None)):
            raise TypeError('stream must provide binary read')
        if self.caption is not None:
            if not isinstance(self.caption, str):
                raise TypeError('caption must be text or None')
            # A conservative UTF-16 bound; no parse_mode/entities are supplied.
            if len(self.caption.encode('utf-16-le')) // 2 > 1024:
                raise ValueError('caption exceeds the 1024 UTF-16 unit limit')


@dataclass(frozen=True)
class Receipt:
    """Acknowledgement returned by a provider adapter after a successful send."""
    destination: Destination
    message_id: int | str

    def __post_init__(self):
        if type(self.message_id) not in (int, str) or not str(self.message_id).strip():
            raise ValueError('message_id must be a nonempty string or integer')


def _arguments(destination: Destination, document: Document, max_bytes: int) -> dict:
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError('max_bytes must be a positive byte count')
    if document.size_bytes > max_bytes:
        raise ValueError('document exceeds configured byte limit')
    kwargs = {'chat_id': destination.chat_id, 'document': document.stream, 'filename': document.filename}
    if destination.message_thread_id is not None:
        kwargs['message_thread_id'] = destination.message_thread_id
    if document.caption is not None:
        kwargs['caption'] = document.caption
    return kwargs


def _receipt(value: Receipt, destination: Destination) -> Receipt:
    if not isinstance(value, Receipt) or value.destination != destination:
        # The provider may already have sent the file. This is NOT a retry signal.
        raise ValueError('provider must return a receipt for the exact requested destination')
    return value


def send_document(
    sender: Callable[..., Receipt], destination: Destination, document: Document,
    *, max_bytes: int = 50_000_000,
) -> Receipt:
    """Call an application provider once; propagate all errors without retry."""
    return _receipt(sender(**_arguments(destination, document, max_bytes)), destination)


async def send_document_async(
    sender: Callable[..., Awaitable[Receipt]], destination: Destination, document: Document,
    *, max_bytes: int = 50_000_000,
) -> Receipt:
    """Async equivalent: retain caller's topic and stream throughout the await."""
    return _receipt(await sender(**_arguments(destination, document, max_bytes)), destination)
