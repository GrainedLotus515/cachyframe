from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from cachyframe_core.compat import PlayerStatsData
from cachyframe_core.models import (
    AccountSnapshot,
    CaptureEvent,
    PublicLink,
    PublicLinkParts,
    SniperSubscription,
    StatsPoint,
    TradeRecord,
)
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .database import session_scope
from .models import (
    AccountSnapshotORM,
    Base,
    CaptureEventORM,
    DiagnosticsUploadORM,
    PublicLinkORM,
    SniperSubscriptionORM,
    StatsPointORM,
    TradeRecordORM,
    UserIdentityORM,
)


class StorageRepository:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        diagnostics_dir: Path,
    ) -> None:
        self._session_factory = session_factory
        self._diagnostics_dir = diagnostics_dir
        self._diagnostics_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        engine = self._session_factory.kw["bind"]
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def upsert_snapshot(self, snapshot: AccountSnapshot) -> AccountSnapshot:
        async with session_scope(self._session_factory) as session:
            identity = await session.get(UserIdentityORM, snapshot.user_hash)
            if identity is None:
                identity = UserIdentityORM(
                    user_hash=snapshot.user_hash,
                    secret_token=snapshot.secret_token or secrets.token_urlsafe(24),
                    username=snapshot.username,
                )
                session.add(identity)
            else:
                if snapshot.secret_token:
                    identity.secret_token = snapshot.secret_token
                if snapshot.username:
                    identity.username = snapshot.username

            row = AccountSnapshotORM(
                id=str(uuid4()),
                user_hash=snapshot.user_hash,
                captured_at=snapshot.captured_at,
                payload=snapshot.model_dump(mode="json"),
            )
            session.add(row)
        return snapshot

    async def get_current_snapshot(self, user_hash: str) -> AccountSnapshot | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AccountSnapshotORM)
                .where(AccountSnapshotORM.user_hash == user_hash)
                .order_by(AccountSnapshotORM.captured_at.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            return None if row is None else AccountSnapshot.model_validate(row.payload)

    async def add_stats_points(self, user_hash: str, points: list[StatsPoint]) -> int:
        async with session_scope(self._session_factory) as session:
            for point in points:
                session.add(
                    StatsPointORM(
                        user_hash=user_hash,
                        ts=point.ts,
                        payload=point.model_dump(mode="json"),
                    )
                )
        return len(points)

    async def add_trades(self, user_hash: str, trades: list[TradeRecord]) -> int:
        async with session_scope(self._session_factory) as session:
            for trade in trades:
                session.add(
                    TradeRecordORM(
                        user_hash=user_hash,
                        ts=trade.ts,
                        payload=trade.model_dump(mode="json"),
                    )
                )
        return len(trades)

    async def add_capture_events(self, user_hash: str, events: list[CaptureEvent]) -> int:
        async with session_scope(self._session_factory) as session:
            for event in events:
                session.add(
                    CaptureEventORM(
                        id=event.event_id,
                        user_hash=user_hash,
                        kind=event.kind,
                        occurred_at=event.occurred_at,
                        payload=event.model_dump(mode="json"),
                    )
                )
        return len(events)

    async def list_capture_events(self, user_hash: str, limit: int = 50) -> list[dict]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(CaptureEventORM)
                .where(CaptureEventORM.user_hash == user_hash)
                .order_by(CaptureEventORM.occurred_at.desc())
                .limit(limit)
            )
            return [row.payload for row in result.scalars()]

    async def _list_stats_points(self, session: AsyncSession, user_hash: str) -> list[StatsPoint]:
        result = await session.execute(
            select(StatsPointORM)
            .where(StatsPointORM.user_hash == user_hash)
            .order_by(StatsPointORM.ts)
        )
        return [StatsPoint.model_validate(row.payload) for row in result.scalars()]

    async def _list_trades(self, session: AsyncSession, user_hash: str) -> list[TradeRecord]:
        result = await session.execute(
            select(TradeRecordORM)
            .where(TradeRecordORM.user_hash == user_hash)
            .order_by(TradeRecordORM.ts)
        )
        return [TradeRecord.model_validate(row.payload) for row in result.scalars()]

    async def get_player_stats_data(
        self,
        user_hash: str,
        secret_token: str | None = None,
    ) -> PlayerStatsData | None:
        async with self._session_factory() as session:
            identity = await session.get(UserIdentityORM, user_hash)
            if identity is None:
                return None
            if secret_token is not None and identity.secret_token != secret_token:
                return None
            stats = await self._list_stats_points(session, user_hash)
            trades = await self._list_trades(session, user_hash)
            return PlayerStatsData.from_domain(
                user_hash=user_hash,
                stats=stats,
                trades=trades,
            )

    async def create_public_link(
        self,
        user_hash: str,
        parts: int,
        username_when_public: str | None = None,
        ttl_days: int = 365,
    ) -> PublicLink:
        public_link = PublicLink(
            token=secrets.token_urlsafe(24),
            user_hash=user_hash,
            parts=parts,
            username_when_public=username_when_public,
            expires_at=datetime.now(UTC) + timedelta(days=ttl_days),
        )
        async with session_scope(self._session_factory) as session:
            session.add(
                PublicLinkORM(
                    id=public_link.id,
                    token=public_link.token,
                    user_hash=public_link.user_hash,
                    parts=public_link.parts,
                    username_when_public=public_link.username_when_public,
                    created_at=public_link.created_at,
                    expires_at=public_link.expires_at,
                )
            )
        return public_link

    async def list_public_links(self, user_hash: str) -> list[PublicLink]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PublicLinkORM)
                .where(PublicLinkORM.user_hash == user_hash)
                .order_by(PublicLinkORM.created_at.desc())
            )
            return [
                PublicLink(
                    id=row.id,
                    token=row.token,
                    user_hash=row.user_hash,
                    parts=row.parts,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    revoked_at=row.revoked_at,
                    username_when_public=row.username_when_public,
                )
                for row in result.scalars()
            ]

    async def revoke_public_link(self, user_hash: str, link_id: str) -> bool:
        async with session_scope(self._session_factory) as session:
            row = await session.get(PublicLinkORM, link_id)
            if row is None or row.user_hash != user_hash:
                return False
            row.revoked_at = datetime.now(UTC)
        return True

    async def get_public_stats(self, token: str) -> PlayerStatsData | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PublicLinkORM).where(
                    PublicLinkORM.token == token,
                    PublicLinkORM.revoked_at.is_(None),
                    PublicLinkORM.expires_at > datetime.now(UTC),
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            stats = await self._list_stats_points(session, row.user_hash)
            trades = await self._list_trades(session, row.user_hash)
            stats_mask = int(
                PublicLinkParts.ACCOUNT_DATA
                | PublicLinkParts.PLATINUM
                | PublicLinkParts.DUCATS
                | PublicLinkParts.ENDO
                | PublicLinkParts.CREDITS
                | PublicLinkParts.AYA
            )
            return PlayerStatsData.from_domain(
                user_hash=row.user_hash,
                stats=stats if row.parts & stats_mask else [],
                trades=trades if row.parts & int(PublicLinkParts.TRADES) else [],
                public_parts=row.parts,
                username_when_public=row.username_when_public,
            )

    async def create_sniper_subscription(
        self,
        user_hash: str,
        subscription: SniperSubscription,
    ) -> SniperSubscription:
        async with session_scope(self._session_factory) as session:
            session.add(
                SniperSubscriptionORM(
                    id=subscription.id,
                    user_hash=user_hash,
                    payload=subscription.model_dump(mode="json"),
                )
            )
        return subscription

    async def list_sniper_subscriptions(self, user_hash: str) -> list[SniperSubscription]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(SniperSubscriptionORM).where(SniperSubscriptionORM.user_hash == user_hash)
            )
            return [SniperSubscription.model_validate(row.payload) for row in result.scalars()]

    async def delete_sniper_subscription(self, user_hash: str, subscription_id: str) -> bool:
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                delete(SniperSubscriptionORM).where(
                    SniperSubscriptionORM.user_hash == user_hash,
                    SniperSubscriptionORM.id == subscription_id,
                )
            )
        return result.rowcount > 0

    async def save_diagnostics(
        self,
        user_hash: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> str:
        upload_id = str(uuid4())
        stored_path = self._diagnostics_dir / f"{upload_id}-{filename}"
        stored_path.write_bytes(content)
        async with session_scope(self._session_factory) as session:
            session.add(
                DiagnosticsUploadORM(
                    id=upload_id,
                    user_hash=user_hash,
                    filename=filename,
                    content_type=content_type,
                    stored_path=str(stored_path),
                )
            )
        return upload_id

    async def analytics_overview(self, user_hash: str) -> dict[str, int | float]:
        async with self._session_factory() as session:
            trade_count = await session.scalar(
                select(func.count())
                .select_from(TradeRecordORM)
                .where(TradeRecordORM.user_hash == user_hash)
            )
            point_count = await session.scalar(
                select(func.count())
                .select_from(StatsPointORM)
                .where(StatsPointORM.user_hash == user_hash)
            )
            latest_snapshot = await self.get_current_snapshot(user_hash)
            total_items = (
                sum(item.quantity for item in latest_snapshot.items)
                if latest_snapshot
                else 0
            )
            total_relics = (
                sum(relic.quantity for relic in latest_snapshot.relics)
                if latest_snapshot
                else 0
            )
            return {
                "trade_count": int(trade_count or 0),
                "stats_point_count": int(point_count or 0),
                "total_items": total_items,
                "total_relics": total_relics,
            }

    async def analytics_for_item(self, user_hash: str, item_id: str) -> dict[str, int]:
        snapshot = await self.get_current_snapshot(user_hash)
        if snapshot is None:
            return {"owned": 0, "trades": 0}
        owned = sum(item.quantity for item in snapshot.items if item.item_id == item_id)
        async with self._session_factory() as session:
            trades = await self._list_trades(session, user_hash)
        trade_hits = 0
        for trade in trades:
            names = [item.name for item in trade.tx] + [item.name for item in trade.rx]
            if item_id in names:
                trade_hits += 1
        return {"owned": owned, "trades": trade_hits}
