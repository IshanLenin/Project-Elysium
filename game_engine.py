import requests
import json
import os
import textwrap
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import time

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key="
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# The endpoint for the free Stable Diffusion model on Hugging Face
STABLE_DIFFUSION_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not found.")
if not HUGGINGFACE_API_KEY:
    print("WARNING: HUGGINGFACE_API_KEY environment variable not found.")

# --- Helper function to call the Gemini Text API ---
def call_gemini_api(prompt):
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(f"{GEMINI_API_URL}{GEMINI_API_KEY}", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        if data.get('candidates'):
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Error: The AI returned an unexpected text response."
    except requests.exceptions.RequestException as e:
        print(f"Text API Call Error: {e}")
        return "Error: Could not connect to the AI."

# --- Function to Generate a Visual Prompt ---
def generate_visual_prompt(story_text):
    print("...AI is creating a visual prompt...")
    prompt = (
        "You are an AI assistant that creates safe, simple, and concise image generation prompts. "
        "Based on the following fantasy story scene, create a very short, clean, descriptive prompt. "
        "It must be under 20 words. "
        "Style: beautiful digital art, fantasy, cinematic lighting. "
        f"Scene: '{story_text}'"
    )
    visual_prompt = call_gemini_api(prompt)
    cleaned_prompt = visual_prompt.replace('\n', ' ').replace('*', '').strip()
    print(f"Generated Visual Prompt: {cleaned_prompt}")
    return cleaned_prompt

# --- NEW Function to Generate an Image with Stable Diffusion ---
def generate_image_with_stable_diffusion(visual_prompt):
    if not HUGGINGFACE_API_KEY:
        print("Cannot generate image, Hugging Face API key is missing.")
        return None
        
    print("...AI is generating the illustration with Stable Diffusion...")
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": visual_prompt}
    
    try:
        response = requests.post(STABLE_DIFFUSION_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # The response is the raw image data
        return Image.open(BytesIO(response.content))

    except requests.exceptions.RequestException as e:
        print(f"Stable Diffusion image generation failed: {e}")
        if e.response:
            try:
                # The model might be loading, which is a common case
                error_data = e.response.json()
                if "error" in error_data and "estimated_time" in error_data:
                    wait_time = int(error_data["estimated_time"])
                    print(f"Model is loading, waiting for {wait_time} seconds and retrying...")
                    time.sleep(wait_time)
                    return generate_image_with_stable_diffusion(visual_prompt) # Retry once
            except:
                pass # If parsing fails, just print the raw text
            print(f"Error details: {e.response.text}")
        return None

# --- Main Game Loop ---
def main_game_loop():
    print("="*50)
    print("      Welcome to Project Elysium: The AI Storyteller")
    print("="*50)
    
    user_idea = input("Enter your character and setting (e.g., 'a knight in a haunted forest'):\n> ")
    story_history = [f"The user's character is {user_idea}."]
    scene_counter = 0
    
    initial_prompt = (
        "You are a text adventure game's Dungeon Master. "
        f"The user's character and setting is: '{user_idea}'. "
        "Describe the opening scene in a vivid, engaging style. "
        "End your response by giving the user two clear choices, labeled A and B."
    )
    
    print("\n...AI is thinking...")
    scene_text = call_gemini_api(initial_prompt)
    story_history.append(f"AI Scene: {scene_text}")
    
    visual_prompt = generate_visual_prompt(scene_text)
    image = generate_image_with_stable_diffusion(visual_prompt)
    if image:
        scene_counter += 1
        image_path = f"scene_{scene_counter}.png"
        image.save(image_path)
        print(f"Illustration saved to {image_path}")
    
    while True:
        print("\n" + "="*50 + "\n")
        print(textwrap.fill(scene_text, width=80))
        print("\n" + "="*50)
        
        user_choice = input("What do you do? (Type A or B, or 'quit' to exit)\n> ").upper()
        
        if user_choice == 'QUIT':
            print("\nThanks for playing!")
            break
        
        if user_choice not in ['A', 'B']:
            print("\nInvalid choice. Please enter A or B.")
            continue
            
        story_history.append(f"User chose: {user_choice}")
        
        next_prompt = (
            "You are a text adventure game's Dungeon Master. Continue the story based on the user's last choice. "
            "Describe the outcome and the new scene. Keep it consistent and engaging. "
            "End with two new, clear choices, labeled A and B. "
            f"Here is the story so far:\n{' '.join(story_history)}"
        )
        
        print("\n...AI is thinking...")
        scene_text = call_gemini_api(next_prompt)
        story_history.append(f"AI Scene: {scene_text}")
        
        visual_prompt = generate_visual_prompt(scene_text)
        image = generate_image_with_stable_diffusion(visual_prompt)
        if image:
            scene_counter += 1
            image_path = f"scene_{scene_counter}.png"
            image.save(image_path)
            print(f"Illustration saved to {image_path}")

if __name__ == "__main__":
    main_game_loop()
