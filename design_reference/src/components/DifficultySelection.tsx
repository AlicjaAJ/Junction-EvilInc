import { motion } from 'motion/react';
import { Target, Zap, Flame } from 'lucide-react';

interface DifficultySelectionProps {
  onSelect: (difficulty: 'easy' | 'medium' | 'hard') => void;
}

const difficulties = [
  {
    id: 'easy',
    name: 'EASY_MODE',
    description: '5x5 GRID >> NOVICE_OPERATIVE',
    icon: '◆',
    color: 'bg-green-500',
    hoverColor: 'hover:bg-green-400',
    borderColor: 'border-green-700',
  },
  {
    id: 'medium',
    name: 'MEDIUM_MODE',
    description: '10x10 GRID >> TRAINED_AGENT',
    icon: '◆◆',
    color: 'bg-yellow-500',
    hoverColor: 'hover:bg-yellow-400',
    borderColor: 'border-yellow-700',
  },
  {
    id: 'hard',
    name: 'HARD_MODE',
    description: '20x20 GRID >> ELITE_COMMANDER',
    icon: '◆◆◆',
    color: 'bg-red-500',
    hoverColor: 'hover:bg-red-400',
    borderColor: 'border-red-700',
  },
] as const;

export function DifficultySelection({ onSelect }: DifficultySelectionProps) {
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
        transition={{ type: "spring", duration: 0.5 }}
        className="max-w-2xl w-full"
      >
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-center mb-8"
        >
          <h1 className="text-cyan-400 pixel-text mb-2">{'>> SELECT_DIFFICULTY'}</h1>
          <p className="text-green-400 pixel-text text-sm">CHOOSE_BATTLEFIELD_PARAMETERS</p>
        </motion.div>

        {/* Difficulty Cards */}
        <div className="space-y-4">
          {difficulties.map((diff, index) => (
            <motion.button
              key={diff.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * index }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onSelect(diff.id as 'easy' | 'medium' | 'hard')}
              className={`w-full p-6 bg-black border-4 ${diff.borderColor} transition-all duration-200 shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.6)] relative overflow-hidden group`}
            >
              {/* Scan line animation */}
              <motion.div
                animate={{ y: ['0%', '100%'] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-500/10 to-transparent h-8 pointer-events-none"
              />

              <div className="flex items-center gap-6 relative z-10">
                {/* Icon */}
                <div className={`p-4 ${diff.color} border-4 ${diff.borderColor} min-w-[80px] flex items-center justify-center`}>
                  <span className="text-black pixel-text text-2xl">{diff.icon}</span>
                </div>

                {/* Info */}
                <div className="flex-1 text-left">
                  <h3 className="text-cyan-400 pixel-text mb-1">{diff.name}</h3>
                  <p className="text-green-400 pixel-text text-sm">{diff.description}</p>
                </div>

                {/* Arrow */}
                <motion.div
                  animate={{ x: [0, 10, 0] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  className="text-cyan-400 pixel-text text-2xl"
                >
                  ►
                </motion.div>
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}