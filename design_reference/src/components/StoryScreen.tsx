import { motion } from 'motion/react';
import { Loader2, Zap, AlertCircle, Clock } from 'lucide-react';

interface StoryScreenProps {
  type: 'loading' | 'opening' | 'ending';
  title: string;
  story?: string;
  message?: string;
  isVictory?: boolean;
  onContinue?: () => void;
  onNewMission?: () => void;
  duration?: number;
}

export function StoryScreen({ 
  type, 
  title, 
  story, 
  message, 
  isVictory,
  onContinue,
  onNewMission,
  duration
}: StoryScreenProps) {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen flex items-center justify-center p-4 relative"
    >
      {/* Pixel grid background */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: 'linear-gradient(0deg, transparent 24%, rgba(0, 255, 255, .3) 25%, rgba(0, 255, 255, .3) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, .3) 75%, rgba(0, 255, 255, .3) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(0, 255, 255, .3) 25%, rgba(0, 255, 255, .3) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, .3) 75%, rgba(0, 255, 255, .3) 76%, transparent 77%, transparent)',
        backgroundSize: '50px 50px'
      }} />

      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: -20 }}
        transition={{ type: "spring", duration: 0.5 }}
        className="max-w-3xl w-full relative"
      >
        {/* Retro terminal window */}
        <div className="bg-black border-4 border-cyan-500 rounded-none shadow-[0_0_30px_rgba(0,255,255,0.5)] relative overflow-hidden">
          {/* Terminal header bar */}
          <div className="h-8 bg-cyan-500 border-b-4 border-cyan-700 flex items-center px-3 gap-2">
            <div className="size-3 bg-black border-2 border-black" />
            <div className="size-3 bg-black border-2 border-black" />
            <div className="size-3 bg-black border-2 border-black" />
            <span className="ml-2 text-black pixel-text text-xs">TERMINAL://MISSION_CONTROL</span>
          </div>

          {/* Header */}
          <div className={`px-8 py-6 border-b-4 ${
            type === 'ending' 
              ? isVictory 
                ? 'bg-green-500/20 border-green-500' 
                : 'bg-red-500/20 border-red-500'
              : 'bg-cyan-500/20 border-cyan-500'
          }`}>
            <div className="flex items-center justify-center gap-3">
              {type === 'loading' ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <div className="size-6 border-4 border-cyan-500 border-t-transparent" />
                </motion.div>
              ) : type === 'ending' && isVictory ? (
                <span className="text-2xl">✓</span>
              ) : type === 'ending' && !isVictory ? (
                <span className="text-2xl">✗</span>
              ) : (
                <span className="text-2xl">►</span>
              )}
              <h1 className={`pixel-text ${
                type === 'ending'
                  ? isVictory
                    ? 'text-green-400'
                    : 'text-red-400'
                  : 'text-cyan-400'
              }`}>
                {title}
              </h1>
            </div>
          </div>

          {/* Content */}
          <div className="px-8 py-10 bg-black">
            {type === 'loading' ? (
              <div className="text-center space-y-4">
                <div className="flex justify-center gap-2">
                  <motion.div
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                    className="size-4 bg-cyan-500"
                  />
                  <motion.div
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                    className="size-4 bg-cyan-500"
                  />
                  <motion.div
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                    className="size-4 bg-cyan-500"
                  />
                </div>
                <p className="text-cyan-400 pixel-text">{message}</p>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="space-y-4"
              >
                <p className="text-green-400 pixel-text leading-relaxed">
                  {story}
                </p>
                
                {/* Timer display */}
                {type === 'ending' && duration !== undefined && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 }}
                    className="pt-6 mt-6 border-t-4 border-cyan-500/30"
                  >
                    <div className="flex items-center justify-center gap-4 bg-cyan-500/10 border-4 border-cyan-500/30 p-4">
                      <Clock className="size-6 text-cyan-400" />
                      <div className="text-center">
                        <div className="text-cyan-400 pixel-text text-xs mb-1">MISSION DURATION</div>
                        <div className="text-cyan-400 pixel-text text-2xl">{formatTime(duration)}</div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}
          </div>

          {/* Actions */}
          {type !== 'loading' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="px-8 py-6 bg-black border-t-4 border-cyan-500/30"
            >
              {type === 'opening' ? (
                <button
                  onClick={onContinue}
                  className="w-full py-4 bg-cyan-500 hover:bg-cyan-400 text-black pixel-text border-4 border-cyan-700 hover:border-cyan-600 transition-all duration-200 relative overflow-hidden group"
                >
                  <span className="relative z-10">► BEGIN_MISSION</span>
                  <div className="absolute inset-0 bg-cyan-300 translate-y-full group-hover:translate-y-0 transition-transform duration-200" />
                </button>
              ) : (
                <div className="flex gap-4">
                  <button
                    onClick={onNewMission}
                    className="flex-1 py-4 bg-green-500 hover:bg-green-400 text-black pixel-text border-4 border-green-700 hover:border-green-600 transition-all duration-200 relative overflow-hidden group"
                  >
                    <span className="relative z-10">► NEW_MISSION</span>
                    <div className="absolute inset-0 bg-green-300 translate-y-full group-hover:translate-y-0 transition-transform duration-200" />
                  </button>
                  <button
                    onClick={() => window.location.reload()}
                    className="flex-1 py-4 bg-red-500 hover:bg-red-400 text-black pixel-text border-4 border-red-700 hover:border-red-600 transition-all duration-200 relative overflow-hidden group"
                  >
                    <span className="relative z-10">✗ QUIT</span>
                    <div className="absolute inset-0 bg-red-300 translate-y-full group-hover:translate-y-0 transition-transform duration-200" />
                  </button>
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Glitch effect overlay */}
        <motion.div
          animate={{ 
            opacity: [0, 0.5, 0],
            x: [0, 2, -2, 0]
          }}
          transition={{ 
            duration: 0.3,
            repeat: Infinity,
            repeatDelay: 3
          }}
          className="absolute inset-0 bg-cyan-500/10 pointer-events-none"
        />
      </motion.div>
    </motion.div>
  );
}