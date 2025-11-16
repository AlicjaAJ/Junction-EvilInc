"""
Image Generator Module

Generates cyberpunk-themed images for mission briefing and outcome screens.
Uses Google AI Studio API (Gemini) or Vertex AI Imagen for image generation.
"""

import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Google Cloud Configuration
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def generate_mission_image(story_text, image_type="briefing"):
    """
    Generate a cyberpunk-themed image based on the story text.
    Uses Gemini Flash via Google AI Studio if available, otherwise tries Vertex AI Imagen.
    
    Args:
        story_text: The story text to base the image on
        image_type: "briefing" for opening story, "outcome" for ending story
    
    Returns:
        PIL Image object or None if generation fails
    """
    # Try Gemini Flash via Google AI Studio first if API key is available
    if GEMINI_API_KEY and not USE_VERTEX_AI:
        return _generate_with_gemini(story_text, image_type)
    
    # Try Vertex AI Imagen if configured
    if USE_VERTEX_AI and PROJECT_ID:
        return _generate_with_imagen(story_text, image_type)
    
    # Fallback to enhanced placeholder
    return None


def _generate_with_gemini(story_text, image_type="briefing"):
    """
    Generate image using Gemini Flash Image model via Google AI Studio REST API.
    
    Args:
        story_text: The story text to base the image on
        image_type: "briefing" for opening story, "outcome" for ending story
    
    Returns:
        PIL Image object or None if generation fails
    """
    if not GEMINI_API_KEY:
        return None
    
    try:
        import requests
        import base64
        from PIL import Image
        import random
        
        # Create a prompt for image generation
        if image_type == "briefing":
            prompt = f"""Create a cyberpunk anime-style poster illustration depicting: {story_text[:200]}
            
Style: Retro-futuristic cyberpunk aesthetic, animated character art style, neon colors (cyan, purple, green), 
dark backgrounds, glowing effects, terminal/CRT screen aesthetic, dramatic lighting, action-oriented composition.
The image should show animated-looking characters in a cyberpunk setting."""
        else:  # outcome
            prompt = f"""Create a cyberpunk anime-style poster illustration depicting the mission outcome: {story_text[:200]}
            
Style: Retro-futuristic cyberpunk aesthetic, animated character art style, neon colors (cyan, purple, red/green based on outcome), 
dark backgrounds, glowing effects, terminal/CRT screen aesthetic, dramatic lighting, cinematic composition.
The image should show animated-looking characters in a cyberpunk setting representing the mission result."""
        
        # Gemini image-capable model endpoints (include higher-quota preview)
        gemini_image_models = [
            "gemini-2.0-flash-preview-image-generation",  # recommended for higher quota
            "gemini-2.5-flash-image",
            "gemini-2.0-flash-exp",
        ]
        random.shuffle(gemini_image_models)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Try without response_mime_type first - the model might handle it differently
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        for model_name in gemini_image_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract image from response
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "inlineData" in part:
                                image_data_b64 = part["inlineData"]["data"]
                                image_data = base64.b64decode(image_data_b64)
                                return Image.open(BytesIO(image_data))
                            elif "data" in part:
                                # Try direct data
                                image_data = part["data"]
                                if isinstance(image_data, str):
                                    image_data = base64.b64decode(image_data)
                                return Image.open(BytesIO(image_data))
            else:
                print(f"Gemini API error ({model_name}): {response.status_code} - {response.text}")
        
        return None
    except Exception as e:
        print(f"Error generating image with Gemini: {e}")
        import traceback
        traceback.print_exc()
        return None


