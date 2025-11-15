"""
Watchlist Management System
Manage multiple watchlists, add/remove symbols, import/export
"""
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import csv
from pathlib import Path
from loguru import logger
from utils.cache import cache_manager


@dataclass
class Watchlist:
    """Watchlist model"""
    id: str
    name: str
    description: str
    symbols: List[str]
    created_at: datetime
    updated_at: datetime
    is_default: bool = False
    color: str = "#3b82f6"  # Default blue

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "symbols": self.symbols,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_default": self.is_default,
            "color": self.color,
        }


class WatchlistManager:
    """
    Complete Watchlist Management System

    Features:
    - Create/Update/Delete watchlists
    - Add/Remove symbols
    - Multiple watchlists support
    - Import/Export (JSON, CSV)
    - Predefined templates
    - Symbol validation
    - Auto-save to cache/database
    """

    def __init__(self, storage_path: str = "data/watchlists.json"):
        self.storage_path = Path(storage_path)
        self.watchlists: Dict[str, Watchlist] = {}
        self._load_watchlists()
        self._create_default_templates()

    def _load_watchlists(self):
        """Load watchlists from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for wl_data in data:
                    wl = Watchlist(
                        id=wl_data['id'],
                        name=wl_data['name'],
                        description=wl_data['description'],
                        symbols=wl_data['symbols'],
                        created_at=datetime.fromisoformat(wl_data['created_at']),
                        updated_at=datetime.fromisoformat(wl_data['updated_at']),
                        is_default=wl_data.get('is_default', False),
                        color=wl_data.get('color', '#3b82f6'),
                    )
                    self.watchlists[wl.id] = wl

                logger.info(f"Loaded {len(self.watchlists)} watchlists")
            except Exception as e:
                logger.error(f"Error loading watchlists: {e}")

    def _save_watchlists(self):
        """Save watchlists to storage"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = [wl.to_dict() for wl in self.watchlists.values()]

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Also cache in Redis for fast access
            cache_manager.set("watchlists:all", data, ttl=3600)

            logger.info(f"Saved {len(self.watchlists)} watchlists")
        except Exception as e:
            logger.error(f"Error saving watchlists: {e}")

    def create_watchlist(
        self,
        name: str,
        description: str = "",
        symbols: List[str] = None,
        color: str = "#3b82f6"
    ) -> Watchlist:
        """
        Create a new watchlist

        Args:
            name: Watchlist name
            description: Optional description
            symbols: Initial symbols (default: empty)
            color: Color for UI (hex code)

        Returns:
            Created Watchlist object
        """
        import uuid

        watchlist_id = str(uuid.uuid4())
        symbols = symbols or []

        # Validate and clean symbols
        symbols = [s.upper().strip() for s in symbols if s.strip()]

        watchlist = Watchlist(
            id=watchlist_id,
            name=name,
            description=description,
            symbols=symbols,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            color=color,
        )

        self.watchlists[watchlist_id] = watchlist
        self._save_watchlists()

        logger.info(f"Created watchlist: {name} with {len(symbols)} symbols")
        return watchlist

    def update_watchlist(
        self,
        watchlist_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        color: Optional[str] = None,
    ) -> Optional[Watchlist]:
        """Update existing watchlist"""
        if watchlist_id not in self.watchlists:
            logger.warning(f"Watchlist {watchlist_id} not found")
            return None

        watchlist = self.watchlists[watchlist_id]

        if name:
            watchlist.name = name
        if description is not None:
            watchlist.description = description
        if symbols is not None:
            watchlist.symbols = [s.upper().strip() for s in symbols if s.strip()]
        if color:
            watchlist.color = color

        watchlist.updated_at = datetime.now()
        self._save_watchlists()

        logger.info(f"Updated watchlist: {watchlist.name}")
        return watchlist

    def delete_watchlist(self, watchlist_id: str) -> bool:
        """Delete a watchlist"""
        if watchlist_id not in self.watchlists:
            return False

        watchlist = self.watchlists[watchlist_id]

        if watchlist.is_default:
            logger.warning(f"Cannot delete default watchlist: {watchlist.name}")
            return False

        del self.watchlists[watchlist_id]
        self._save_watchlists()

        logger.info(f"Deleted watchlist: {watchlist.name}")
        return True

    def add_symbol(self, watchlist_id: str, symbol: str) -> bool:
        """Add symbol to watchlist"""
        if watchlist_id not in self.watchlists:
            return False

        watchlist = self.watchlists[watchlist_id]
        symbol = symbol.upper().strip()

        if symbol in watchlist.symbols:
            logger.info(f"Symbol {symbol} already in watchlist {watchlist.name}")
            return False

        watchlist.symbols.append(symbol)
        watchlist.updated_at = datetime.now()
        self._save_watchlists()

        logger.info(f"Added {symbol} to {watchlist.name}")
        return True

    def remove_symbol(self, watchlist_id: str, symbol: str) -> bool:
        """Remove symbol from watchlist"""
        if watchlist_id not in self.watchlists:
            return False

        watchlist = self.watchlists[watchlist_id]
        symbol = symbol.upper().strip()

        if symbol not in watchlist.symbols:
            return False

        watchlist.symbols.remove(symbol)
        watchlist.updated_at = datetime.now()
        self._save_watchlists()

        logger.info(f"Removed {symbol} from {watchlist.name}")
        return True

    def get_watchlist(self, watchlist_id: str) -> Optional[Watchlist]:
        """Get watchlist by ID"""
        return self.watchlists.get(watchlist_id)

    def get_all_watchlists(self) -> List[Watchlist]:
        """Get all watchlists"""
        return list(self.watchlists.values())

    def get_default_watchlist(self) -> Optional[Watchlist]:
        """Get default watchlist"""
        for wl in self.watchlists.values():
            if wl.is_default:
                return wl
        return None

    def export_to_json(self, watchlist_id: str, filepath: str) -> bool:
        """Export watchlist to JSON file"""
        if watchlist_id not in self.watchlists:
            return False

        try:
            watchlist = self.watchlists[watchlist_id]

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(watchlist.to_dict(), f, ensure_ascii=False, indent=2)

            logger.info(f"Exported {watchlist.name} to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting watchlist: {e}")
            return False

    def export_to_csv(self, watchlist_id: str, filepath: str) -> bool:
        """Export watchlist symbols to CSV file"""
        if watchlist_id not in self.watchlists:
            return False

        try:
            watchlist = self.watchlists[watchlist_id]

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Symbol'])
                for symbol in watchlist.symbols:
                    writer.writerow([symbol])

            logger.info(f"Exported {watchlist.name} symbols to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False

    def import_from_json(self, filepath: str) -> Optional[Watchlist]:
        """Import watchlist from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Generate new ID to avoid conflicts
            import uuid
            watchlist_id = str(uuid.uuid4())

            watchlist = Watchlist(
                id=watchlist_id,
                name=data['name'],
                description=data.get('description', ''),
                symbols=data['symbols'],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                color=data.get('color', '#3b82f6'),
            )

            self.watchlists[watchlist_id] = watchlist
            self._save_watchlists()

            logger.info(f"Imported watchlist: {watchlist.name}")
            return watchlist
        except Exception as e:
            logger.error(f"Error importing watchlist: {e}")
            return None

    def import_from_csv(self, filepath: str, name: str, description: str = "") -> Optional[Watchlist]:
        """Import symbols from CSV file and create watchlist"""
        try:
            symbols = []

            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if row:
                        symbols.append(row[0].strip().upper())

            return self.create_watchlist(name, description, symbols)
        except Exception as e:
            logger.error(f"Error importing from CSV: {e}")
            return None

    def _create_default_templates(self):
        """Create predefined watchlist templates"""
        if self.watchlists:
            return  # Already have watchlists

        # VN30 Index
        vn30_symbols = [
            "VCB", "VHM", "VIC", "VNM", "FPT", "GAS", "MSN", "MWG", "VPB", "HPG",
            "TCB", "BID", "CTG", "SAB", "SSI", "VRE", "PLX", "POW", "MBB", "ACB",
            "GVR", "HDB", "TPB", "VJC", "PDR", "STB", "NVL", "BCM", "KDH", "VCG"
        ]

        self.create_watchlist(
            name="VN30",
            description="VN30 Index - Top 30 stocks by market cap",
            symbols=vn30_symbols,
            color="#22c55e"
        )

        # Banking sector
        banking_symbols = ["VCB", "TCB", "BID", "CTG", "MBB", "ACB", "VPB", "HDB", "TPB", "STB"]
        self.create_watchlist(
            name="Ngân hàng",
            description="Banking sector stocks",
            symbols=banking_symbols,
            color="#3b82f6"
        )

        # Real Estate
        realestate_symbols = ["VHM", "VIC", "NVL", "KDH", "BCM", "VRE", "PDR"]
        self.create_watchlist(
            name="Bất động sản",
            description="Real estate stocks",
            symbols=realestate_symbols,
            color="#f59e0b"
        )

        # Technology
        tech_symbols = ["FPT", "CMG", "VGI", "SAM", "ITD"]
        self.create_watchlist(
            name="Công nghệ",
            description="Technology sector",
            symbols=tech_symbols,
            color="#8b5cf6"
        )

        # Securities
        securities_symbols = ["SSI", "VND", "HCM", "VCI", "MBS", "SHS"]
        self.create_watchlist(
            name="Chứng khoán",
            description="Securities companies",
            symbols=securities_symbols,
            color="#ec4899"
        )

        # Set VN30 as default
        if self.watchlists:
            vn30_id = list(self.watchlists.keys())[0]
            self.watchlists[vn30_id].is_default = True

        self._save_watchlists()
        logger.info("Created default watchlist templates")

    def search_symbols(self, query: str) -> List[str]:
        """Search for symbols across all watchlists"""
        query = query.upper()
        found = set()

        for watchlist in self.watchlists.values():
            for symbol in watchlist.symbols:
                if query in symbol:
                    found.add(symbol)

        return sorted(list(found))

    def get_all_unique_symbols(self) -> List[str]:
        """Get all unique symbols across all watchlists"""
        all_symbols = set()

        for watchlist in self.watchlists.values():
            all_symbols.update(watchlist.symbols)

        return sorted(list(all_symbols))


# Global instance
watchlist_manager = WatchlistManager()
