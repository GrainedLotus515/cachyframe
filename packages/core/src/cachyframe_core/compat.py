from __future__ import annotations

import struct
from collections.abc import Iterable
from datetime import UTC, datetime

from pydantic import Field

from .models import (
    Model,
    OwnedRelic,
    PublicLinkParts,
    RelicRefinement,
    RelicTier,
    StatsPoint,
    TradeClassification,
    TradeRecord,
)


class PlayerStatsTradeItem(Model):
    name: str
    display_name: str | None = Field(default=None, alias="displayName")
    cnt: int = 1
    rank: int = 0


class PlayerStatsTrade(Model):
    ts: datetime
    tx: list[PlayerStatsTradeItem] = Field(default_factory=list)
    rx: list[PlayerStatsTradeItem] = Field(default_factory=list)
    user: str | None = None
    type: TradeClassification = TradeClassification.TRADE
    total_plat: int | None = Field(default=None, alias="totalPlat")


class PlayerStatsData(Model):
    general_data_points: list[StatsPoint] = Field(
        default_factory=list,
        alias="generalDataPoints",
    )
    trades: list[PlayerStatsTrade] = Field(default_factory=list)
    last_update: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        alias="lastUpdate",
    )
    user_hash: str | None = Field(default=None, alias="userHash")
    public_parts: int = Field(default=int(PublicLinkParts.NONE), alias="publicParts")
    username_when_public: str | None = Field(
        default=None,
        alias="usernameWhenPublic",
    )

    @classmethod
    def from_domain(
        cls,
        user_hash: str,
        stats: list[StatsPoint],
        trades: list[TradeRecord],
        public_parts: int = int(PublicLinkParts.NONE),
        username_when_public: str | None = None,
    ) -> PlayerStatsData:
        converted_trades = [
            PlayerStatsTrade(
                ts=trade.ts,
                tx=[
                    PlayerStatsTradeItem(
                        name=item.name,
                        displayName=item.display_name,
                        cnt=item.quantity,
                        rank=item.rank,
                    )
                    for item in trade.tx
                ],
                rx=[
                    PlayerStatsTradeItem(
                        name=item.name,
                        displayName=item.display_name,
                        cnt=item.quantity,
                        rank=item.rank,
                    )
                    for item in trade.rx
                ],
                user=trade.user,
                type=trade.type,
                totalPlat=trade.total_plat,
            )
            for trade in trades
        ]
        last_update = max(
            [point.ts for point in stats] + [trade.ts for trade in trades],
            default=datetime.now(UTC),
        )
        return cls(
            generalDataPoints=stats,
            trades=converted_trades,
            lastUpdate=last_update,
            userHash=user_hash,
            publicParts=public_parts,
            usernameWhenPublic=username_when_public,
        )


def _relic_name_bytes(code: str) -> bytes:
    return code.encode("ascii", errors="ignore")[:3].ljust(3, b"\x00")


def encode_relic_inventory(relics: Iterable[OwnedRelic]) -> bytes:
    relic_list = list(relics)
    payload = bytearray()
    payload.extend(struct.pack("<I", len(relic_list)))
    for relic in relic_list:
        payload.extend(
            struct.pack(
                "<BB3sI",
                int(RelicTier(relic.tier)),
                int(RelicRefinement(relic.refinement)),
                _relic_name_bytes(relic.code),
                relic.quantity,
            )
        )
    return bytes(payload)
