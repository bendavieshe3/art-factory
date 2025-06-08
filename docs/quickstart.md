# Quick Start Guide

Get Art Factory running in under 10 minutes! This guide will walk you through setting up Art Factory for AI image generation.

## What You'll Need

- **Python 3.11+** installed on your system
- **AI provider API key** (fal.ai or Replicate - free tiers available)
- **10 minutes** of your time

## Step 1: Get API Keys

Choose one or both providers:

### fal.ai (Recommended for beginners)
1. Visit [fal.ai](https://fal.ai/)
2. Sign up for a free account
3. Go to [API Keys](https://fal.ai/dashboard/keys)
4. Create a new API key
5. Copy the key (starts with `fal_...`)

### Replicate
1. Visit [replicate.com](https://replicate.com/)
2. Sign up for a free account
3. Go to [Account Settings](https://replicate.com/account/api-tokens)
4. Create a new token
5. Copy the token (starts with `r8_...`)

## Step 2: Install Art Factory

### Download and Setup
```bash
# Clone the repository
git clone https://github.com/bendavieshe3/art-factory.git
cd art-factory

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment
Create a `.env` file in the project folder:

```bash
# Required: Add your API key(s)
FAL_KEY=your_fal_api_key_here
REPLICATE_API_TOKEN=your_replicate_token_here

# Optional: Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
```

**📝 Note**: Replace `your_fal_api_key_here` with your actual API key from Step 1.

## Step 3: Initialize the Database

```bash
# Set up the database
python manage.py migrate

# Load AI model definitions
python manage.py load_seed_data

# Start the server
python manage.py runserver
```

You should see:
```
✅ Successfully loaded 11 factory machine definitions and 16 instances
Django version 5.2.1, using settings 'ai_art_factory.settings'
Starting development server at http://127.0.0.1:8000/
```

## Step 4: Create Your First Image

1. **Open your browser** to http://127.0.0.1:8000
2. **Navigate to "Production"** in the top menu
3. **Choose an AI model** (try "FLUX.1 Schnell" for fast results)
4. **Enter a prompt** like: `"A serene mountain lake at sunset with pine trees"`
5. **Click "Place Order"**

### What happens next:
- Your order appears in the "Orders" section
- A background worker processes your request
- Generated images appear in "Inventory" when complete
- You can download, view, or delete images from Inventory

## Step 5: Explore Features

### Order Management
- **Track Progress**: Monitor order status in real-time
- **Batch Generation**: Create multiple images from one prompt
- **Model Comparison**: Try different AI models for varied styles

### Inventory
- **Download Images**: Save images to your computer
- **View Metadata**: See generation parameters, dimensions, and seeds
- **Bulk Operations**: Select multiple images for download or deletion

### Advanced Options
- **Negative Prompts**: Specify what you don't want in images
- **Custom Parameters**: Adjust dimensions, steps, and other model-specific settings
- **Error Recovery**: Automatic retry for failed generations

## Next Steps

### Try Different Models
Each AI model has different strengths:
- **FLUX.1 Dev**: High-quality, detailed images (slower)
- **FLUX.1 Schnell**: Fast generation with good quality
- **SDXL Models**: Excellent for photorealistic images
- **Dreamshaper**: Great for artistic and stylized images

### Experiment with Prompts
Effective prompting tips:
- Be specific about style: `"photorealistic"`, `"digital art"`, `"oil painting"`
- Include lighting: `"golden hour"`, `"dramatic lighting"`, `"soft natural light"`
- Add composition details: `"close-up"`, `"wide angle"`, `"bird's eye view"`
- Use negative prompts to avoid unwanted elements

### Batch Processing
Generate multiple variations:
1. Set **Quantity** > 1 in the order form
2. Each image gets a different random seed
3. Perfect for exploring variations of the same concept

## Troubleshooting

### Common Issues

**❌ "FAL_API_KEY not configured"**
- Check your `.env` file exists in the project root
- Verify your API key is correct and starts with `fal_`
- Restart the server after changing environment variables

**❌ "No workers available"**
- The worker system starts automatically
- Check the console for worker startup messages
- Try refreshing the page and placing a new order

**❌ Orders stuck in "processing"**
- Check your internet connection
- Verify your API key has sufficient credits
- Look for error messages in the terminal output

**❌ Images not appearing**
- Wait a few moments - generation can take 30-60 seconds
- Refresh the Inventory page
- Check the Orders page for error messages

### Getting Help

1. **Check the terminal** where you ran `python manage.py runserver` for error messages
2. **Review the Orders page** for specific error information
3. **Try a simpler prompt** to test if the issue is prompt-related
4. **Check API provider status** pages for service outages

## What's Next?

- **Production Deployment**: See `docs/deployment.md` for production setup
- **Architecture Overview**: Read `docs/design.md` to understand the system
- **Contributing**: Check out the GitHub repository for contribution guidelines

### Join the Community
- Report issues or request features on GitHub
- Share your generated images and prompts
- Contribute improvements and bug fixes

---

**🎉 Congratulations!** You now have a fully functional AI image generation system. Start creating and have fun exploring the possibilities of AI art!