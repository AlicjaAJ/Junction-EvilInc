# Presentation Slide Content

## Game Summary (3-5 Bullet Points)

• **Dynamic Narrative Experience**: Every playthrough features a unique, AI-generated mission briefing and outcome story set in a dystopian AI vs Humanity conflict—no two games tell the same story

• **Intelligent AI Opponent**: Face an LLM-powered opponent with distinct personalities (honest, deceptive, or unpredictable) that adapts its strategy and dialogue based on the mission context

• **Strategic Gameplay Loop**: Hide your beacon, find the AI's artifact, and engage in real-time chat to gather information—but beware, the AI can lie based on its personality

• **Time-Pressured Challenge**: Race against the clock with limited attempts across three difficulty levels (5x5 to 15x15 grids), creating tension between exploration and strategic decision-making

• **Outcome-Driven Storytelling**: Your victory or defeat shapes a dynamically generated ending narrative, making each game session feel like a unique mission with real consequences

---

## Technical Implementation (3-5 Bullet Points)

• **Multi-Model LLM Architecture**: Leverages Google Gemini API with intelligent fallback chains (gemini-2.0-flash-exp → gemini-2.0-flash-lite) for reliable story generation and AI opponent responses

• **Asynchronous Content Generation**: Background threading for story and image generation prevents UI blocking, ensuring smooth gameplay while AI creates narrative content in real-time

• **Personality-Driven AI System**: The opponent AI maintains game state memory, contextual awareness from mission briefings, and personality-specific response logic that shapes its strategic behavior

• **Modular Architecture**: Clean separation between story generation, opponent AI, game logic, and rendering systems enables maintainable code and easy feature extension

• **Dynamic Image Generation**: Integrates Gemini image models and Vertex AI Imagen for cyberpunk-themed mission visuals, with graceful fallbacks to procedural placeholder graphics

---

## Relevance to Junction 2025 Challenge (3-5 Bullet Points)

• **AI as Core Gameplay Mechanic**: The game fundamentally cannot exist without AI—the opponent's personality, strategic decisions, and dialogue are all LLM-generated, creating unpredictable and emergent gameplay

• **Generative Storytelling**: Every mission briefing and ending is uniquely crafted by AI, ensuring no two playthroughs are identical—the narrative adapts to game outcomes and creates personalized experiences

• **AI-Powered Opponent Intelligence**: Unlike scripted NPCs, the AI opponent reasons about game state, maintains context from conversations, and makes strategic decisions using LLM capabilities, creating a truly intelligent adversary

• **Emergent Player-AI Interaction**: The chat system enables natural language dialogue where players must interpret the AI's responses based on its personality—creating a meta-game of trust, deception, and psychological strategy

• **Technical Innovation**: Demonstrates production-ready integration of multiple AI models (text generation, image generation, conversational AI) working together to create a cohesive, AI-native gaming experience

