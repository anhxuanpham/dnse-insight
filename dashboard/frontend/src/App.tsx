import { useState } from 'react'

function App() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('VCB')

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

          <div className="text-sm text-green-400">
            ● Connected
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto p-6">
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <h2 className="text-3xl font-bold mb-4">DNSE Trading Bot Dashboard</h2>
          <p className="text-xl text-gray-300 mb-6">System is running successfully!</p>

          <div className="grid grid-cols-3 gap-4 mt-8">
            <div className="bg-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-400">Selected Symbol</p>
              <p className="text-2xl font-bold text-blue-400">{selectedSymbol}</p>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-400">Portfolio Value</p>
              <p className="text-2xl font-bold text-green-400">1,234M VND</p>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-400">Status</p>
              <p className="text-2xl font-bold text-green-400">Active</p>
            </div>
          </div>

          <div className="mt-8 space-x-4">
            <button
              onClick={() => setSelectedSymbol('VCB')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
            >
              VCB
            </button>
            <button
              onClick={() => setSelectedSymbol('VHM')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
            >
              VHM
            </button>
            <button
              onClick={() => setSelectedSymbol('HPG')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
            >
              HPG
            </button>
          </div>
        </div>
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
