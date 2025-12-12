import React, { useState, useRef, useEffect } from 'react';
import { api } from '../services/api';

const RagQuery = () => {
  // State for the current input
  const [query, setQuery] = useState('');
  const [kbType, setKbType] = useState('gkb'); // Default to General Knowledge Base
  
  // State for the conversation history
  // Structure: { id: 1, role: 'user' | 'ai', content: string, sources?: array }
  const [chatHistory, setChatHistory] = useState([]);
  
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to the bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isLoading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    // 1. Add User Message immediately
    const userMessage = { 
      id: Date.now(), 
      role: 'user', 
      content: query 
    };
    
    setChatHistory(prev => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);

    try {
      // 2. Call the API
      // api.performQuery returns: { query, answer, retrieved_context }
      const data = await api.performQuery(userMessage.content, kbType);

      // 3. Add AI Response
      const aiMessage = {
        id: Date.now() + 1,
        role: 'ai',
        content: data.answer,
        sources: data.retrieved_context // Save context to display later
      };
      setChatHistory(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error("RAG Query Error:", error);
      // Add Error Message
      const errorMessage = {
        id: Date.now() + 1,
        role: 'ai',
        content: "Sorry, I encountered an error connecting to the knowledge base.",
        isError: true
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      
      {/* Header / Toolbar */}
      <div className="bg-indigo-600 p-4 flex justify-between items-center shadow-sm z-10">
        <h2 className="text-white font-semibold text-lg flex items-center gap-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
          AI Assistant
        </h2>
        
        {/* KB Type Selector */}
        <div className="flex items-center space-x-2">
          <label className="text-indigo-100 text-sm font-medium">Source:</label>
          <select
            value={kbType}
            onChange={(e) => setKbType(e.target.value)}
            className="bg-indigo-700 text-white text-sm rounded-md border-none focus:ring-2 focus:ring-white py-1 px-3 cursor-pointer"
          >
            <option value="gkb">General (GKB)</option>
            <option value="skb">Specific (SKB)</option>
          </select>
        </div>
      </div>

      {/* Chat Area (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {chatHistory.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-60">
            <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
            <p>Select a knowledge base and start asking questions.</p>
          </div>
        )}

        {chatHistory.map((msg) => (
          <div 
            key={msg.id} 
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div 
              className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-sm text-sm md:text-base leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-br-none' 
                  : msg.isError 
                    ? 'bg-red-50 text-red-800 border border-red-200'
                    : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
            
            {/* Source/Context Metadata (Only for AI) */}
            {msg.role === 'ai' && msg.sources && msg.sources.length > 0 && (
              <details className="mt-1 ml-2 max-w-[80%]">
                <summary className="text-xs text-gray-400 cursor-pointer hover:text-indigo-600 select-none flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  View Sources ({msg.sources.length})
                </summary>
                <div className="mt-2 bg-white p-2 rounded border border-gray-200 shadow-sm text-xs text-gray-600 space-y-2">
                  {msg.sources.map((src, idx) => (
                    <div key={idx} className="border-b last:border-0 pb-1 last:pb-0">
                      <span className="font-semibold text-gray-800">Match {idx + 1} (Score: {src.score.toFixed(2)}):</span>
                      <p className="truncate mt-1 italic">{JSON.stringify(src.metadata)}</p>
                    </div>
                  ))}
                </div>
              </details>
            )}
            
            <span className="text-[10px] text-gray-400 mt-1 px-1">
              {msg.role === 'user' ? 'You' : 'AI'}
            </span>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex items-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-none px-4 py-3 border border-gray-200 flex items-center space-x-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} className="bg-white p-4 border-t border-gray-100">
        <div className="flex gap-2">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              // Submit on Enter (without Shift)
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(e);
              }
            }}
            placeholder="Ask a question about your documents..."
            className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            rows="1"
            style={{ minHeight: '50px' }}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className={`px-6 rounded-lg font-medium text-white transition-colors flex items-center justify-center
              ${isLoading || !query.trim() 
                ? 'bg-gray-300 cursor-not-allowed' 
                : 'bg-indigo-600 hover:bg-indigo-700 shadow-md'
              }`}
          >
            <svg className="w-5 h-5 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
          </button>
        </div>
        <p className="text-xs text-center text-gray-400 mt-2">
          Press Enter to send, Shift + Enter for new line
        </p>
      </form>
    </div>
  );
};

export default RagQuery;