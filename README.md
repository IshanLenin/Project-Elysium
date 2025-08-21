Project Elysium: The AI Storyteller
Live Demo: https://elysium.ishan-visionary.tech

(Suggestion: Replace this with a real screenshot of your application)

1. Overview
Project Elysium is a dynamic, AI-powered interactive storytelling game. It leverages a sophisticated chain of generative AI models to create a unique, illustrated text-based adventure in real-time. A user provides an initial prompt for a character and setting, and the application generates a branching narrative, complete with unique, AI-generated illustrations for each scene.

This project was built to explore the creative potential of chaining multiple AI models and to solve the engineering challenges of managing a real-time, stateful application.

2. Key Features
Dynamic Story Generation: Utilizes a Large Language Model (Google's Gemini) to act as a "Dungeon Master," creating a unique, branching narrative based on user choices.

Real-Time AI Illustrations: For each scene, a second AI pipeline generates a descriptive visual prompt, which is then fed to an image generation model (Stable Diffusion) to create a unique illustration.

Interactive, Real-Time Gameplay: A persistent WebSocket connection ensures a smooth, real-time experience, with new story segments and images pushed to the user's browser instantly.

Stateful Backend: The FastAPI backend maintains the entire story history for each session, providing the necessary context to the AI for generating a consistent and coherent narrative.

3. System Architecture
Project Elysium is built on a modern, asynchronous architecture designed to handle the slow, blocking nature of generative AI calls.

Frontend (The Storybook): A user starts a game from a simple web interface built with HTML, CSS, and JavaScript. This client opens a WebSocket connection to the backend.

Backend (The API Workshop): A FastAPI server manages the game logic.

It maintains a story_history for each active WebSocket connection.

When a user makes a choice, the backend sends a carefully engineered prompt, including the entire story history, to the text generation AI.

AI Chain (The Magic):

Text Generation (Gemini): The first AI model generates the next part of the story and two new choices.

Visual Prompt Generation (Gemini): The generated story text is immediately sent to a second AI prompt, which is tasked with creating a concise, descriptive prompt for an image model.

Image Generation (Stable Diffusion): This final visual prompt is sent to the Hugging Face Inference API to generate the scene's illustration.

Real-Time Push: The backend pushes the new story text and the generated image back to the frontend through the open WebSocket, instantly updating the user's view.

4. Tech Stack
Category

Technology

Backend

Python, FastAPI, WebSockets

Frontend

HTML, CSS, JavaScript

AI Models

Google Gemini (Text & Prompting), Stable Diffusion (Images)

API Libraries

requests, python-dotenv, Pillow

Deployment

Docker, Nginx, DigitalOcean, Certbot (SSL)

Dev Tools

Git, GitHub, VS Code, Postman

5. Local Setup and Installation
To run this project on your local machine, follow these steps:

Prerequisites:

Python 3.9+

A .env file in the root directory with your GEMINI_API_KEY and HUGGINGFACE_API_KEY.

1. Clone the Repository:

git clone https://github.com/IshanLenin/Project-Elysium.git
cd Project-Elysium

2. Install Dependencies:

pip install -r requirements.txt

3. Run the API Server:

uvicorn main:app --reload

The application will be available at http://127.0.0.1:8000.
