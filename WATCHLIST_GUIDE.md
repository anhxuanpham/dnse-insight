# 📋 Watchlist Management Guide

Complete guide for managing watchlists in DNSE Insight trading system.

## 🎯 Overview

The Watchlist Management system allows you to:
- ✅ Create **unlimited watchlists**
- ✅ **Add/Remove symbols** easily
- ✅ **Organize** stocks by sector, strategy, or preference
- ✅ **Import/Export** watchlists (JSON, CSV)
- ✅ **Search** across all watchlists
- ✅ **Color-code** for easy identification
- ✅ **Pre-loaded templates** (VN30, Banking, Tech, etc.)

---

## 🚀 Quick Start

### Via Web Dashboard

1. **Access Dashboard**: `http://localhost:3000`
2. **Click "Watchlists"** in sidebar
3. **View predefined templates** or create new

### Via API

```bash
# Get all watchlists
curl http://localhost:8001/api/v1/watchlists/

# Get default watchlist
curl http://localhost:8001/api/v1/watchlists/default
```

### Via Python Code

```python
from core.watchlist_manager import watchlist_manager

# Get all watchlists
watchlists = watchlist_manager.get_all_watchlists()

# Create new watchlist
wl = watchlist_manager.create_watchlist(
    name="My Portfolio",
    symbols=["VCB", "VHM", "FPT"]
)
```

---

## 📚 Predefined Templates

The system comes with 5 predefined watchlists:

### 1. VN30 (Default) 🟢
**30 stocks** - Top companies by market cap
```
VCB, VHM, VIC, VNM, FPT, GAS, MSN, MWG, VPB, HPG,
TCB, BID, CTG, SAB, SSI, VRE, PLX, POW, MBB, ACB,
GVR, HDB, TPB, VJC, PDR, STB, NVL, BCM, KDH, VCG
```

### 2. Ngân hàng (Banking) 🔵
**10 stocks** - Banking sector
```
VCB, TCB, BID, CTG, MBB, ACB, VPB, HDB, TPB, STB
```

### 3. Bất động sản (Real Estate) 🟡
**7 stocks** - Real estate sector
```
VHM, VIC, NVL, KDH, BCM, VRE, PDR
```

### 4. Công nghệ (Technology) 🟣
**5 stocks** - Technology sector
```
FPT, CMG, VGI, SAM, ITD
```

### 5. Chứng khoán (Securities) 🔴
**6 stocks** - Securities companies
```
SSI, VND, HCM, VCI, MBS, SHS
```

---

## 🛠️ API Reference

### Get All Watchlists

```bash
GET /api/v1/watchlists/

Response:
[
  {
    "id": "uuid",
    "name": "VN30",
    "description": "Top 30 stocks",
    "symbols": ["VCB", "VHM", ...],
    "color": "#22c55e",
    "is_default": true,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00"
  }
]
```

### Get Specific Watchlist

```bash
GET /api/v1/watchlists/{watchlist_id}

Response:
{
  "id": "uuid",
  "name": "My Portfolio",
  "symbols": ["VCB", "VHM", "FPT"],
  ...
}
```

### Create Watchlist

```bash
POST /api/v1/watchlists/
Content-Type: application/json

{
  "name": "Tech Stocks",
  "description": "Technology companies",
  "symbols": ["FPT", "CMG", "VGI"],
  "color": "#8b5cf6"
}

Response:
{
  "success": true,
  "watchlist": { ... }
}
```

### Update Watchlist

```bash
PUT /api/v1/watchlists/{watchlist_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "color": "#f59e0b"
}
```

### Delete Watchlist

```bash
DELETE /api/v1/watchlists/{watchlist_id}

Response:
{
  "success": true,
  "message": "Watchlist deleted"
}
```

### Add Symbol

```bash
POST /api/v1/watchlists/{watchlist_id}/symbols
Content-Type: application/json

{
  "symbol": "VCB"
}

Response:
{
  "success": true,
  "watchlist": { ... }
}
```

### Remove Symbol

```bash
DELETE /api/v1/watchlists/{watchlist_id}/symbols/{symbol}

Response:
{
  "success": true,
  "watchlist": { ... }
}
```

### Search Symbols

```bash
GET /api/v1/watchlists/search/{query}

Example: GET /api/v1/watchlists/search/VC

Response:
{
  "symbols": ["VCB", "VCI", "VCG"]
}
```

### Get All Unique Symbols

