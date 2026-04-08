from __future__ import annotations

import asyncio
import json

from cachyframe_core.settings import get_settings
from cachyframe_data_sources.warframestat import WarframeStatClient
from cachyframe_ui import FeatureTab, OverlayWindow, StatusPanel
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from .backend_client import DesktopBackendClient


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings = get_settings()
        self._warframestat = WarframeStatClient()
        self._backend = DesktopBackendClient(self._settings.desktop.backend_url)
        self._refresh_task: asyncio.Task[None] | None = None
        self.setWindowTitle("CachyFrame")
        self.resize(1400, 900)

        shell = QWidget()
        layout = QVBoxLayout(shell)

        self.status_panel = StatusPanel()
        self.status_panel.refresh_button.clicked.connect(self.refresh_async)
        layout.addWidget(self.status_panel)

        self.tabs = QTabWidget()
        self.foundry_tab = FeatureTab(
            "Foundry",
            "Inventory-backed foundry and crafting tree surface.",
        )
        self.inventory_tab = FeatureTab(
            "Inventory",
            "Tradable inventory, sets, and listing helpers.",
        )
        self.mastery_tab = FeatureTab("Mastery Helper", "Mastery-oriented recommendations.")
        self.relic_tab = FeatureTab("Relic Planner", "Relic counts, EV, and overlay export state.")
        self.riven_tab = FeatureTab(
            "Riven Explorer",
            "Rivens, sniper subscriptions, and market signals.",
        )
        self.stats_tab = FeatureTab("Stats", "Stats, public links, and analytics surface.")
        for label, widget in (
            ("Foundry", self.foundry_tab),
            ("Inventory", self.inventory_tab),
            ("Mastery Helper", self.mastery_tab),
            ("Relic Planner", self.relic_tab),
            ("Rivens", self.riven_tab),
            ("Stats", self.stats_tab),
        ):
            self.tabs.addTab(widget, label)
        layout.addWidget(self.tabs, stretch=1)
        self.setCentralWidget(shell)

        self.overlay_windows = {
            "relic_rewards": OverlayWindow("Relic Rewards Overlay"),
            "relic_recommendation": OverlayWindow("Relic Recommendation Overlay"),
            "riven_chat": OverlayWindow("Riven Chat Overlay"),
            "riven_reroll": OverlayWindow("Riven Reroll Overlay"),
        }
        QTimer.singleShot(0, self.refresh_async)

    def refresh_async(self) -> None:
        if self._refresh_task is None or self._refresh_task.done():
            self._refresh_task = asyncio.create_task(self.refresh())

    async def refresh(self) -> None:
        try:
            health = await self._backend.get_health()
            dashboard = await self._backend.get_dashboard(self._settings.user_hash)
            foundry = await self._backend.get_foundry(self._settings.user_hash)
            inventory = await self._backend.get_inventory(
                self._settings.user_hash,
                tradable_only=True,
            )
            relics = await self._backend.get_relics(self._settings.user_hash)
        except Exception as exc:  # pragma: no cover - network/UI
            self.status_panel.set_backend_status("offline")
            self.status_panel.set_collector_status("idle")
            self.status_panel.set_proxy_status("unconfigured")
            self.stats_tab.set_text(f"Unable to fetch backend state:\n{exc}")
            try:
                worldstate = await self._warframestat.get_worldstate(self._settings.platform)
            except Exception:
                return
            summary = {
                "timestamp": worldstate.get("timestamp"),
                "fissures": len(worldstate.get("fissures", [])),
                "news": len(worldstate.get("news", [])),
                "events": len(worldstate.get("events", [])),
            }
            self.relic_tab.set_text(json.dumps(summary, indent=2))
            return
        self.status_panel.set_backend_status(health["status"])
        self.status_panel.set_collector_status("ready")
        proxy_status = f"{self._settings.proxy.host}:{self._settings.proxy.port}"
        self.status_panel.set_proxy_status(proxy_status)
        self.stats_tab.set_text(json.dumps(dashboard, indent=2))
        self.relic_tab.set_text(json.dumps(relics, indent=2))
        self.foundry_tab.set_text(json.dumps(foundry, indent=2))
        self.inventory_tab.set_text(json.dumps(inventory, indent=2))
        snapshot = dashboard.get("snapshot") or {}
        self.mastery_tab.set_text(
            json.dumps(
                {
                    "mastery_rank": snapshot.get("mastery_rank"),
                    "ready_to_build_count": snapshot.get("ready_to_build_count"),
                    "unmastered_owned_count": snapshot.get("unmastered_owned_count"),
                },
                indent=2,
            )
        )
        self.riven_tab.set_text(
            json.dumps(
                {
                    "analytics": dashboard.get("analytics", {}),
                    "worldstate": dashboard.get("worldstate", {}),
                },
                indent=2,
            )
        )
