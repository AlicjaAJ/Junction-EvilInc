import { motion } from 'motion/react';
import type { CellState } from './GameBoard';

interface GridProps {
  cells: CellState[][];
  gridSize: number;
  onCellClick: (row: number, col: number) => void;
  isPlayerTurn: boolean;
  gameState: 'bomb_placement' | 'player_turn';
}

export function Grid({ cells, gridSize, onCellClick, isPlayerTurn, gameState }: GridProps) {
  const getCellColor = (cell: CellState) => {
    if (!cell.revealed) {
      return 'bg-black border-cyan-700';
    }
    
    // Bomb found (winning cell)
    if (cell.hasBomb) {
      return 'bg-green-500 border-green-700 animate-pulse';
    }
    
    // Player revealed
    if (cell.revealedBy === 'player') {
      return 'bg-blue-500/40 border-blue-600';
    }
    
    // AI revealed
    return 'bg-red-500/40 border-red-600';
  };

  const getCellSize = () => {
    if (gridSize <= 5) return 'size-20';
    if (gridSize <= 10) return 'size-12';
    return 'size-8';
  };

  const getFontSize = () => {
    if (gridSize <= 5) return 'text-[10px]';
    if (gridSize <= 10) return 'text-[8px]';
    return 'text-[6px]';
  };

  const getBombSize = () => {
    if (gridSize <= 5) return 'text-2xl';
    if (gridSize <= 10) return 'text-lg';
    return 'text-xs';
  };

  const getGridNumber = (row: number, col: number) => {
    return row * gridSize + col + 1;
  };

  return (
    <div className="inline-block p-2 bg-black border-4 border-cyan-500 shadow-[0_0_30px_rgba(0,255,255,0.5)] relative">
      {/* Scanline effect */}
      <motion.div
        animate={{ y: ['0%', '100%'] }}
        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-500/10 to-transparent h-12 pointer-events-none z-10"
      />

      <div 
        className="grid gap-[2px] relative"
        style={{ 
          gridTemplateColumns: `repeat(${gridSize}, minmax(0, 1fr))`,
        }}
      >
        {cells.map((row, rowIndex) =>
          row.map((cell, colIndex) => {
            const gridNumber = getGridNumber(rowIndex, colIndex);
            const isClickable = gameState === 'bomb_placement' || (isPlayerTurn && !cell.revealed);
            
            return (
              <motion.button
                key={`${rowIndex}-${colIndex}`}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: (rowIndex * gridSize + colIndex) * 0.003 }}
                whileHover={isClickable ? { scale: 1.15, zIndex: 20 } : {}}
                whileTap={isClickable ? { scale: 0.9 } : {}}
                onClick={() => onCellClick(rowIndex, colIndex)}
                disabled={!isClickable}
                className={`
                  ${getCellSize()}
                  ${getCellColor(cell)}
                  border-4
                  relative
                  transition-all duration-100
                  ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed'}
                  flex items-center justify-center
                  group
                `}
              >
                {/* Grid Number */}
                {!cell.revealed && (
                  <span className={`absolute top-0.5 left-0.5 text-cyan-700 pixel-text ${getFontSize()}`}>
                    {gridNumber}
                  </span>
                )}

                {/* Bomb Indicator */}
                {cell.revealed && cell.hasBomb && (
                  <motion.span
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ type: "spring", duration: 0.5 }}
                    className={`${getBombSize()} pixel-text`}
                  >
                    {cell.bombOwner === 'player' ? '●' : '■'}
                  </motion.span>
                )}

                {/* Hover effect for unrevealed cells */}
                {!cell.revealed && isClickable && (
                  <div className="absolute inset-0 bg-cyan-500/0 group-hover:bg-cyan-500/30 transition-colors duration-200 border-2 border-transparent group-hover:border-cyan-400" />
                )}

                {/* Pixel corner decoration */}
                {!cell.revealed && (
                  <>
                    <div className="absolute top-0 left-0 size-1 bg-cyan-700" />
                    <div className="absolute top-0 right-0 size-1 bg-cyan-700" />
                    <div className="absolute bottom-0 left-0 size-1 bg-cyan-700" />
                    <div className="absolute bottom-0 right-0 size-1 bg-cyan-700" />
                  </>
                )}
              </motion.button>
            );
          })
        )}
      </div>
    </div>
  );
}