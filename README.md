AI Image Generator with 3D Conversion
Watch the demo: https://youtu.be/ALRGYINNx1k

What It Does
Transform text prompts into AI-generated images and interactive 3D models — all in your browser!
Type "a futuristic cyberpunk city" → Get a stunning DALL-E 3 image → Convert it to a 3D model → Explore it with Three.js

Architecture
Simple 3-step pipeline:

Text → Image (DALL-E 3) - 10-15 seconds
Image → 3D Model (Meshy AI) - 2-3 minutes
View in Browser (Three.js) - Interactive rotation, zoom, pan

Tech stack: Flask backend + Vanilla JS frontend + OpenAI + Meshy AI

How It's Processed
User Input → Flask API → DALL-E 3 → PNG saved locally → 
User clicks "Convert" → Meshy AI (base64 upload) → 
Polls every 5s → GLB model downloaded → Three.js viewer
All files stored locally, no database needed for MVP.

Future Improvements
Next up:
User authentication & personal galleries
PostgreSQL database for history
Batch generation (multiple images at once)
Prompt templates & suggestions
Mobile app with AR model viewing

Long-term:

Animation support for 3D models
Video generation from image sequences
Social sharing & public gallery

Built with: Python • Flask • JavaScript • DALL-E 3 • Meshy AI • Three.js
