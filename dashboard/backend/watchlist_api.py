"""
Watchlist API Endpoints for Dashboard
"""
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.watchlist_manager import watchlist_manager, Watchlist
from loguru import logger


router = APIRouter(prefix="/api/v1/watchlists", tags=["watchlists"])


# Pydantic models for request/response
class WatchlistCreate(BaseModel):
    name: str
    description: str = ""
    symbols: List[str] = []
    color: str = "#3b82f6"


class WatchlistUpdate(BaseModel):
    name: str = None
    description: str = None
    symbols: List[str] = None
    color: str = None


class SymbolAdd(BaseModel):
    symbol: str


class WatchlistImport(BaseModel):
    name: str
    description: str = ""
    symbols: List[str]


@router.get("/")
async def get_all_watchlists():
    """Get all watchlists"""
    watchlists = watchlist_manager.get_all_watchlists()
    return [wl.to_dict() for wl in watchlists]


@router.get("/default")
async def get_default_watchlist():
    """Get default watchlist"""
    watchlist = watchlist_manager.get_default_watchlist()
    if not watchlist:
        raise HTTPException(status_code=404, detail="No default watchlist found")
    return watchlist.to_dict()


@router.get("/{watchlist_id}")
async def get_watchlist(watchlist_id: str):
    """Get specific watchlist"""
    watchlist = watchlist_manager.get_watchlist(watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist.to_dict()


@router.post("/")
async def create_watchlist(data: WatchlistCreate):
    """Create new watchlist"""
    try:
        watchlist = watchlist_manager.create_watchlist(
            name=data.name,
            description=data.description,
            symbols=data.symbols,
            color=data.color,
        )
        return {"success": True, "watchlist": watchlist.to_dict()}
    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{watchlist_id}")
async def update_watchlist(watchlist_id: str, data: WatchlistUpdate):
    """Update watchlist"""
    watchlist = watchlist_manager.update_watchlist(
        watchlist_id=watchlist_id,
        name=data.name,
        description=data.description,
        symbols=data.symbols,
        color=data.color,
    )

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {"success": True, "watchlist": watchlist.to_dict()}


@router.delete("/{watchlist_id}")
async def delete_watchlist(watchlist_id: str):
    """Delete watchlist"""
    success = watchlist_manager.delete_watchlist(watchlist_id)

    if not success:
        raise HTTPException(status_code=404, detail="Watchlist not found or cannot delete")

    return {"success": True, "message": "Watchlist deleted"}


@router.post("/{watchlist_id}/symbols")
async def add_symbol(watchlist_id: str, data: SymbolAdd):
    """Add symbol to watchlist"""
    success = watchlist_manager.add_symbol(watchlist_id, data.symbol)

    if not success:
        raise HTTPException(status_code=400, detail="Could not add symbol")

    watchlist = watchlist_manager.get_watchlist(watchlist_id)
    return {"success": True, "watchlist": watchlist.to_dict()}


@router.delete("/{watchlist_id}/symbols/{symbol}")
async def remove_symbol(watchlist_id: str, symbol: str):
    """Remove symbol from watchlist"""
    success = watchlist_manager.remove_symbol(watchlist_id, symbol)

    if not success:
        raise HTTPException(status_code=400, detail="Could not remove symbol")

    watchlist = watchlist_manager.get_watchlist(watchlist_id)
    return {"success": True, "watchlist": watchlist.to_dict()}


@router.get("/search/{query}")
async def search_symbols(query: str):
    """Search symbols across all watchlists"""
    results = watchlist_manager.search_symbols(query)
    return {"symbols": results}


@router.get("/symbols/all")
async def get_all_symbols():
    """Get all unique symbols"""
    symbols = watchlist_manager.get_all_unique_symbols()
    return {"symbols": symbols}


@router.post("/import")
async def import_watchlist(data: WatchlistImport):
    """Import watchlist from symbols list"""
    watchlist = watchlist_manager.create_watchlist(
        name=data.name,
        description=data.description,
        symbols=data.symbols
    )
    return {"success": True, "watchlist": watchlist.to_dict()}


@router.get("/{watchlist_id}/export/json")
async def export_json(watchlist_id: str):
    """Export watchlist as JSON"""
    watchlist = watchlist_manager.get_watchlist(watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return watchlist.to_dict()


@router.get("/{watchlist_id}/export/csv")
async def export_csv(watchlist_id: str):
    """Export watchlist symbols as CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv

    watchlist = watchlist_manager.get_watchlist(watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Symbol'])
    for symbol in watchlist.symbols:
        writer.writerow([symbol])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={watchlist.name}.csv"
        }
    )
