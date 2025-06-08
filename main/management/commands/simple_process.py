import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from main.models import OrderItem, Product

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Simple synchronous order processing"

    def handle(self, *args, **options):
        pending_items = OrderItem.objects.filter(status="pending")

        if not pending_items:
            self.stdout.write(self.style.SUCCESS("No pending orders to process"))
            return

        self.stdout.write(f"Processing {pending_items.count()} pending orders...")

        for item in pending_items:
            self.stdout.write(f"Processing order item {item.id}...")

            try:
                # Update status to processing
                item.status = "processing"
                item.started_at = timezone.now()
                item.save()

                # Get machine info
                machine_name = item.order.factory_machine_name
                provider = item.order.provider

                if provider == "fal.ai":
                    result = self.process_fal_item(item, machine_name)
                elif provider == "replicate":
                    result = self.process_replicate_item(item, machine_name)
                else:
                    raise ValueError(f"Unknown provider: {provider}")

                if result:
                    item.status = "completed"
                    item.product = result
                    self.stdout.write(self.style.SUCCESS(f"✅ Completed order item {item.id}"))
                else:
                    item.status = "failed"
                    item.error_message = "Generation failed"
                    self.stdout.write(self.style.ERROR(f"❌ Failed order item {item.id}"))

                item.completed_at = timezone.now()
                item.save()

                # Update order status if all items are completed
                self.update_order_status(item.order)

            except Exception as e:
                item.status = "failed"
                item.error_message = str(e)
                item.completed_at = timezone.now()
                item.save()
                self.update_order_status(item.order)
                self.stdout.write(self.style.ERROR(f"❌ Error processing order item {item.id}: {e}"))

    def update_order_status(self, order):
        """Update order status based on item completion."""
        items = order.orderitem_set.all()
        completed_items = items.filter(status="completed")
        failed_items = items.filter(status="failed")

        if completed_items.count() == items.count():
            # All items completed successfully
            order.status = "completed"
            order.completed_at = timezone.now()
            order.save()
            self.stdout.write(f"  📋 Order {order.id} marked as completed")
        elif failed_items.count() == items.count():
            # All items failed
            order.status = "failed"
            order.completed_at = timezone.now()
            order.save()
            self.stdout.write(f"  📋 Order {order.id} marked as failed")
        elif (completed_items.count() + failed_items.count()) == items.count():
            # Mixed results - mark as completed if at least one succeeded
            order.status = "completed"
            order.completed_at = timezone.now()
            order.save()
            self.stdout.write(f"  📋 Order {order.id} marked as completed (with some failures)")

    def process_fal_item(self, item, machine_name):
        """Process item using fal.ai"""
        if not settings.FAL_API_KEY:
            raise ValueError("FAL_KEY not configured")

        import fal_client

        os.environ["FAL_KEY"] = settings.FAL_API_KEY

        # Prepare arguments
        arguments = {"prompt": item.prompt, **item.parameters}

        self.stdout.write(f"  Submitting to {machine_name}...")
        if "enable_safety_checker" in arguments:
            self.stdout.write(f'    Safety checker enabled: {arguments["enable_safety_checker"]}')

        # Submit and get result
        handle = fal_client.submit(machine_name, arguments=arguments)
        result = handle.get()

        if result and isinstance(result, dict) and "images" in result and result["images"]:
            image_info = result["images"][0]
            image_url = image_info["url"]

            # Download image
            import httpx

            with httpx.Client() as client:
                response = client.get(image_url)
                response.raise_for_status()
                image_content = response.content

            # Create product
            return self.create_product(
                item=item,
                file_content=image_content,
                metadata={
                    "width": image_info.get("width"),
                    "height": image_info.get("height"),
                    "seed": self.safe_seed_value(result.get("seed")),
                    "provider_id": str(result.get("request_id", "")),
                },
                provider="fal.ai",
                model_name=machine_name,
            )

        return None

    def process_replicate_item(self, item, machine_name):
        """Process item using Replicate"""
        if not settings.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN not configured")

        import replicate

        os.environ["REPLICATE_API_TOKEN"] = settings.REPLICATE_API_TOKEN

        # Prepare input
        input_params = {"prompt": item.prompt, **item.parameters}

        self.stdout.write(f"  Submitting to {machine_name}...")
        if "disable_safety_checker" in input_params:
            self.stdout.write(f'    Safety checker disabled: {input_params["disable_safety_checker"]}')

        # Submit and get result
        output = replicate.run(machine_name, input=input_params)

        if output:
            if hasattr(output, "__iter__") and not isinstance(output, str):
                output = list(output)[0] if output else None

            if output:
                # Download file
                if hasattr(output, "read"):
                    image_content = output.read()
                else:
                    import httpx

                    with httpx.Client() as client:
                        response = client.get(str(output))
                        response.raise_for_status()
                        image_content = response.content

                # Create product
                return self.create_product(
                    item=item,
                    file_content=image_content,
                    metadata={
                        "width": input_params.get("width", 1024),
                        "height": input_params.get("height", 1024),
                        "seed": self.safe_seed_value(input_params.get("seed")),
                        "provider_id": f"replicate_{timezone.now().timestamp()}",
                    },
                    provider="replicate",
                    model_name=machine_name,
                )

        return None

    def create_product(self, item, file_content, metadata, provider, model_name):
        """Create a Product record from generated content."""
        import os

        from django.conf import settings

        # Create product
        product = Product.objects.create(
            title="Generated Image",
            prompt=item.prompt,
            parameters=item.parameters,
            provider=provider,
            model_name=model_name,
            product_type="image",
            file_path="",  # Will be set after file save
            file_size=len(file_content),
            file_format="png",
            width=metadata.get("width"),
            height=metadata.get("height"),
            seed=metadata.get("seed"),
            provider_id=metadata.get("provider_id", ""),
        )

        # Save file
        media_dir = os.path.join(settings.MEDIA_ROOT, "generated", provider)
        os.makedirs(media_dir, exist_ok=True)

        file_name = f"{provider}_{item.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = f"generated/{provider}/{file_name}"
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        with open(full_path, "wb") as f:
            f.write(file_content)

        # Update product with file path
        product.file_path = file_path
        product.save()

        self.stdout.write(f"    Created product {product.id}: {file_path}")

        return product

    def safe_seed_value(self, seed):
        """Convert seed to safe value for SQLite BigIntegerField."""
        if seed is None:
            return None

        try:
            # Convert to int if it's a string
            if isinstance(seed, str):
                seed = int(seed)

            # SQLite's INTEGER max is 2^63-1 (9223372036854775807)
            # If seed is larger, use modulo to fit within range
            max_sqlite_int = 9223372036854775807
            if seed > max_sqlite_int:
                return seed % max_sqlite_int
            elif seed < -max_sqlite_int:
                return -((-seed) % max_sqlite_int)

            return seed
        except (ValueError, TypeError):
            # If conversion fails, return None
            return None