```bash
GET /api/v1/watchlists/symbols/all

Response:
{
  "symbols": ["ACB", "BCM", "BID", "CMG", ...]
}
```

### Export to JSON

```bash
GET /api/v1/watchlists/{watchlist_id}/export/json

Response:
{
  "id": "uuid",
  "name": "My Portfolio",
  "symbols": ["VCB", "VHM"],
  ...
}
```

### Export to CSV

```bash
GET /api/v1/watchlists/{watchlist_id}/export/csv

Response: (CSV file download)
Symbol
VCB
VHM
FPT
```

### Import Watchlist

```bash
POST /api/v1/watchlists/import
Content-Type: application/json

{
  "name": "Imported List",
  "description": "From external source",
  "symbols": ["VCB", "VHM", "FPT", "HPG"]
}
```

---

## 💻 Python Usage Examples

### Basic Operations

```python
from core.watchlist_manager import watchlist_manager

# Create watchlist
wl = watchlist_manager.create_watchlist(
    name="My Favorites",
    description="Stocks I'm watching",
    symbols=["VCB", "FPT", "MWG"],
    color="#10b981"
)

# Add symbol
watchlist_manager.add_symbol(wl.id, "VHM")

# Remove symbol
watchlist_manager.remove_symbol(wl.id, "MWG")

# Update watchlist
watchlist_manager.update_watchlist(
    wl.id,
    name="Updated Name",
    description="New description"
)

# Delete watchlist
watchlist_manager.delete_watchlist(wl.id)
```

### Export/Import

```python
# Export to CSV
watchlist_manager.export_to_csv(wl.id, "my_watchlist.csv")

# Export to JSON
watchlist_manager.export_to_json(wl.id, "my_watchlist.json")

# Import from JSON
imported_wl = watchlist_manager.import_from_json("my_watchlist.json")

# Import from CSV
imported_wl = watchlist_manager.import_from_csv(
    "symbols.csv",
    name="Imported Stocks",
    description="From CSV file"
)
```

### Search and Query

```python
# Search symbols
results = watchlist_manager.search_symbols("VC")
# Returns: ["VCB", "VCI", "VCG"]

# Get all unique symbols
all_symbols = watchlist_manager.get_all_unique_symbols()
# Returns: ["ACB", "BCM", "BID", ...]

# Get default watchlist
default = watchlist_manager.get_default_watchlist()

# Get all watchlists
all_wl = watchlist_manager.get_all_watchlists()
```

---

## 🎨 Frontend Usage (React)

```tsx
import { WatchlistManager } from '../components/WatchlistManager';

function App() {
  const handleSelectWatchlist = (watchlist) => {
    console.log('Selected:', watchlist.name);
    // Subscribe to symbols for real-time data
    subscribeToSymbols(watchlist.symbols);
  };

  return (
    <WatchlistManager onSelectWatchlist={handleSelectWatchlist} />
  );
}
```

### Component Features

- ✅ **Drag & drop** symbol management
- ✅ **Color picker** for visual organization
- ✅ **Search** within watchlist
- ✅ **Export** buttons for CSV/JSON
- ✅ **Real-time** symbol count
- ✅ **Delete confirmation** dialog
- ✅ **Auto-save** on changes

---

## 📝 File Formats

### JSON Format

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "My Portfolio",
  "description": "Active trades",
  "symbols": ["VCB", "VHM", "FPT"],
  "color": "#3b82f6",
  "is_default": false,
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T12:00:00"
}
```

### CSV Format

```csv
Symbol
VCB
VHM
FPT
HPG
MWG
```

---

## 🔧 Integration Examples

### With Trading Bot

```python
from core.trading_bot import TradingBot
from core.watchlist_manager import watchlist_manager

# Get symbols from watchlist
wl = watchlist_manager.get_watchlist("watchlist-id")

# Start bot with watchlist symbols
bot = TradingBot(symbols=wl.symbols)
bot.start()
```

### With Market Screener

```python
from screener.core.scanner_engine import scanner_engine
from core.watchlist_manager import watchlist_manager

# Scan symbols from watchlist
wl = watchlist_manager.get_default_watchlist()
scanner_engine.set_symbols(wl.symbols)

# Run scan
results = scanner_engine.scan_all()
```

### With Dashboard

```python
# Auto-load watchlist on dashboard startup
default_wl = watchlist_manager.get_default_watchlist()

# Subscribe to WebSocket updates for all symbols
for symbol in default_wl.symbols:
    subscribe_to_price_updates(symbol)
