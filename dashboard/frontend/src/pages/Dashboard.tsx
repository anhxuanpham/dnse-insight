/**
 * Main Dashboard Page
 */
import React, { useState, useEffect } from 'react';
import { TradingChart } from '../components/TradingChart';
import { MarketHeatmap } from '../components/MarketHeatmap';
import { Watchlist } from '../components/Watchlist';
import { useWebSocket } from '../hooks/useWebSocket';
import { useApi } from '../hooks/useApi';

export const Dashboard: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('VCB');
  const { isConnected, subscribe, unsubscribe } = useWebSocket();
  const { data: heatmapData, isLoading: heatmapLoading } = useApi('/api/v1/market/heatmap');
  const { data: watchlistData, isLoading: watchlistLoading } = useApi('/api/v1/market/watchlist');
  const { data: portfolioData } = useApi('/api/v1/portfolio/summary');

  useEffect(() => {
    // Subscribe to selected symbol on WebSocket
    if (isConnected) {
      subscribe([selectedSymbol]);
    }

    return () => {
      if (isConnected) {
        unsubscribe([selectedSymbol]);
      }
    };
  }, [selectedSymbol, isConnected]);

  const handleSymbolClick = (symbol: string) => {
    setSelectedSymbol(symbol);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 p-4">
        <div className="container mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold">DNSE Insight Dashboard</h1>
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
              <span className="text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
            {portfolioData && (
              <div className="text-right">
                <div className="text-xs text-gray-400">Portfolio Value</div>
                <div className="text-lg font-bold">
                  {(portfolioData.total_value / 1000000).toFixed(1)}M VND
                </div>
                <div className={`text-sm ${portfolioData.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {portfolioData.total_pnl >= 0 ? '+' : ''}
                  {(portfolioData.total_pnl / 1000000).toFixed(2)}M ({(portfolioData.total_return * 100).toFixed(2)}%)
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto p-4">
        <div className="grid grid-cols-12 gap-4">
          {/* Left Sidebar - Watchlist */}
          <div className="col-span-3">
            {watchlistLoading ? (
              <div className="animate-pulse bg-gray-800 rounded-lg h-96" />
            ) : (
              <Watchlist
                items={watchlistData || []}
                onSymbolClick={handleSymbolClick}
              />
            )}
          </div>

          {/* Center - Chart */}
          <div className="col-span-6">
            <div className="bg-gray-900 rounded-lg p-4">
              <TradingChart
                symbol={selectedSymbol}
                data={[]} // Will be populated from WebSocket
                width={800}
                height={500}
              />
            </div>

            {/* Market Heatmap */}
            <div className="mt-4">
              {heatmapLoading ? (
                <div className="animate-pulse bg-gray-800 rounded-lg h-96" />
              ) : (
                <MarketHeatmap data={heatmapData || []} />
              )}
            </div>
          </div>

          {/* Right Sidebar - Portfolio & Signals */}
          <div className="col-span-3">
            <div className="bg-gray-900 rounded-lg p-4">
              <h2 className="text-xl font-bold mb-4">Active Positions</h2>
              {/* Positions list will go here */}
              <div className="text-sm text-gray-400">
                No active positions
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
