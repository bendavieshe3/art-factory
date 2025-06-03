#!/usr/bin/env python
"""
Generate factory machine fixtures with proper timestamps
"""
import json
from datetime import datetime

# Base timestamp
base_time = "2025-05-31T08:00:00Z"

factory_machines = [
    {
        "pk": 1,
        "name": "fal-ai/flux/dev",
        "display_name": "FLUX.1 Dev (fal.ai)",
        "description": "High-quality text-to-image generation with excellent human anatomy and text reproduction. Best for detailed, artistic images.",
        "provider": "fal.ai",
        "model_family": "flux",
        "modality": "text-to-image",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Text description of the image to generate"},
                "width": {"type": "integer", "default": 1024, "minimum": 256, "maximum": 1440, "description": "Width of the generated image"},
                "height": {"type": "integer", "default": 1024, "minimum": 256, "maximum": 1440, "description": "Height of the generated image"},
                "seed": {"type": "integer", "description": "Random seed for reproducibility"},
                "guidance_scale": {"type": "number", "default": 3.5, "minimum": 1.0, "maximum": 20.0, "description": "How closely to follow the prompt"},
                "num_inference_steps": {"type": "integer", "default": 28, "minimum": 1, "maximum": 50, "description": "Number of denoising steps"}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 1024, "height": 1024, "guidance_scale": 3.5, "num_inference_steps": 28},
        "max_concurrent_jobs": 3,
        "estimated_duration": "00:00:30",
        "cost_per_operation": "0.05"
    },
    {
        "pk": 2,
        "name": "fal-ai/flux/schnell",
        "display_name": "FLUX.1 Schnell (fal.ai)",
        "description": "Fast version of FLUX.1 for rapid generation. Good quality with faster processing time.",
        "provider": "fal.ai",
        "model_family": "flux",
        "modality": "text-to-image",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Text description of the image to generate"},
                "width": {"type": "integer", "default": 1024, "minimum": 256, "maximum": 1440},
                "height": {"type": "integer", "default": 1024, "minimum": 256, "maximum": 1440},
                "seed": {"type": "integer", "description": "Random seed for reproducibility"},
                "num_inference_steps": {"type": "integer", "default": 4, "minimum": 1, "maximum": 8, "description": "Number of denoising steps (fewer for speed)"}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 1024, "height": 1024, "num_inference_steps": 4},
        "max_concurrent_jobs": 5,
        "estimated_duration": "00:00:15",
        "cost_per_operation": "0.03"
    },
    {
        "pk": 3,
        "name": "black-forest-labs/flux-schnell",
        "display_name": "FLUX.1 Schnell (Replicate)",
        "description": "Fast FLUX.1 model on Replicate. Good for rapid prototyping and batch generation.",
        "provider": "replicate",
        "model_family": "flux",
        "modality": "text-to-image",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Text description of the image to generate"},
                "width": {"type": "integer", "default": 1024, "minimum": 256, "maximum": 1440},
                "height": {"type": "integer", "default": 1024, "minimum": 256, "maximum": 1440},
                "seed": {"type": "integer", "description": "Random seed for reproducibility"},
                "num_outputs": {"type": "integer", "default": 1, "minimum": 1, "maximum": 4, "description": "Number of images to generate"},
                "num_inference_steps": {"type": "integer", "default": 4, "minimum": 1, "maximum": 8}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 1024, "height": 1024, "num_outputs": 1, "num_inference_steps": 4},
        "max_concurrent_jobs": 3,
        "estimated_duration": "00:00:20",
        "cost_per_operation": "0.04"
    },
    {
        "pk": 4,
        "name": "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
        "display_name": "Stable Diffusion XL (Replicate)",
        "description": "High-resolution text-to-image generation with excellent detail and composition. Industry standard model.",
        "provider": "replicate",
        "model_family": "stable-diffusion",
        "modality": "text-to-image",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Text description of the image to generate"},
                "negative_prompt": {"type": "string", "description": "What you don't want in the image"},
                "width": {"type": "integer", "default": 1024, "minimum": 512, "maximum": 1536},
                "height": {"type": "integer", "default": 1024, "minimum": 512, "maximum": 1536},
                "seed": {"type": "integer", "description": "Random seed for reproducibility"},
                "guidance_scale": {"type": "number", "default": 7.5, "minimum": 1.0, "maximum": 20.0},
                "num_inference_steps": {"type": "integer", "default": 25, "minimum": 10, "maximum": 50},
                "scheduler": {"type": "string", "default": "DPMSolverMultistep", "enum": ["DDIM", "DPMSolverMultistep", "HeunDiscrete", "K_EULER", "K_EULER_ANCESTRAL", "PNDM"]},
                "disable_safety_checker": {"type": "boolean", "default": True, "description": "Disable the safety checker to prevent false positives"}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 1024, "height": 1024, "guidance_scale": 7.5, "num_inference_steps": 25, "scheduler": "DPMSolverMultistep", "disable_safety_checker": True},
        "max_concurrent_jobs": 2,
        "estimated_duration": "00:01:00",
        "cost_per_operation": "0.08"
    }
]

# Generate fixture data
fixture_data = []
for machine in factory_machines:
    fixture_data.append({
        "model": "main.factorymachinedefinition",
        "pk": machine["pk"],
        "fields": {
            **{k: v for k, v in machine.items() if k != "pk"},
            "is_active": True
        }
    })

# Write to file
with open('main/fixtures/factory_machines.json', 'w') as f:
    json.dump(fixture_data, f, indent=2)

print("Generated factory_machines.json with proper timestamps")