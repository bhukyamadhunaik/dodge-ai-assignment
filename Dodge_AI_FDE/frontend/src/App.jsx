import React, { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Send, Loader2, Maximize2, Minimize2 } from 'lucide-react';
import './App.css';

export default function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', text: 'Hello! I am Dodge AI. Ask me about the O2C flow, highest billing products, or broken flows.' }
  ]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const fgRef = useRef();

  useEffect(() => {
    // Fetch graph data
    fetch('http://localhost:8000/api/graph')
      .then(res => res.json())
      .then(data => {
        setGraphData(data);
        console.log("Loaded graph:", data.nodes.length, "nodes");
      })
      .catch(err => console.error("Error loading graph:", err));
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = { role: 'user', text: query };
    setChatHistory(prev => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.text })
      });
      const data = await res.json();
      setChatHistory(prev => [...prev, { role: 'assistant', text: data.response || "No response." }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'assistant', text: "Error connecting to server." }]);
    } finally {
      setLoading(false);
    }
  };

  const getThemeColor = (type) => {
    switch(type) {
      case 'SalesOrder': return '#3b82f6'; // blue
      case 'Customer': return '#eab308'; // yellow
      case 'SalesOrderItem': return '#60a5fa'; // light blue
      case 'Delivery': return '#10b981'; // green
      case 'DeliveryItem': return '#34d399'; // light green
      case 'BillingDocument': return '#8b5cf6'; // purple
      case 'BillingItem': return '#a78bfa'; // light purple
      case 'JournalEntry': return '#f43f5e'; // rose
      case 'Product': return '#f97316'; // orange
      case 'Plant': return '#14b8a6'; // teal
      default: return '#9ca3af'; // gray
    }
  };

  return (
    <div className="layout">
      {/* Sidebar for Chat */}
      <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="logo-container">
            <div className="logo-dot"></div>
            <h2>Dodge AI</h2>
          </div>
          <button className="toggle-btn mobile-only" onClick={() => setSidebarOpen(false)}>
            <Minimize2 size={18} />
          </button>
        </div>
        
        <div className="chat-container">
          <div className="chat-history">
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.role === 'assistant' && <div className="avatar">D</div>}
                  <div className="text" style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-content">
                  <div className="avatar">D</div>
                  <div className="text typing"><Loader2 className="spinner" size={16} /> Thinking...</div>
                </div>
              </div>
            )}
          </div>
          
          <form className="chat-input-form" onSubmit={handleSend}>
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about the data..."
              disabled={loading}
            />
            <button type="submit" disabled={loading || !query.trim()}>
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>

      {/* Main View for Graph */}
      <div className="main-content">
        {!sidebarOpen && (
          <button className="toggle-btn floating" onClick={() => setSidebarOpen(true)}>
            <Maximize2 size={18} />
          </button>
        )}
        <div className="graph-container">
          {graphData.nodes.length > 0 ? (
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              nodeLabel="label"
              nodeColor={node => getThemeColor(node.type)}
              linkColor={() => 'rgba(255,255,255,0.1)'}
              backgroundColor="#0f1115"
              nodeRelSize={4}
              linkDirectionalArrowLength={2}
              linkDirectionalArrowRelPos={1}
              onNodeClick={node => {
                // Center camera on node
                fgRef.current.centerAt(node.x, node.y, 1000);
                fgRef.current.zoom(8, 2000);
                
                // Show info in chat
                const info = Object.entries(node.data)
                  .filter(([k,v]) => typeof v !== 'object')
                  .map(([k,v]) => `${k}: ${v}`).join('\n');
                setChatHistory(prev => [...prev, { role: 'assistant', text: `Node Inspector (${node.type}):\n${info}` }]);
              }}
            />
          ) : (
            <div className="loading-graph">
              <Loader2 className="spinner large" />
              <p>Constructing Graph Representation...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
