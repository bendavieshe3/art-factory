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
    },
    {
        "pk": 5,
        "name": "fal-ai/fast-sdxl",
        "display_name": "Fast SDXL (fal.ai)",
        "description": "Optimized SDXL for lightning-fast generation. Excellent balance of speed and quality.",
        "provider": "fal.ai",
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
                "disable_safety_checker": {"type": "boolean", "default": True, "description": "Disable the safety checker"}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 1024, "height": 1024, "guidance_scale": 7.5, "num_inference_steps": 25, "disable_safety_checker": True},
        "max_concurrent_jobs": 4,
        "estimated_duration": "00:00:20",
        "cost_per_operation": "0.04"
    },
    {
        "pk": 6,
        "name": "fal-ai/fast-lightning-sdxl",
        "display_name": "SDXL Lightning (fal.ai)",
        "description": "Ultra-fast SDXL Lightning variant. Generates high-quality images in just 4 steps.",
        "provider": "fal.ai",
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
                "num_inference_steps": {"type": "integer", "default": 4, "minimum": 1, "maximum": 8},
                "disable_safety_checker": {"type": "boolean", "default": True, "description": "Disable the safety checker"}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 1024, "height": 1024, "num_inference_steps": 4, "disable_safety_checker": True},
        "max_concurrent_jobs": 5,
        "estimated_duration": "00:00:10",
        "cost_per_operation": "0.025"
    },
    {
        "pk": 7,
        "name": "fal-ai/fast-turbo-diffusion",
        "display_name": "SDXL Turbo (fal.ai)",
        "description": "SDXL Turbo for single-step generation. Ultra-fast but with some quality trade-offs.",
        "provider": "fal.ai",
        "model_family": "stable-diffusion",
        "modality": "text-to-image",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Text description of the image to generate"},
                "width": {"type": "integer", "default": 512, "minimum": 512, "maximum": 1024},
                "height": {"type": "integer", "default": 512, "minimum": 512, "maximum": 1024},
                "seed": {"type": "integer", "description": "Random seed for reproducibility"},
                "num_inference_steps": {"type": "integer", "default": 1, "minimum": 1, "maximum": 4},
                "disable_safety_checker": {"type": "boolean", "default": True, "description": "Disable the safety checker"}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 512, "height": 512, "num_inference_steps": 1, "disable_safety_checker": True},
        "max_concurrent_jobs": 6,
        "estimated_duration": "00:00:05",
        "cost_per_operation": "0.02"
    },
    {
        "pk": 8,
        "name": "bytedance/sdxl-lightning-4step:727e49a643e999d602a896c774a0658ffefea21465756a6ce24b7ea4165eba6a",
        "display_name": "SDXL Lightning 4-step (Replicate)",
        "description": "SDXL Lightning by ByteDance. Generates high-quality 1024px images in just 4 steps.",
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
                "num_outputs": {"type": "integer", "default": 1, "minimum": 1, "maximum": 4},
                "scheduler": {"type": "string", "default": "K_EULER", "enum": ["DDIM", "K_EULER", "DPMSolverMultistep", "K_EULER_ANCESTRAL", "PNDM", "KLMS"]},
                "disable_safety_checker": {"type": "boolean", "default": True, "description": "Disable the safety checker"}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 1024, "height": 1024, "num_outputs": 1, "scheduler": "K_EULER", "disable_safety_checker": True},
        "max_concurrent_jobs": 3,
        "estimated_duration": "00:00:15",
        "cost_per_operation": "0.03"
    },
    {
        "pk": 9,
        "name": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "display_name": "SDXL 1.0 (Replicate)",
        "description": "The original SDXL 1.0 model. High-quality generation with full control over parameters.",
        "provider": "replicate",
        "model_family": "stable-diffusion",
        "modality": "text-to-image",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Text description of the image to generate"},
                "negative_prompt": {"type": "string", "description": "What you don't want in the image"},
                "width": {"type": "integer", "default": 1024, "minimum": 512, "maximum": 2048},
                "height": {"type": "integer", "default": 1024, "minimum": 512, "maximum": 2048},
                "seed": {"type": "integer", "description": "Random seed for reproducibility"},
                "guidance_scale": {"type": "number", "default": 7.5, "minimum": 1.0, "maximum": 20.0},
                "num_inference_steps": {"type": "integer", "default": 30, "minimum": 1, "maximum": 50},
                "scheduler": {"type": "string", "default": "K_EULER", "enum": ["DDIM", "K_EULER", "DPMSolverMultistep", "K_EULER_ANCESTRAL", "PNDM", "KLMS"]},
                "refine": {"type": "string", "default": "no_refiner", "enum": ["no_refiner", "expert_ensemble_refiner", "base_image_refiner"]},
                "high_noise_frac": {"type": "number", "default": 0.8, "minimum": 0.0, "maximum": 1.0},
                "disable_safety_checker": {"type": "boolean", "default": True, "description": "Disable the safety checker"}
            },
            "required": ["prompt"]
        },
        "default_parameters": {"width": 1024, "height": 1024, "guidance_scale": 7.5, "num_inference_steps": 30, "scheduler": "K_EULER", "refine": "no_refiner", "high_noise_frac": 0.8, "disable_safety_checker": True},
        "max_concurrent_jobs": 2,
        "estimated_duration": "00:00:45",
        "cost_per_operation": "0.06"
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