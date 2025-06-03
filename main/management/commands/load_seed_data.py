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
                        "name": "stability-ai/stable-diffusion-xl-base-1.0",
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