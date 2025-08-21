import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import requests
import json
from PIL import Image
from io import BytesIO
import base64

# Load environment variables
load_dotenv()

# --- Configuration ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key="
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
STABLE_DIFFUSION_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

# --- Initialize FastAPI App ---
app = FastAPI(
    title="Project Elysium API",
    description="An AI-powered interactive storytelling game."
)

# --- Core AI Functions ---

async def call_gemini_api_async(prompt):  # Call Gemini API asynchronously
    loop = asyncio.get_event_loop()  # Get the current event loop
    return await loop.run_in_executor(None, call_gemini_api, prompt) 

def call_gemini_api(prompt):  # Call Gemini API
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(f"{GEMINI_API_URL}{GEMINI_API_KEY}", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        if data.get('candidates'):  # Check if there are any candidates
            return data['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        print(f"Text API Call Error: {e}")
    return "Error: The AI storyteller is currently unavailable."

async def generate_visual_prompt_async(story_text):  # Generate visual prompt asynchronously
    prompt = (
        "You are an AI assistant creating image prompts. Based on the following scene, "
        "create a short, descriptive prompt under 20 words. "
        "Style: beautiful digital art, fantasy, cinematic lighting. "
        f"Scene: '{story_text}'"
    )
    visual_prompt = await call_gemini_api_async(prompt)  # Call Gemini API asynchronously
    return visual_prompt.replace('\n', ' ').replace('*', '').strip()  # Clean up the visual prompt

async def generate_image_async(visual_prompt):
    loop = asyncio.get_event_loop() 
    return await loop.run_in_executor(None, generate_image_with_stable_diffusion, visual_prompt) 

def generate_image_with_stable_diffusion(visual_prompt):
    if not HUGGINGFACE_API_KEY: return None
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": visual_prompt}
    try:
        response = requests.post(STABLE_DIFFUSION_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Check for HTTP errors
        image = Image.open(BytesIO(response.content))  # Open the image
        buffered = BytesIO()  # Create a buffer
        image.save(buffered, format="PNG")  # Save the image to the buffer
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")  # Encode the image to base64
        return img_str
    except requests.exceptions.RequestException as e:
        print(f"Image generation failed: {e}")
    return None

# --- WebSocket Logic ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []  # List of active WebSocket connections

    async def connect(self, websocket: WebSocket):
        await websocket.accept()  # Wait for the client to connect
        self.active_connections.append(websocket)  # Add the new connection

    def disconnect(self, websocket: WebSocket):  # Remove the connection
        self.active_connections.remove(websocket) 

manager = ConnectionManager()  # Manage WebSocket connections

@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)  # Accept the WebSocket connection
    story_history = []  # Keep track of the story progression
    try:
        initial_data = await websocket.receive_json()  # Receive initial data from the client
        user_idea = initial_data.get("idea", "a brave adventurer in a mysterious land")  # Get user idea
        story_history.append(f"The user's character is {user_idea}.") 

        # --- INITIAL PROMPT ---
        initial_prompt = (
            "You are a text adventure game's Dungeon Master. "
            f"The user's character and setting is: '{user_idea}'. "
            "Describe the opening scene vividly. "
            "Your response MUST end with two clear choices for the user, formatted exactly as 'A) [Choice text]' and 'B) [Choice text]' on separate lines."
        )
        
        scene_text = await call_gemini_api_async(initial_prompt)
        story_history.append(f"AI Scene: {scene_text}")
        
        await websocket.send_json({"type": "story", "text": scene_text})
        
        visual_prompt = await generate_visual_prompt_async(scene_text)
        image_b64 = await generate_image_async(visual_prompt)
        if image_b64:
            await websocket.send_json({"type": "image", "data": image_b64})

        while True:
            data = await websocket.receive_json()
            user_choice = data.get("choice")
            
            if user_choice not in ['A', 'B']: continue
                
            story_history.append(f"User chose: {user_choice}")
            
            # --- UPDATED PROMPT ---
            next_prompt = (
                "You are a text adventure game's Dungeon Master. Continue the story based on the user's last choice. "
                "Describe the outcome and the new scene. Keep the story consistent. "
                "Your response MUST end with two new, clear choices, formatted exactly as 'A) [Choice text]' and 'B) [Choice text]' on separate lines. "
                f"Here is the story so far:\n{' '.join(story_history)}"
            )
            
            scene_text = await call_gemini_api_async(next_prompt)
            story_history.append(f"AI Scene: {scene_text}")
            
            await websocket.send_json({"type": "story", "text": scene_text})
            
            visual_prompt = await generate_visual_prompt_async(scene_text)
            image_b64 = await generate_image_async(visual_prompt)
            if image_b64:
                await websocket.send_json({"type": "image", "data": image_b64})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected.")

# --- Serve the frontend ---

app.mount("/static", StaticFiles(directory="static"), name="static")  # Serve static files

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')  # Serve the main HTML file
