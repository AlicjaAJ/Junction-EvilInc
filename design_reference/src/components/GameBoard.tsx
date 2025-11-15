import { useState, useEffect } from 'react';
import { Grid } from './Grid';
import { ChatSidebar } from './ChatSidebar';
import { motion } from 'motion/react';
import { Clock } from 'lucide-react';

interface GameBoardProps {
  gameState: 'bomb_placement' | 'player_turn';
  setGameState: (state: 'bomb_placement' | 'player_turn') => void;
  difficulty: 'easy' | 'medium' | 'hard';
  gridSize: number;
  missionData: { player_item: string; ai_item: string };
  onGameEnd: (winner: 'Player' | 'AI') => void;
  startTime: number;
}

export type CellState = {
  revealed: boolean;
  revealedBy: 'player' | 'ai' | null;
  hasBomb: boolean;
  bombOwner: 'player' | 'ai' | null;
};

export function GameBoard({ 
  gameState, 
  setGameState,
  difficulty, 
  gridSize, 
  missionData,
  onGameEnd,
  startTime
}: GameBoardProps) {
  const [cells, setCells] = useState<CellState[][]>([]);
  const [playerBombPos, setPlayerBombPos] = useState<{ row: number; col: number } | null>(null);
  const [aiBombPos, setAiBombPos] = useState<{ row: number; col: number } | null>(null);
  const [isPlayerTurn, setIsPlayerTurn] = useState(true);
  const [chatMessages, setChatMessages] = useState<{ sender: 'player' | 'ai'; message: string }[]>([]);
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Initialize grid
  useEffect(() => {
    const newCells: CellState[][] = [];
    for (let row = 0; row < gridSize; row++) {
      const rowCells: CellState[] = [];
      for (let col = 0; col < gridSize; col++) {
        rowCells.push({
          revealed: false,
          revealedBy: null,
          hasBomb: false,
          bombOwner: null,
        });
      }
      newCells.push(rowCells);
    }
    setCells(newCells);
  }, [gridSize]);

  // Timer
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleCellClick = (row: number, col: number) => {
    if (gameState === 'bomb_placement' && !playerBombPos) {
      // Player places their bomb
      const newCells = [...cells];
      newCells[row][col].hasBomb = true;
      newCells[row][col].bombOwner = 'player';
      setCells(newCells);
      setPlayerBombPos({ row, col });

      // AI places bomb randomly
      let aiRow, aiCol;
      do {
        aiRow = Math.floor(Math.random() * gridSize);
        aiCol = Math.floor(Math.random() * gridSize);
      } while (aiRow === row && aiCol === col);

      newCells[aiRow][aiCol].hasBomb = true;
      newCells[aiRow][aiCol].bombOwner = 'ai';
      setAiBombPos({ row: aiRow, col: aiCol });

      // Transition to game
      setGameState('player_turn');
      setChatMessages([{
        sender: 'ai',
        message: `YOUR ${missionData.player_item} IS SECURED. NOW LET'S SEE IF YOU CAN FIND MY ${missionData.ai_item}...`
      }]);
    } else if (gameState === 'player_turn' && isPlayerTurn) {
      // Player reveals a cell
      if (cells[row][col].revealed) return;

      const newCells = [...cells];
      newCells[row][col].revealed = true;
      newCells[row][col].revealedBy = 'player';
      setCells(newCells);

      // Check if player found AI's bomb
      if (newCells[row][col].hasBomb && newCells[row][col].bombOwner === 'ai') {
        setTimeout(() => onGameEnd('Player'), 500);
        return;
      }

      // Switch to AI turn
      setIsPlayerTurn(false);
      
      // AI takes turn after delay
      setTimeout(() => {
        aiTakeTurn(newCells);
      }, 1000);
    }
  };

  const aiTakeTurn = (currentCells: CellState[][]) => {
    // AI reveals a random unrevealed cell
    const unrevealed: { row: number; col: number }[] = [];
    for (let row = 0; row < gridSize; row++) {
      for (let col = 0; col < gridSize; col++) {
        if (!currentCells[row][col].revealed) {
          unrevealed.push({ row, col });
        }
      }
    }

    if (unrevealed.length === 0) return;

    const target = unrevealed[Math.floor(Math.random() * unrevealed.length)];
    const newCells = [...currentCells];
    newCells[target.row][target.col].revealed = true;
    newCells[target.row][target.col].revealedBy = 'ai';
    setCells(newCells);

    // Check if AI found player's bomb
    if (newCells[target.row][target.col].hasBomb && newCells[target.row][target.col].bombOwner === 'player') {
      setTimeout(() => onGameEnd('AI'), 500);
      return;
    }

    // Switch back to player
    setIsPlayerTurn(true);
  };

  const handleSendMessage = (message: string) => {
    setChatMessages([...chatMessages, { sender: 'player', message }]);
    
    // Simulate AI response
    setIsAiThinking(true);
    setTimeout(() => {
      const responses = [
        "YOUR TACTICS ARE PREDICTABLE, HUMAN.",
        "INTERESTING MOVE. BUT FUTILE.",
        "LOGIC WILL PREVAIL OVER EMOTION.",
        "I CALCULATE YOUR DEFEAT IS INEVITABLE.",
        `THE ${missionData.ai_item} IS WELL HIDDEN. YOU'LL NEVER FIND IT.`,
        "EVERY MOVE BRINGS YOU CLOSER TO FAILURE.",
      ];
      const aiResponse = responses[Math.floor(Math.random() * responses.length)];
      setChatMessages(prev => [...prev, { sender: 'ai', message: aiResponse }]);
      setIsAiThinking(false);
    }, 1500);
  };

  const getPromptText = () => {
    if (gameState === 'bomb_placement') {
      return `>> HIDE_YOUR_${missionData.player_item}`;
    }
    if (isPlayerTurn) {
      return `>> FIND_THE_${missionData.ai_item}`;
    }
    return ">> AI_PROCESSING...";
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen flex items-center justify-center p-4 lg:p-8 relative"
    >
      {/* Pixel grid background */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: 'linear-gradient(0deg, transparent 24%, rgba(0, 255, 255, .3) 25%, rgba(0, 255, 255, .3) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, .3) 75%, rgba(0, 255, 255, .3) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(0, 255, 255, .3) 25%, rgba(0, 255, 255, .3) 26%, transparent 27%, transparent 74%, rgba(0, 255, 255, .3) 75%, rgba(0, 255, 255, .3) 76%, transparent 77%, transparent)',
        backgroundSize: '50px 50px'
      }} />

      <div className="w-full max-w-7xl">
        {/* Header with Prompt and Timer */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-6 bg-black border-4 border-cyan-500 p-4 shadow-[0_0_20px_rgba(0,255,255,0.5)]"
        >
          <div>
            <h2 className="text-cyan-400 pixel-text">{getPromptText()}</h2>
            {!isPlayerTurn && (
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-green-400 pixel-text text-sm mt-1"
              >
                PROCESSING_TACTICAL_ANALYSIS...
              </motion.p>
            )}
          </div>
          
          {/* Real-time timer */}
          <div className="flex items-center gap-3 bg-cyan-500/10 border-4 border-cyan-500/30 px-4 py-2">
            <Clock className="size-5 text-cyan-400" />
            <div className="text-center">
              <div className="text-cyan-400 pixel-text text-xs">TIME</div>
              <div className="text-cyan-400 pixel-text text-xl">{formatTime(elapsedTime)}</div>
            </div>
          </div>
        </motion.div>

        {/* Game Area */}
        <div className="grid lg:grid-cols-[1fr_400px] gap-6">
          {/* Grid */}
          <div className="flex items-center justify-center">
            <Grid
              cells={cells}
              gridSize={gridSize}
              onCellClick={handleCellClick}
              isPlayerTurn={isPlayerTurn}
              gameState={gameState}
            />
          </div>

          {/* Chat Sidebar */}
          <div className="lg:block hidden">
            <ChatSidebar
              messages={chatMessages}
              onSendMessage={handleSendMessage}
              isAiThinking={isAiThinking}
              disabled={gameState === 'bomb_placement'}
            />
          </div>
        </div>

        {/* Mobile Chat - Below grid */}
        <div className="lg:hidden mt-6">
          <ChatSidebar
            messages={chatMessages}
            onSendMessage={handleSendMessage}
            isAiThinking={isAiThinking}
            disabled={gameState === 'bomb_placement'}
          />
        </div>
      </div>
    </motion.div>
  );
}