def _generate_with_imagen(story_text, image_type="briefing"):
    """
    Generate image using Vertex AI Imagen API.
    
    Args:
        story_text: The story text to base the image on
        image_type: "briefing" for opening story, "outcome" for ending story
    
    Returns:
        PIL Image object or None if generation fails
    """
    if not PROJECT_ID:
        return None
    
    try:
        from google.cloud import aiplatform
        from vertexai.preview import vision_models
        
        # Initialize Vertex AI
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        
        # Create a prompt for image generation
        if image_type == "briefing":
            prompt = f"""Create a cyberpunk anime-style poster illustration depicting: {story_text[:200]}
            
Style: Retro-futuristic cyberpunk aesthetic, animated character art style, neon colors (cyan, purple, green), 
dark backgrounds, glowing effects, terminal/CRT screen aesthetic, dramatic lighting, action-oriented composition.
The image should show animated-looking characters in a cyberpunk setting."""
        else:  # outcome
            prompt = f"""Create a cyberpunk anime-style poster illustration depicting the mission outcome: {story_text[:200]}
            
Style: Retro-futuristic cyberpunk aesthetic, animated character art style, neon colors (cyan, purple, red/green based on outcome), 
dark backgrounds, glowing effects, terminal/CRT screen aesthetic, dramatic lighting, cinematic composition.
The image should show animated-looking characters in a cyberpunk setting representing the mission result."""
        
        # Use Imagen 3 API (imagegeneration@006)
        model = vision_models.ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Generate image
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_some",
            person_generation="allow_all",
        )
        
        if response and len(response.images) > 0:
            # Get the first generated image
            generated_image = response.images[0]
            
            # Convert to PIL Image
            from PIL import Image
            
            # Imagen returns images - access the image bytes
            if hasattr(generated_image, '_image_bytes'):
                image_bytes = generated_image._image_bytes
            elif hasattr(generated_image, 'image_bytes'):
                image_bytes = generated_image.image_bytes
            elif hasattr(generated_image, '_raw_response'):
                image_bytes = generated_image._raw_response
            else:
                # Try accessing via gcs_uri if available
                if hasattr(generated_image, 'gcs_uri'):
                    import requests
                    # Download from GCS URI (would need proper auth)
                    print("Image available at GCS URI, but direct download not implemented")
                    return None
                return None
            
            if image_bytes:
                return Image.open(BytesIO(image_bytes))
        
        return None
    except ImportError:
        print("Google Cloud Vertex AI not available. Install: pip install google-cloud-aiplatform")
        return None
    except Exception as e:
        print(f"Error generating image with Imagen: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_mission_image_simple(story_text, image_type="briefing"):
    """
    Fallback: Generate a cyberpunk-themed placeholder image with character-like shapes.
    Creates a stylized poster-like image with geometric character representations.
    
    Args:
        story_text: The story text (not used in fallback)
        image_type: "briefing" or "outcome"
    
    Returns:
        PIL Image object
    """
    from PIL import Image, ImageDraw
    
    # Create a placeholder image
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(img)
    
    # Draw cyberpunk-style placeholder with character-like shapes
    if image_type == "briefing":
        primary_color = (6, 182, 212)  # CYAN_500
        accent_color = (34, 211, 238)  # CYAN_400
        text = "MISSION BRIEFING"
    else:
        primary_color = (239, 68, 68)  # RED_500
        accent_color = (248, 113, 113)  # RED_400
        text = "MISSION OUTCOME"
    
    # Draw thick border
    draw.rectangle([0, 0, width-1, height-1], outline=primary_color, width=6)
    
    # Draw grid pattern background
    for i in range(0, width, 40):
        draw.line([(i, 0), (i, height)], fill=(primary_color[0]//4, primary_color[1]//4, primary_color[2]//4), width=1)
    for i in range(0, height, 40):
        draw.line([(0, i), (width, i)], fill=(primary_color[0]//4, primary_color[1]//4, primary_color[2]//4), width=1)
    
    # Draw character-like geometric shapes (anime-style silhouettes)
    center_x, center_y = width // 2, height // 2
    
    # Main character silhouette (head and body)
    head_size = 60
    body_width = 80
    body_height = 120
    
    # Head (circle)
    draw.ellipse([center_x - head_size//2, center_y - 100, center_x + head_size//2, center_y - 100 + head_size], 
                outline=accent_color, width=3)
    
    # Body (rectangle/torso)
    draw.rectangle([center_x - body_width//2, center_y - 40, center_x + body_width//2, center_y - 40 + body_height],
                  outline=primary_color, width=4)
    
    # Arms (lines)
    draw.line([(center_x - body_width//2, center_y - 20), (center_x - body_width//2 - 30, center_y + 20)], 
             fill=primary_color, width=3)
    draw.line([(center_x + body_width//2, center_y - 20), (center_x + body_width//2 + 30, center_y + 20)], 
             fill=primary_color, width=3)
    
    # Legs (lines)
    draw.line([(center_x - body_width//4, center_y - 40 + body_height), 
               (center_x - body_width//4, center_y - 40 + body_height + 40)], 
             fill=primary_color, width=3)
    draw.line([(center_x + body_width//4, center_y - 40 + body_height), 
               (center_x + body_width//4, center_y - 40 + body_height + 40)], 
             fill=primary_color, width=3)
    
    # Add glow effects (circles)
    for i in range(3):
        glow_size = head_size + i * 20
        alpha = 50 - i * 15
        glow_color = (min(255, accent_color[0] + alpha), min(255, accent_color[1] + alpha), min(255, accent_color[2] + alpha))
        draw.ellipse([center_x - glow_size//2, center_y - 100 - glow_size//2 + head_size//2, 
                     center_x + glow_size//2, center_y - 100 + glow_size//2 + head_size//2],
                    outline=glow_color, width=2)
    
    # Add some tech elements (small squares/circles)
    for x_offset in [-150, 150]:
        for y_offset in [-80, 80]:
            tech_x = center_x + x_offset
            tech_y = center_y + y_offset
            draw.rectangle([tech_x - 15, tech_y - 15, tech_x + 15, tech_y + 15], 
                          outline=primary_color, width=2)
            draw.ellipse([tech_x - 8, tech_y - 8, tech_x + 8, tech_y + 8], 
                        fill=accent_color)
    
    return img

