import { useMemo } from 'react';

const trades = [
  { symbol: 'AAPL', side: 'Buy', size: 200, price: 175.24, status: 'Filled' },
  { symbol: 'TSLA', side: 'Sell', size: 50, price: 820.50, status: 'Partial' },
  { symbol: 'BTCUSD', side: 'Buy', size: 0.15, price: 69300.0, status: 'Filled' },
  { symbol: 'ETHUSD', side: 'Sell', size: 1.2, price: 3290.8, status: 'Pending' },
];

const summary = [
  { label: 'Portfolio value', value: '$124,800' },
  { label: 'Daily P/L', value: '+$4,200' },
  { label: 'Open positions', value: '7' },
  { label: 'Available cash', value: '$48,500' },
];

function App() {
  const totalTrades = useMemo(() => trades.length, []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <h1>Trading Dashboard</h1>
          <p>Monitor positions, orders, and market activity.</p>
        </div>
        <button>New Order</button>
      </header>
      <section className="summary-grid">
        {summary.map((item) => (
          <article key={item.label} className="summary-card">
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </article>
        ))}
      </section>
      <main className="dashboard-grid">
        <section className="panel chart-panel">
          <h2>Market Overview</h2>
          <div className="chart-placeholder">Price chart placeholder</div>
          <p className="panel-footer">Real-time updates and market depth visualization.</p>
        </section>
        <section className="panel trades-panel">
          <div className="panel-header">
            <h2>Recent Trades</h2>
            <span>{totalTrades} trades</span>
          </div>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Size</th>
                <th>Price</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr key={`${trade.symbol}-${trade.price}`}>
                  <td>{trade.symbol}</td>
                  <td>{trade.side}</td>
                  <td>{trade.size}</td>
                  <td>{trade.price.toFixed(2)}</td>
                  <td>{trade.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}

export default App;
