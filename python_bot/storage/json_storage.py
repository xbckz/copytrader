"""
JSON Storage - Simple file-based storage for bot data
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class JSONStorage:
    """Simple JSON file storage"""

    def __init__(self, storage_dir: str = "data"):
        """Initialize JSON storage"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        # File paths
        self.sessions_file = self.storage_dir / "sessions.json"
        self.wallets_file = self.storage_dir / "wallets.json"
        self.positions_file = self.storage_dir / "positions.json"
        self.trades_file = self.storage_dir / "trades.json"
        self.balance_transactions_file = self.storage_dir / "balance_transactions.json"

        # Initialize files if they don't exist
        self._init_files()

        logger.info(f"JSON storage initialized at {self.storage_dir}")

    def _init_files(self):
        """Initialize storage files"""
        files = {
            self.sessions_file: [],
            self.wallets_file: [],
            self.positions_file: [],
            self.trades_file: [],
            self.balance_transactions_file: []
        }

        for file_path, default_data in files.items():
            if not file_path.exists():
                self._save_json(file_path, default_data)

    def _load_json(self, file_path: Path) -> Any:
        """Load JSON from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []

    def _save_json(self, file_path: Path, data: Any):
        """Save JSON to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")

    # ==================== Sessions ====================

    def save_session(self, session_data: Dict):
        """Save or update a session"""
        sessions = self._load_json(self.sessions_file)

        # Find and update or append
        found = False
        for i, s in enumerate(sessions):
            if s['session_id'] == session_data['session_id']:
                sessions[i] = session_data
                found = True
                break

        if not found:
            sessions.append(session_data)

        self._save_json(self.sessions_file, sessions)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        sessions = self._load_json(self.sessions_file)
        for s in sessions:
            if s['session_id'] == session_id:
                return s
        return None

    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions"""
        return self._load_json(self.sessions_file)

    def delete_session(self, session_id: str):
        """Delete a session"""
        sessions = self._load_json(self.sessions_file)
        sessions = [s for s in sessions if s['session_id'] != session_id]
        self._save_json(self.sessions_file, sessions)

    # ==================== Wallets ====================

    def save_wallet(self, wallet_data: Dict):
        """Save or update a wallet"""
        wallets = self._load_json(self.wallets_file)

        # Find and update or append
        found = False
        for i, w in enumerate(wallets):
            if w['address'] == wallet_data['address']:
                wallets[i] = wallet_data
                found = True
                break

        if not found:
            wallets.append(wallet_data)

        self._save_json(self.wallets_file, wallets)

    def get_wallet(self, address: str) -> Optional[Dict]:
        """Get wallet by address"""
        wallets = self._load_json(self.wallets_file)
        for w in wallets:
            if w['address'] == address:
                return w
        return None

    def get_all_wallets(self) -> List[Dict]:
        """Get all wallets"""
        return self._load_json(self.wallets_file)

    def delete_wallet(self, address: str):
        """Delete a wallet"""
        wallets = self._load_json(self.wallets_file)
        wallets = [w for w in wallets if w['address'] != address]
        self._save_json(self.wallets_file, wallets)

    # ==================== Positions ====================

    def save_position(self, position_data: Dict):
        """Save or update a position"""
        positions = self._load_json(self.positions_file)

        # Find and update or append
        found = False
        for i, p in enumerate(positions):
            if p['id'] == position_data['id']:
                positions[i] = position_data
                found = True
                break

        if not found:
            positions.append(position_data)

        self._save_json(self.positions_file, positions)

    def get_position(self, position_id: str) -> Optional[Dict]:
        """Get position by ID"""
        positions = self._load_json(self.positions_file)
        for p in positions:
            if p['id'] == position_id:
                return p
        return None

    def get_all_positions(self, session_id: str = None) -> List[Dict]:
        """Get all positions, optionally filtered by session"""
        positions = self._load_json(self.positions_file)
        if session_id:
            positions = [p for p in positions if p.get('session_id') == session_id]
        return positions

    # ==================== Trades ====================

    def save_trade(self, trade_data: Dict):
        """Save a trade"""
        trades = self._load_json(self.trades_file)
        trades.append(trade_data)
        self._save_json(self.trades_file, trades)

    def get_all_trades(self, session_id: str = None, limit: int = None) -> List[Dict]:
        """Get trades, optionally filtered by session and limited"""
        trades = self._load_json(self.trades_file)

        if session_id:
            trades = [t for t in trades if t.get('session_id') == session_id]

        # Sort by timestamp (newest first)
        trades.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        if limit:
            trades = trades[:limit]

        return trades

    # ==================== Balance Transactions ====================

    def save_balance_transaction(self, transaction_data: Dict):
        """Save a balance transaction"""
        transactions = self._load_json(self.balance_transactions_file)
        transactions.append(transaction_data)
        self._save_json(self.balance_transactions_file, transactions)

    def get_balance_transactions(
        self,
        session_id: str = None,
        limit: int = None
    ) -> List[Dict]:
        """Get balance transactions"""
        transactions = self._load_json(self.balance_transactions_file)

        if session_id:
            transactions = [t for t in transactions if t.get('session_id') == session_id]

        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        if limit:
            transactions = transactions[:limit]

        return transactions
