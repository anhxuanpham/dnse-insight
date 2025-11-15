import { useState, useEffect } from 'react'
import { WatchlistManager } from './components/WatchlistManager'
import { TradingChart } from './components/TradingChart'
import { MarketHeatmap } from './components/MarketHeatmap'
import { Watchlist } from './components/Watchlist'

function App() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('VCB')
  const [view, setView] = useState<'dashboard' | 'watchlist' | 'chart' | 'heatmap'>('dashboard')

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-blue-400">
              📊 DNSE Insight
            </h1>
            <span className="text-sm text-gray-400">
              Real-time Trading Dashboard
            </span>
          </div>

          <nav className="flex space-x-4">
            <button
              onClick={() => setView('dashboard')}
              className={`px-4 py-2 rounded-lg transition ${
                view === 'dashboard'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setView('watchlist')}
              className={`px-4 py-2 rounded-lg transition ${
                view === 'watchlist'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Watchlists
            </button>
            <button
              onClick={() => setView('chart')}
              className={`px-4 py-2 rounded-lg transition ${
                view === 'chart'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Charts
            </button>
            <button
              onClick={() => setView('heatmap')}
              className={`px-4 py-2 rounded-lg transition ${
                view === 'heatmap'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Heatmap
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto p-6">
        {view === 'dashboard' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Watchlist */}
            <div className="lg:col-span-1">
              <Watchlist onSelectSymbol={setSelectedSymbol} />
            </div>

            {/* Right: Chart + Info */}
            <div className="lg:col-span-2 space-y-6">
              <TradingChart symbol={selectedSymbol} />

              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-sm text-gray-400">Portfolio Value</p>
                  <p className="text-2xl font-bold text-green-400">
                    1,234,567,890 VND
                  </p>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-sm text-gray-400">Today's P&L</p>
                  <p className="text-2xl font-bold text-green-400">
                    +12,345,678 VND
                  </p>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-sm text-gray-400">Win Rate</p>
                  <p className="text-2xl font-bold text-blue-400">
                    68.5%
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {view === 'watchlist' && (
          <WatchlistManager onSelectWatchlist={(wl) => console.log('Selected:', wl)} />
        )}

        {view === 'chart' && (
          <div className="max-w-7xl mx-auto">
            <TradingChart symbol={selectedSymbol} />
          </div>
        )}

        {view === 'heatmap' && (
          <MarketHeatmap />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 px-6 py-4 mt-8">
        <div className="text-center text-sm text-gray-400">
          <p>DNSE Insight Trading Bot © 2024 | Made with ❤️ for Vietnamese traders</p>
        </div>
      </footer>
    </div>
  )
}

export default App
