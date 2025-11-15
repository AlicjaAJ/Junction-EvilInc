import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface ChatSidebarProps {
  messages: { sender: 'player' | 'ai'; message: string }[];
  onSendMessage: (message: string) => void;
  isAiThinking: boolean;
  disabled?: boolean;
}

export function ChatSidebar({ messages, onSendMessage, isAiThinking, disabled }: ChatSidebarProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAiThinking]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isAiThinking && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-black border-4 border-cyan-500 shadow-[0_0_20px_rgba(0,255,255,0.5)] overflow-hidden relative">
      {/* Scanline effect */}
      <motion.div
        animate={{ y: ['0%', '100%'] }}
        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-500/10 to-transparent h-12 pointer-events-none z-10"
      />

      {/* Header */}
      <div className="px-4 py-3 bg-cyan-500 border-b-4 border-cyan-700">
        <div className="flex items-center gap-3">
          <div className="size-3 bg-black border-2 border-black" />
          <div>
            <h3 className="text-black pixel-text">AI_OPPONENT_CHAT</h3>
            <p className="text-black/70 pixel-text text-[10px]">
              {messages.length === 0 ? 'NO_MESSAGES' : `${Math.floor(messages.length / 2)}_EXCHANGES`}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-black">
        {messages.length === 0 && !disabled && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-green-400 pixel-text py-8 text-xs"
          >
            <div className="mb-4">◢◤◢◤◢◤</div>
            <p>CHAT_WITH_AI_OPPONENT</p>
            <p className="mt-2 text-[10px] text-cyan-400">
              REQUEST_HINTS_OR_DISCUSS_STRATEGY
            </p>
          </motion.div>
        )}

        {disabled && messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-cyan-700 pixel-text py-8 text-xs"
          >
            <p>CHAT_DISABLED_DURING_SETUP</p>
          </motion.div>
        )}

        <AnimatePresence mode="popLayout">
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: "spring", duration: 0.3 }}
              className={`flex ${msg.sender === 'player' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] px-3 py-2 border-4 ${
                  msg.sender === 'player'
                    ? 'bg-blue-500 border-blue-700 text-black'
                    : 'bg-red-500 border-red-700 text-black'
                }`}
              >
                <p className="pixel-text text-[10px] opacity-70 mb-1">
                  {msg.sender === 'player' ? '>> YOU' : '>> AI'}
                </p>
                <p className="pixel-text text-xs break-words">{msg.message}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isAiThinking && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="bg-red-500/50 border-4 border-red-700/50 px-3 py-2">
              <div className="flex items-center gap-2 text-black pixel-text text-xs">
                <motion.div
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                >
                  ▮
                </motion.div>
                <span>AI_PROCESSING...</span>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 bg-black border-t-4 border-cyan-700">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={disabled ? "DISABLED" : "TYPE_MESSAGE..."}
            disabled={isAiThinking || disabled}
            className="w-full px-3 py-2 pr-12 bg-black border-4 border-cyan-700 text-green-400 placeholder-cyan-700 pixel-text text-xs focus:outline-none focus:border-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
            maxLength={200}
          />
          <button
            type="submit"
            disabled={!input.trim() || isAiThinking || disabled}
            className="absolute right-1 top-1/2 -translate-y-1/2 px-3 py-1 bg-cyan-500 hover:bg-cyan-400 disabled:bg-cyan-900 disabled:cursor-not-allowed border-2 border-cyan-700 transition-all duration-200"
          >
            <span className="pixel-text text-black text-xs">►</span>
          </button>
        </div>
        <p className="pixel-text text-[10px] text-cyan-700 mt-1">
          {input.length}/200_CHARS
        </p>
      </form>
    </div>
  );
}