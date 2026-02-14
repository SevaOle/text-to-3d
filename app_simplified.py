"""
Simplified Flask Backend for AI Image Generator
- Direct OpenAI DALL-E 3 image generation
- Meshy AI 3D model conversion
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import requests
import uuid
from datetime import datetime
import time
import json

app = Flask(__name__)
CORS(app)

# ==================== CONFIGURATION ====================
# Your API Keys
OPENAI_API_KEY = ""
MESHY_API_KEY = ""

# Storage folders
UPLOAD_FOLDER = 'static/generated_images'
MODELS_FOLDER = 'static/3d_models'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODELS_FOLDER, exist_ok=True)

# ==================== HELPER FUNCTIONS ====================

def generate_image_dalle(prompt):
    """
    Generate image using OpenAI DALL-E 3
    """
    try:
        print(f"📸 Generating image with DALL-E 3...")
        print(f"Prompt: {prompt}")
        
        url = "https://api.openai.com/v1/images/generations"
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            raise Exception(f"OpenAI API error: {error_msg}")
        
        data = response.json()
        image_url = data['data'][0]['url']
        
        print(f"✅ Image generated: {image_url}")
        
        # Download and save image locally
        image_response = requests.get(image_url, timeout=30)
        image_filename = f"{uuid.uuid4()}.png"
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        
        local_url = f"/static/generated_images/{image_filename}"
        print(f"💾 Image saved locally: {local_url}")
        
        return local_url, image_path
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        raise Exception(f"Image generation failed: {str(e)}")


def convert_to_3d_meshy(image_path):
    """
    Convert image to 3D model using Meshy AI
    
    Meshy AI Workflow:
    1. Upload image and create task
    2. Poll task status until complete
    3. Download 3D model
    """
    try:
        print(f"🎭 Starting 3D conversion with Meshy AI...")
        
        # Step 1: Create image-to-3D task
        url = "https://api.meshy.ai/v2/image-to-3d"
        
        headers = {
            "Authorization": f"Bearer {MESHY_API_KEY}"
        }
        
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Create task
        files = {
            'image_file': ('image.png', image_data, 'image/png')
        }
        
        data = {
            'enable_pbr': 'true',  # Enable PBR materials
            'ai_model': 'meshy-4'  # Latest model
        }
        
        print("📤 Uploading image to Meshy AI...")
        response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        
        if response.status_code not in [200, 201]:
            error_msg = response.text
            raise Exception(f"Meshy API error: {error_msg}")
        
        result = response.json()
        task_id = result.get('result')
        
        if not task_id:
            raise Exception("No task ID returned from Meshy")
        
        print(f"✅ Task created: {task_id}")
        print("⏳ Waiting for 3D model generation (this may take 2-3 minutes)...")
        
        # Step 2: Poll for task completion
        status_url = f"https://api.meshy.ai/v2/image-to-3d/{task_id}"
        
        max_attempts = 60  # 5 minutes max (5 seconds per attempt)
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(5)  # Wait 5 seconds between checks
            attempt += 1
            
            status_response = requests.get(status_url, headers=headers, timeout=30)
            
            if status_response.status_code != 200:
                print(f"⚠️ Status check failed: {status_response.text}")
                continue
            
            status_data = status_response.json()
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            
            print(f"📊 Status: {status} | Progress: {progress}%")
            
            if status == 'SUCCEEDED':
                # Get model download URL
                model_urls = status_data.get('model_urls', {})
                glb_url = model_urls.get('glb')
                
                if not glb_url:
                    raise Exception("No GLB model URL in response")
                
                print(f"✅ 3D model ready! Downloading...")
                
                # Download 3D model
                model_response = requests.get(glb_url, timeout=60)
                model_filename = f"{uuid.uuid4()}.glb"
                model_path = os.path.join(MODELS_FOLDER, model_filename)
                
                with open(model_path, 'wb') as f:
                    f.write(model_response.content)
                
                local_model_url = f"/static/3d_models/{model_filename}"
                print(f"💾 3D model saved: {local_model_url}")
                
                return local_model_url
                
            elif status == 'FAILED':
                error = status_data.get('error', 'Unknown error')
                raise Exception(f"3D conversion failed: {error}")
            
            # Still processing, continue polling
        
        raise Exception("3D conversion timed out after 5 minutes")
        
    except Exception as e:
        print(f"❌ 3D conversion error: {e}")
        raise Exception(f"3D conversion failed: {str(e)}")


# ==================== API ROUTES ====================

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    """
    Generate image from user prompt (no Claude enhancement)
    """
    try:
        data = request.get_json()
        user_prompt = data.get('idea', '').strip()
        
        if not user_prompt:
            return jsonify({
                'success': False,
                'error': 'No prompt provided'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"🎨 New image generation request")
        print(f"User prompt: {user_prompt}")
        print(f"{'='*60}\n")
        
        # Generate image directly with user's prompt
        image_url, image_path = generate_image_dalle(user_prompt)
        
        # Generate unique ID
        image_id = str(uuid.uuid4())
        
        print(f"\n✨ Image generation complete!")
        print(f"Image ID: {image_id}")
        print(f"Image URL: {image_url}\n")
        
        return jsonify({
            'success': True,
            'image_id': image_id,
            'image_url': image_url,
            'image_path': image_path,  # Store for 3D conversion
            'prompt': user_prompt,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/convert-to-3d', methods=['POST'])
def convert_to_3d():
    """
    Convert generated image to 3D model using Meshy AI
    """
    try:
        data = request.get_json()
        image_path = data.get('image_path')
        
        if not image_path:
            return jsonify({
                'success': False,
                'error': 'No image path provided'
            }), 400
        
        # Convert relative URL to file path if needed
        if image_path.startswith('/static/'):
            image_path = image_path.replace('/static/', 'static/')
        
        print(f"\n{'='*60}")
        print(f"🎭 3D conversion request")
        print(f"Image path: {image_path}")
        print(f"{'='*60}\n")
        
        # Convert to 3D
        model_url = convert_to_3d_meshy(image_path)
        
        print(f"\n✨ 3D conversion complete!")
        print(f"Model URL: {model_url}\n")
        
        return jsonify({
            'success': True,
            'model_url': model_url
        })
        
    except Exception as e:
        print(f"\n❌ 3D conversion error: {e}\n")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'openai_configured': bool(OPENAI_API_KEY),
        'meshy_configured': bool(MESHY_API_KEY),
        'timestamp': datetime.now().isoformat()
    })


# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AI Image Generator Backend Starting...")
    print("="*60)
    print(f"📸 OpenAI DALL-E: {'✅ Configured' if OPENAI_API_KEY else '❌ Not configured'}")
    print(f"🎭 Meshy AI: {'✅ Configured' if MESHY_API_KEY else '❌ Not configured'}")
    print(f"💾 Upload folder: {UPLOAD_FOLDER}")
    print(f"🎨 Models folder: {MODELS_FOLDER}")
    print("="*60)
    print("\n🌐 Server running on http://localhost:5000")
    print("📡 API endpoints:")
    print("   POST /api/generate-image")
    print("   POST /api/convert-to-3d")
    print("   GET  /api/health")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
