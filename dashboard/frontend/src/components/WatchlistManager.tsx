/**
 * Watchlist Manager Component
 * Complete UI for managing watchlists
 */
import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, Download, Upload, Search, X } from 'lucide-react';

interface Watchlist {
  id: string;
  name: string;
  description: string;
  symbols: string[];
  color: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

interface WatchlistManagerProps {
  onSelectWatchlist?: (watchlist: Watchlist) => void;
}

export const WatchlistManager: React.FC<WatchlistManagerProps> = ({ onSelectWatchlist }) => {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [selectedWatchlist, setSelectedWatchlist] = useState<Watchlist | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [newSymbol, setNewSymbol] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color: '#3b82f6',
  });

  useEffect(() => {
    loadWatchlists();
  }, []);

  const loadWatchlists = async () => {
    try {
      const response = await fetch('/api/v1/watchlists/');
      const data = await response.json();
      setWatchlists(data);

      // Auto-select default watchlist
      const defaultWL = data.find((wl: Watchlist) => wl.is_default);
      if (defaultWL && !selectedWatchlist) {
        setSelectedWatchlist(defaultWL);
        onSelectWatchlist?.(defaultWL);
      }
    } catch (error) {
      console.error('Failed to load watchlists:', error);
    }
  };

  const createWatchlist = async () => {
    try {
      const response = await fetch('/api/v1/watchlists/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      if (data.success) {
        await loadWatchlists();
        setIsCreating(false);
        setFormData({ name: '', description: '', color: '#3b82f6' });
      }
    } catch (error) {
      console.error('Failed to create watchlist:', error);
    }
  };

  const updateWatchlist = async () => {
    if (!selectedWatchlist) return;

    try {
      const response = await fetch(`/api/v1/watchlists/${selectedWatchlist.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      if (data.success) {
        await loadWatchlists();
        setIsEditing(false);
      }
    } catch (error) {
      console.error('Failed to update watchlist:', error);
    }
  };

  const deleteWatchlist = async (id: string) => {
    if (!confirm('Are you sure you want to delete this watchlist?')) return;

    try {
      const response = await fetch(`/api/v1/watchlists/${id}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      if (data.success) {
        await loadWatchlists();
        if (selectedWatchlist?.id === id) {
          setSelectedWatchlist(null);
        }
      }
    } catch (error) {
      console.error('Failed to delete watchlist:', error);
    }
  };

  const addSymbol = async () => {
    if (!selectedWatchlist || !newSymbol.trim()) return;

    try {
      const response = await fetch(`/api/v1/watchlists/${selectedWatchlist.id}/symbols`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: newSymbol.toUpperCase() }),
      });

      const data = await response.json();
      if (data.success) {
        setSelectedWatchlist(data.watchlist);
        setNewSymbol('');
        await loadWatchlists();
      }
    } catch (error) {
      console.error('Failed to add symbol:', error);
    }
  };

  const removeSymbol = async (symbol: string) => {
    if (!selectedWatchlist) return;

    try {
      const response = await fetch(
        `/api/v1/watchlists/${selectedWatchlist.id}/symbols/${symbol}`,
        { method: 'DELETE' }
      );

      const data = await response.json();
      if (data.success) {
        setSelectedWatchlist(data.watchlist);
        await loadWatchlists();
      }
    } catch (error) {
      console.error('Failed to remove symbol:', error);
    }
  };

  const exportToCSV = async () => {
    if (!selectedWatchlist) return;

    try {
      const response = await fetch(
        `/api/v1/watchlists/${selectedWatchlist.id}/export/csv`
      );
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedWatchlist.name}.csv`;
      a.click();
    } catch (error) {
      console.error('Failed to export:', error);
    }
  };

  const filteredSymbols = selectedWatchlist?.symbols.filter(symbol =>
    symbol.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="watchlist-manager bg-gray-900 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Watchlists</h2>
        <button
          onClick={() => setIsCreating(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded flex items-center gap-1"
        >
          <Plus className="w-4 h-4" />
          New
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Watchlist List */}
        <div className="col-span-1 space-y-2">
          {watchlists.map((wl) => (
            <div
              key={wl.id}
              onClick={() => {
                setSelectedWatchlist(wl);
                onSelectWatchlist?.(wl);
              }}
              className={`p-3 rounded cursor-pointer transition-colors ${
                selectedWatchlist?.id === wl.id
                  ? 'bg-gray-700'
                  : 'bg-gray-800 hover:bg-gray-750'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: wl.color }}
                  />
                  <span className="text-white font-medium">{wl.name}</span>
                </div>
                <span className="text-gray-400 text-sm">{wl.symbols.length}</span>
              </div>
              {wl.description && (
                <p className="text-gray-400 text-xs mt-1">{wl.description}</p>
              )}
            </div>
          ))}
        </div>

        {/* Watchlist Detail */}
        <div className="col-span-2">
          {selectedWatchlist ? (
            <div className="bg-gray-800 rounded p-4">
              {/* Toolbar */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">
                  {selectedWatchlist.name}
                </h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setFormData({
                        name: selectedWatchlist.name,
                        description: selectedWatchlist.description,
                        color: selectedWatchlist.color,
                      });
                      setIsEditing(true);
                    }}
                    className="text-gray-400 hover:text-white"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={exportToCSV}
                    className="text-gray-400 hover:text-white"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  {!selectedWatchlist.is_default && (
                    <button
                      onClick={() => deleteWatchlist(selectedWatchlist.id)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Add Symbol */}
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
                  placeholder="Add symbol (e.g., VCB)"
                  className="flex-1 bg-gray-700 text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={addSymbol}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                >
                  Add
                </button>
              </div>

              {/* Search */}
              <div className="relative mb-4">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search symbols..."
                  className="w-full bg-gray-700 text-white pl-10 pr-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Symbols Grid */}
              <div className="grid grid-cols-4 gap-2 max-h-96 overflow-y-auto">
                {filteredSymbols.map((symbol) => (
                  <div
                    key={symbol}
                    className="bg-gray-700 rounded px-3 py-2 flex items-center justify-between group"
                  >
                    <span className="text-white font-medium">{symbol}</span>
                    <button
                      onClick={() => removeSymbol(symbol)}
                      className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>

              {filteredSymbols.length === 0 && (
                <div className="text-center text-gray-400 py-8">
                  No symbols in this watchlist
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-800 rounded p-8 text-center text-gray-400">
              Select a watchlist to view symbols
            </div>
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {(isCreating || isEditing) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96">
            <h3 className="text-xl font-bold text-white mb-4">
              {isCreating ? 'Create Watchlist' : 'Edit Watchlist'}
            </h3>

            <div className="space-y-4">
              <div>
                <label className="text-gray-400 text-sm block mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-gray-700 text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="text-gray-400 text-sm block mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="w-full bg-gray-700 text-white px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>

              <div>
                <label className="text-gray-400 text-sm block mb-1">Color</label>
                <input
                  type="color"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  className="w-full h-10 bg-gray-700 rounded cursor-pointer"
                />
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={() => {
                  setIsCreating(false);
                  setIsEditing(false);
                  setFormData({ name: '', description: '', color: '#3b82f6' });
                }}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded"
              >
                Cancel
              </button>
              <button
                onClick={isCreating ? createWatchlist : updateWatchlist}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
              >
                {isCreating ? 'Create' : 'Update'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