```

---

## 🎯 Best Practices

### 1. Organize by Strategy

```python
# Momentum stocks
momentum_wl = watchlist_manager.create_watchlist(
    name="Momentum",
    symbols=["FPT", "CMG", "MWG"],
    color="#22c55e"
)

# Value stocks
value_wl = watchlist_manager.create_watchlist(
    name="Value Plays",
    symbols=["VCB", "TCB", "BID"],
    color="#3b82f6"
)
```

### 2. Organize by Sector

```python
# Banking
banking = watchlist_manager.create_watchlist(
    name="Banks",
    symbols=["VCB", "TCB", "BID", "CTG"],
    color="#3b82f6"
)

# Tech
tech = watchlist_manager.create_watchlist(
    name="Technology",
    symbols=["FPT", "CMG", "VGI"],
    color="#8b5cf6"
)
```

### 3. Organize by Risk Level

```python
# Conservative (blue chips)
conservative = watchlist_manager.create_watchlist(
    name="Blue Chips",
    symbols=["VCB", "VHM", "VIC", "GAS"],
    color="#10b981"
)

# Aggressive (high volatility)
aggressive = watchlist_manager.create_watchlist(
    name="High Risk",
    symbols=["SSI", "VND", "HCM"],
    color="#ef4444"
)
```

### 4. Regular Updates

```python
# Weekly review and update
def weekly_review():
    wl = watchlist_manager.get_watchlist("my-portfolio-id")

    # Remove underperformers
    for symbol in symbols_to_remove:
        watchlist_manager.remove_symbol(wl.id, symbol)

    # Add new opportunities
    for symbol in new_symbols:
        watchlist_manager.add_symbol(wl.id, symbol)
```

---

## 🔍 Advanced Features

### 1. Bulk Operations

```python
# Add multiple symbols at once
symbols_to_add = ["VCB", "VHM", "FPT", "HPG", "MWG"]
for symbol in symbols_to_add:
    watchlist_manager.add_symbol(wl.id, symbol)
```

### 2. Clone Watchlist

```python
# Get existing watchlist
original = watchlist_manager.get_watchlist("original-id")

# Create copy
copy = watchlist_manager.create_watchlist(
    name=f"{original.name} (Copy)",
    description=original.description,
    symbols=original.symbols.copy(),
    color=original.color
)
```

### 3. Merge Watchlists

```python
wl1 = watchlist_manager.get_watchlist("id1")
wl2 = watchlist_manager.get_watchlist("id2")

# Combine symbols
merged_symbols = list(set(wl1.symbols + wl2.symbols))

# Create merged watchlist
merged = watchlist_manager.create_watchlist(
    name="Merged List",
    symbols=merged_symbols
)
```

---

## 🐛 Troubleshooting

### Watchlist Not Saving

```python
# Check storage path permissions
from pathlib import Path
storage_path = Path("data/watchlists.json")
print(f"Exists: {storage_path.exists()}")
print(f"Writable: {storage_path.parent.is_dir()}")
```

### Symbol Not Adding

```python
# Ensure symbol is uppercase
watchlist_manager.add_symbol(wl_id, "vcb")  # Wrong
watchlist_manager.add_symbol(wl_id, "VCB")  # Correct
```

### Cannot Delete Watchlist

```python
# Default watchlists cannot be deleted
wl = watchlist_manager.get_watchlist(wl_id)
if wl.is_default:
    print("Cannot delete default watchlist")
```

---

## 📊 Statistics

```python
# Get watchlist statistics
def get_stats():
    all_wl = watchlist_manager.get_all_watchlists()
    all_symbols = watchlist_manager.get_all_unique_symbols()

    print(f"Total Watchlists: {len(all_wl)}")
    print(f"Total Unique Symbols: {len(all_symbols)}")

    for wl in all_wl:
        print(f"  {wl.name}: {len(wl.symbols)} symbols")
```

---

## 🔗 Related Documentation

- **Main README**: Complete system overview
- **DEPLOYMENT.md**: Production deployment guide
- **API Documentation**: `http://localhost:8000/docs`

---

## 💡 Tips

1. **Use color coding** - Helps identify watchlists quickly
2. **Keep focused** - Don't add too many symbols to one watchlist
3. **Review regularly** - Update watchlists based on market conditions
4. **Backup exports** - Export important watchlists regularly
5. **Use templates** - Start with predefined templates and customize

---

**Created:** 2024-01-15
**Last Updated:** 2024-01-15
**Version:** 1.0.0
