"""Historique des generations — stockage SQLite local.

100 % local, aucune donnee ne quitte la machine.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class HistoryEntry:
    """Une entree dans l'historique."""

    id: int
    created_at: str  # ISO format
    template_id: str
    template_label: str
    tone: str
    context: str
    output: str
    output_chars: int
    elapsed_seconds: float


class HistoryDB:
    """Gestion de la base SQLite pour l'historique."""

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            db_path = Path(__file__).parent.parent / "boostia_history.db"
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Creer la table si elle n'existe pas."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    template_label TEXT NOT NULL,
                    tone TEXT NOT NULL,
                    context TEXT NOT NULL,
                    output TEXT NOT NULL,
                    output_chars INTEGER NOT NULL,
                    elapsed_seconds REAL NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_created_at ON history (created_at DESC)"
            )
            conn.commit()
        logger.info("history_db_initialized", path=str(self.db_path))

    def add_entry(
        self,
        template_id: str,
        template_label: str,
        tone: str,
        context: str,
        output: str,
        output_chars: int,
        elapsed_seconds: float,
    ) -> int:
        """Ajoute une entree et retourne son ID."""
        created_at = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO history 
                (created_at, template_id, template_label, tone, context, output, output_chars, elapsed_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (created_at, template_id, template_label, tone, context, output, output_chars, elapsed_seconds),
            )
            conn.commit()
            entry_id = cursor.lastrowid
        logger.info(
            "history_entry_added",
            entry_id=entry_id,
            template_id=template_id,
            output_chars=output_chars,
        )
        return entry_id

    def get_all(self, limit: int = 50) -> list[HistoryEntry]:
        """Recupere les N dernieres entrees (plus recentes en premier)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, created_at, template_id, template_label, tone, context, output, output_chars, elapsed_seconds "
                "FROM history ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [HistoryEntry(*row) for row in cursor.fetchall()]

    def get_by_id(self, entry_id: int) -> HistoryEntry | None:
        """Recupere une entree par son ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, created_at, template_id, template_label, tone, context, output, output_chars, elapsed_seconds "
                "FROM history WHERE id = ?",
                (entry_id,),
            )
            row = cursor.fetchone()
            return HistoryEntry(*row) if row else None

    def delete_entry(self, entry_id: int) -> bool:
        """Supprime une entree. Retourne True si supprimee, False si inexistante."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
        if deleted:
            logger.info("history_entry_deleted", entry_id=entry_id)
        return deleted

    def clear_all(self) -> int:
        """Supprime toutes les entrees. Retourne le nombre supprime."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM history")
            conn.commit()
            count = cursor.rowcount
        logger.info("history_cleared", entries_deleted=count)
        return count

    def count(self) -> int:
        """Retourne le nombre total d'entrees."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM history")
            return cursor.fetchone()[0]
