/**
 * Watchlist Component with Auto-scanning Signals
 */
import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface WatchlistItem {
  symbol: string;
  price: number;
  change_percent: number;
  volume: number;
  signal: {
    signal_type: string;
    strength: number;
    reason: string;
  } | null;
}

interface WatchlistProps {
  items: WatchlistItem[];
  onSymbolClick?: (symbol: string) => void;
}

export const Watchlist: React.FC<WatchlistProps> = ({ items, onSymbolClick }) => {
  const getSignalBadge = (signal: WatchlistItem['signal']) => {
    if (!signal) return null;

    const colors = {
      BUY: 'bg-green-500',
      SELL: 'bg-red-500',
      HOLD: 'bg-gray-500',
      CUTLOSS: 'bg-red-700',
    };

    const color = colors[signal.signal_type as keyof typeof colors] || 'bg-gray-500';

    return (
      <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${color}`}>
        {signal.signal_type}
      </span>
    );
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (change < 0) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  return (
    <div className="watchlist bg-gray-900 rounded-lg p-4">
      <h2 className="text-xl font-bold text-white mb-4">Watchlist</h2>
      <div className="space-y-2">
        {items.map((item) => (
          <div
            key={item.symbol}
            className="bg-gray-800 rounded p-3 hover:bg-gray-750 cursor-pointer transition-colors"
            onClick={() => onSymbolClick?.(item.symbol)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-white font-bold text-lg">{item.symbol}</span>
                {getChangeIcon(item.change_percent)}
              </div>
              {getSignalBadge(item.signal)}
            </div>

            <div className="mt-2 flex items-center justify-between text-sm">
              <div>
                <span className="text-white font-semibold">{item.price.toFixed(2)}</span>
                <span className={`ml-2 ${item.change_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {item.change_percent >= 0 ? '+' : ''}{item.change_percent.toFixed(2)}%
                </span>
              </div>
              <span className="text-gray-400">
                Vol: {(item.volume / 1000000).toFixed(1)}M
              </span>
            </div>

            {item.signal && (
              <div className="mt-2 text-xs text-gray-400 truncate">
                {item.signal.reason}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
