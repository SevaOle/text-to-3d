// Global state
let currentImageData = null;
let generatedImages = [];

// DOM Elements
const ideaInput = document.getElementById('ideaInput');
const generateBtn = document.getElementById('generateBtn');
const imageGallery = document.getElementById('imageGallery');
const statusMessage = document.getElementById('statusMessage');
const modal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const modalPrompt = document.getElementById('modalPrompt');
const closeBtn = document.querySelector('.close-btn');
const download3DBtn = document.getElementById('download3DBtn');
const downloadImageBtn = document.getElementById('downloadImageBtn');
const modelStatus = document.getElementById('modelStatus');

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Event Listeners
generateBtn.addEventListener('click', generateImage);
closeBtn.addEventListener('click', closeModal);
download3DBtn.addEventListener('click', convertTo3D);
downloadImageBtn.addEventListener('click', downloadImage);

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === modal) {
        closeModal();
    }
});

// Allow Enter key to generate (with Shift+Enter for new line)
ideaInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        generateImage();
    }
});

/**
 * Main function to generate image from user idea
 */
async function generateImage() {
    const idea = ideaInput.value.trim();
    
    if (!idea) {
        showStatus('Please enter your idea or inspiration!', 'error');
        return;
    }
    
    // Disable button and show loading state
    setLoadingState(true);
    showStatus('🎨 Generating your image with DALL-E 3... This may take 10-15 seconds.', 'info');
    
    try {
        // Call Flask backend
        const response = await fetch(`${API_BASE_URL}/generate-image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ idea: idea })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Add image to gallery
            const imageData = {
                id: data.image_id,
                imageUrl: `http://localhost:5000${data.image_url}`,
                imagePath: data.image_path,  // Store for 3D conversion
                prompt: data.prompt,
                timestamp: new Date().toISOString()
            };
            
            addImageToGallery(imageData);
            
            showStatus('✨ Image generated successfully! Click to view or convert to 3D.', 'success');
            
            // Clear input
            ideaInput.value = '';
            
        } else {
            throw new Error(data.error || 'Failed to generate image');
        }
        
    } catch (error) {
        console.error('Error generating image:', error);
        showStatus(`❌ Error: ${error.message}`, 'error');
    } finally {
        setLoadingState(false);
    }
}

/**
 * Add generated image to the gallery
 */
function addImageToGallery(imageData) {
    generatedImages.unshift(imageData);  // Add to beginning
    
    const galleryItem = document.createElement('div');
    galleryItem.className = 'gallery-item';
    galleryItem.dataset.imageId = imageData.id;
    
    galleryItem.innerHTML = `
        <img src="${imageData.imageUrl}" alt="${imageData.prompt}" loading="lazy">
        <div class="gallery-item-overlay">
            <p class="gallery-item-prompt">${imageData.prompt}</p>
        </div>
    `;
    
    galleryItem.addEventListener('click', () => openModal(imageData));
    
    // Insert at beginning of gallery
    imageGallery.insertBefore(galleryItem, imageGallery.firstChild);
    
    // Add entrance animation
    setTimeout(() => {
        galleryItem.style.animation = 'fadeIn 0.5s';
    }, 10);
}

/**
 * Open modal to view image details
 */
function openModal(imageData) {
    currentImageData = imageData;
    modalImage.src = imageData.imageUrl;
    modalPrompt.textContent = imageData.prompt;
    modal.style.display = 'block';
    modelStatus.style.display = 'none';
    modelStatus.className = 'model-status';
    download3DBtn.disabled = false;
}

/**
 * Close the modal
 */
function closeModal() {
    modal.style.display = 'none';
    currentImageData = null;
}

/**
 * Convert current image to 3D model using Meshy AI
 */
async function convertTo3D() {
    if (!currentImageData) return;
    
    modelStatus.className = 'model-status loading';
    modelStatus.textContent = '🎭 Converting to 3D model... This may take 2-3 minutes. Please wait.';
    download3DBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/convert-to-3d`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_path: currentImageData.imagePath
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            const modelUrl = `http://localhost:5000${data.model_url}`;
            modelStatus.className = 'model-status success';
            modelStatus.innerHTML = `
                ✅ 3D Model ready! 
                <br><br>
                <a href="${modelUrl}" download class="download-link">
                    📥 Download 3D Model (.glb)
                </a>
                <br><br>
                <small>You can view .glb files in Windows 3D Viewer, Blender, or online at <a href="https://gltf-viewer.donmccurdy.com/" target="_blank">glTF Viewer</a></small>
            `;
        } else {
            throw new Error(data.error || 'Failed to convert to 3D');
        }
        
    } catch (error) {
        console.error('Error converting to 3D:', error);
        modelStatus.className = 'model-status error';
        modelStatus.textContent = `❌ Error: ${error.message}`;
    } finally {
        download3DBtn.disabled = false;
    }
}

/**
 * Download the current image
 */
function downloadImage() {
    if (!currentImageData) return;
    
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = currentImageData.imageUrl;
    link.download = `ai-generated-${currentImageData.id}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showStatus('📥 Image downloaded!', 'success');
}

/**
 * Show status message to user
 */
function showStatus(message, type = 'info') {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            if (statusMessage.className.includes('success')) {
                statusMessage.style.display = 'none';
            }
        }, 5000);
    }
}

/**
 * Set loading state for generate button
 */
function setLoadingState(isLoading) {
    generateBtn.disabled = isLoading;
    const btnText = generateBtn.querySelector('.btn-text');
    const btnLoader = generateBtn.querySelector('.btn-loader');
    
    if (isLoading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline';
    } else {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// Test API connection on load
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log('✅ Backend connected:', data);
    } catch (error) {
        console.error('❌ Backend connection failed:', error);
        showStatus('⚠️ Backend not connected. Make sure Flask server is running on port 5000.', 'error');
    }
});
