"""Jalankan beberapa operasi Atlas dalam satu transaksi MongoDB."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

T = TypeVar("T")


async def jalankan_dalam_transaksi(
    db: AsyncDatabase,
    callback: Callable[[AsyncClientSession], Awaitable[T]],
) -> T:
    """Eksekusi callback di dalam transaksi; rollback otomatis jika error."""
    klien = db.client
    async with klien.start_session() as sesi:
        async with await sesi.start_transaction():
            return await callback(sesi)
