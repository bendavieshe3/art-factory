from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import timedelta
from main.models import FactoryMachineDefinition, FactoryMachineInstance


class Command(BaseCommand):
    help = 'Load seed data for factory machines and instances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing factory machines before loading seed data',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(
                self.style.WARNING('Deleting existing factory machines and instances...')
            )
            FactoryMachineInstance.objects.all().delete()
            FactoryMachineDefinition.objects.all().delete()

        self.stdout.write('Creating factory machine definitions...')
        
        try:
            with transaction.atomic():
                # Define factory machines
                machines_data = [
                    {
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
                                "width": {"type": "integer", "default": 1024, "minimum": 256, "maximum": 1440},
                                "height": {"type": "integer", "default": 1024, "minimum": 256, "maximum": 1440},
                                "seed": {"type": "integer", "description": "Random seed for reproducibility"},
                                "guidance_scale": {"type": "number", "default": 3.5, "minimum": 1.0, "maximum": 20.0},
                                "num_inference_steps": {"type": "integer", "default": 28, "minimum": 1, "maximum": 50}
                            },
                            "required": ["prompt"]
                        },
                        "default_parameters": {"width": 1024, "height": 1024, "guidance_scale": 3.5, "num_inference_steps": 28},
                        "max_concurrent_jobs": 3,
                        "estimated_duration": timedelta(seconds=30),
                        "cost_per_operation": "0.05"
                    },
                    {
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
                                "num_inference_steps": {"type": "integer", "default": 4, "minimum": 1, "maximum": 8}
                            },
                            "required": ["prompt"]
                        },
                        "default_parameters": {"width": 1024, "height": 1024, "num_inference_steps": 4},
                        "max_concurrent_jobs": 5,
                        "estimated_duration": timedelta(seconds=15),
                        "cost_per_operation": "0.03"
                    },
                    {
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
                                "num_outputs": {"type": "integer", "default": 1, "minimum": 1, "maximum": 4},
                                "num_inference_steps": {"type": "integer", "default": 4, "minimum": 1, "maximum": 8}
                            },
                            "required": ["prompt"]
                        },
                        "default_parameters": {"width": 1024, "height": 1024, "num_outputs": 1, "num_inference_steps": 4},
                        "max_concurrent_jobs": 3,
                        "estimated_duration": timedelta(seconds=20),
                        "cost_per_operation": "0.04"
                    },
                    {
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
                        "estimated_duration": timedelta(minutes=1),
                        "cost_per_operation": "0.08"
                    },
                    {
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
                        "estimated_duration": timedelta(seconds=20),
                        "cost_per_operation": "0.04"
                    },
                    {
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
                        "estimated_duration": timedelta(seconds=10),
                        "cost_per_operation": "0.025"
                    },
                    {
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
                        "estimated_duration": timedelta(seconds=5),
                        "cost_per_operation": "0.02"
                    },
                    {
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
                        "estimated_duration": timedelta(seconds=15),
                        "cost_per_operation": "0.03"
                    },
                    {
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
                        "estimated_duration": timedelta(seconds=45),
                        "cost_per_operation": "0.06"
                    },
                    {
                        "name": "fal-ai/dreamshaper",
                        "display_name": "Dreamshaper XL (fal.ai)",
                        "description": "Popular SDXL fine-tune model optimized for artistic and creative outputs. Excels at photos, art, anime, and manga styles.",
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
                                "guidance_scale": {"type": "number", "default": 5.0, "minimum": 1.0, "maximum": 20.0},
                                "num_inference_steps": {"type": "integer", "default": 25, "minimum": 10, "maximum": 50},
                                "num_images": {"type": "integer", "default": 1, "minimum": 1, "maximum": 4},
                                "enable_safety_checker": {"type": "boolean", "default": False, "description": "Enable the safety checker"}
                            },
                            "required": ["prompt"]
                        },
                        "default_parameters": {"width": 1024, "height": 1024, "guidance_scale": 5.0, "num_inference_steps": 25, "num_images": 1, "enable_safety_checker": False},
                        "max_concurrent_jobs": 4,
                        "estimated_duration": timedelta(seconds=25),
                        "cost_per_operation": "0.045"
                    },
                    {
                        "name": "lucataco/dreamshaper-xl-turbo",
                        "display_name": "Dreamshaper XL Turbo (Replicate)",
                        "description": "Fast Dreamshaper variant for rapid artistic generation. Great for anime, manga, and stylized art. Runs in just 5 seconds.",
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
                                "guidance_scale": {"type": "number", "default": 2.0, "minimum": 1.0, "maximum": 10.0},
                                "num_inference_steps": {"type": "integer", "default": 6, "minimum": 4, "maximum": 8},
                                "num_outputs": {"type": "integer", "default": 1, "minimum": 1, "maximum": 4},
                                "disable_safety_checker": {"type": "boolean", "default": True, "description": "Disable the safety checker"}
                            },
                            "required": ["prompt"]
                        },
                        "default_parameters": {"width": 1024, "height": 1024, "guidance_scale": 2.0, "num_inference_steps": 6, "num_outputs": 1, "disable_safety_checker": True},
                        "max_concurrent_jobs": 5,
                        "estimated_duration": timedelta(seconds=5),
                        "cost_per_operation": "0.041"
                    }
                ]
                
                # Create factory machines
                machines = []
                for machine_data in machines_data:
                    machine, created = FactoryMachineDefinition.objects.get_or_create(
                        name=machine_data["name"],
                        defaults=machine_data
                    )
                    machines.append(machine)
                    if created:
                        self.stdout.write(f'  Created: {machine.display_name}')
                    else:
                        self.stdout.write(f'  Exists: {machine.display_name}')
                
                # Create factory machine instances
                instances_data = [
                    (machines[0], "flux-dev-01"),
                    (machines[1], "flux-schnell-01"),
                    (machines[1], "flux-schnell-02"),
                    (machines[2], "replicate-flux-01"),
                    (machines[3], "sdxl-replicate-01"),
                    (machines[4], "fast-sdxl-01"),
                    (machines[4], "fast-sdxl-02"),
                    (machines[5], "lightning-sdxl-01"),
                    (machines[5], "lightning-sdxl-02"),
                    (machines[6], "turbo-sdxl-01"),
                    (machines[7], "replicate-lightning-01"),
                    (machines[8], "replicate-sdxl-01"),
                    (machines[9], "dreamshaper-xl-01"),
                    (machines[9], "dreamshaper-xl-02"),
                    (machines[10], "dreamshaper-turbo-01"),
                    (machines[10], "dreamshaper-turbo-02"),
                ]
                
                for machine, instance_id in instances_data:
                    instance, created = FactoryMachineInstance.objects.get_or_create(
                        machine_definition=machine,
                        instance_id=instance_id,
                        defaults={
                            "status": "idle",
                            "total_operations": 0,
                            "successful_operations": 0,
                            "failed_operations": 0,
                        }
                    )
                    if created:
                        self.stdout.write(f'  Created instance: {instance_id}')
                    else:
                        self.stdout.write(f'  Exists instance: {instance_id}')
                
            # Display results
            machine_count = FactoryMachineDefinition.objects.count()
            instance_count = FactoryMachineInstance.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully loaded {machine_count} factory machine definitions '
                    f'and {instance_count} instances'
                )
            )
            
            # Show what was loaded
            self.stdout.write('\nAvailable Factory Machines:')
            for machine in FactoryMachineDefinition.objects.all().order_by('provider', 'display_name'):
                status = '✓' if machine.is_active else '✗'
                self.stdout.write(f'  {status} {machine.display_name} ({machine.provider})')
            
            self.stdout.write(
                self.style.SUCCESS(
                    '\nSeed data loaded successfully! You can now place orders through the web interface.'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading seed data: {e}')
            )