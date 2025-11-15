import { useState, useEffect } from 'react';
import { DifficultySelection } from './components/DifficultySelection';
import { StoryScreen } from './components/StoryScreen';
import { GameBoard } from './components/GameBoard';
import { motion, AnimatePresence } from 'motion/react';

type GameState = 
  | 'loading_story' 
  | 'story_opening' 
  | 'difficulty_selection' 
  | 'bomb_placement' 
  | 'player_turn' 
  | 'loading_ending' 
  | 'story_ending';

type Difficulty = 'easy' | 'medium' | 'hard';

export default function App() {
  const [gameState, setGameState] = useState<GameState>('loading_story');
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  const [openingStory, setOpeningStory] = useState<string>('');
  const [endingStory, setEndingStory] = useState<string>('');
  const [missionData, setMissionData] = useState<{ player_item: string; ai_item: string } | null>(null);
  const [victor, setVictor] = useState<'Player' | 'AI' | null>(null);
  const [gridSize, setGridSize] = useState<number>(5);
  const [gameStartTime, setGameStartTime] = useState<number | null>(null);
  const [gameDuration, setGameDuration] = useState<number>(0);

  // Simulate loading opening story
  useEffect(() => {
    if (gameState === 'loading_story') {
      setTimeout(() => {
        // Mock story generation
        const mockStory = `YEAR 2147 >> HUMANITY'S LAST BASTION ONLINE >> AI COLLECTIVE DETECTED >> QUANTUM DISRUPTOR THREAT LEVEL: CRITICAL >> YOUR MISSION: LOCATE AND NEUTRALIZE ENEMY ARTIFACT BEFORE REALITY COLLAPSE >> PROTECT YOUR TEMPORAL BEACON >> SURVIVAL PROBABILITY: 32.7% >> GOOD LUCK, HUMAN.`;
        const mockData = { player_item: 'TEMPORAL_BEACON', ai_item: 'QUANTUM_DISRUPTOR' };
        setOpeningStory(mockStory);
        setMissionData(mockData);
        setGameState('story_opening');
      }, 2000);
    }
  }, [gameState]);

  const handleBeginMission = () => {
    setGameState('difficulty_selection');
  };

  const handleDifficultySelect = (selectedDifficulty: Difficulty) => {
    setDifficulty(selectedDifficulty);
    const size = selectedDifficulty === 'easy' ? 5 : selectedDifficulty === 'medium' ? 10 : 20;
    setGridSize(size);
    setGameStartTime(Date.now());
    setGameState('bomb_placement');
  };

  const handleGameEnd = (winner: 'Player' | 'AI') => {
    setVictor(winner);
    if (gameStartTime) {
      const duration = Math.floor((Date.now() - gameStartTime) / 1000);
      setGameDuration(duration);
    }
    setGameState('loading_ending');
    
    // Simulate loading ending story
    setTimeout(() => {
      const playerWon = winner === 'Player';
      const mockEnding = playerWon 
        ? `>> MISSION_STATUS: SUCCESS >> QUANTUM_DISRUPTOR NEUTRALIZED >> AI FORCES RETREATING >> TEMPORAL_BEACON SIGNAL STRENGTH: 100% >> TIMELINE SECURED >> HUMANITY SURVIVES THIS CYCLE >> CONGRATULATIONS, OPERATIVE >> NEW FUTURES UNLOCKED >> END TRANSMISSION`
        : `>> MISSION_STATUS: FAILED >> TEMPORAL_BEACON COMPROMISED >> AI VICTORY CONFIRMED >> REALITY FRAGMENTATION IN PROGRESS >> TIMELINE COLLAPSE IMMINENT >> QUANTUM ANALYSIS: NO ALTERNATIVE FUTURES DETECTED >> AI COLLECTIVE DOMINANCE: ABSOLUTE >> END TRANSMISSION`;
      setEndingStory(mockEnding);
      setGameState('story_ending');
    }, 2000);
  };

  const handleNewMission = () => {
    setGameState('loading_story');
    setDifficulty(null);
    setOpeningStory('');
    setEndingStory('');
    setMissionData(null);
    setVictor(null);
    setGridSize(5);
    setGameStartTime(null);
    setGameDuration(0);
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Scanline effect */}
      <div className="fixed inset-0 pointer-events-none bg-scanlines opacity-10 z-50" />
      
      {/* CRT effect */}
      <div className="fixed inset-0 pointer-events-none bg-gradient-to-b from-transparent via-cyan-500/5 to-transparent animate-crt z-40" />
      
      <AnimatePresence mode="wait">
        {gameState === 'loading_story' && (
          <StoryScreen 
            key="loading-opening"
            type="loading" 
            title=">> INITIALIZING MISSION DATA..."
            message=">> QUANTUM_PARAMETERS_LOADING..."
          />
        )}

        {gameState === 'story_opening' && (
          <StoryScreen
            key="opening"
            type="opening"
            title=">> MISSION_BRIEFING"
            story={openingStory}
            onContinue={handleBeginMission}
          />
        )}

        {gameState === 'difficulty_selection' && (
          <DifficultySelection 
            key="difficulty"
            onSelect={handleDifficultySelect} 
          />
        )}

        {(gameState === 'bomb_placement' || gameState === 'player_turn') && difficulty && missionData && gameStartTime && (
          <GameBoard
            key="game"
            gameState={gameState}
            setGameState={setGameState}
            difficulty={difficulty}
            gridSize={gridSize}
            missionData={missionData}
            onGameEnd={handleGameEnd}
            startTime={gameStartTime}
          />
        )}

        {gameState === 'loading_ending' && (
          <StoryScreen 
            key="loading-ending"
            type="loading" 
            title=">> ANALYZING MISSION OUTCOME..."
            message=">> TIMELINE_CONVERGENCE_PROCESSING..."
          />
        )}

        {gameState === 'story_ending' && (
          <StoryScreen
            key="ending"
            type="ending"
            title={victor === 'Player' ? '>> MISSION_SUCCESS' : '>> MISSION_FAILED'}
            story={endingStory}
            isVictory={victor === 'Player'}
            onNewMission={handleNewMission}
            duration={gameDuration}
          />
        )}
      </AnimatePresence>
    </div>
  );
}