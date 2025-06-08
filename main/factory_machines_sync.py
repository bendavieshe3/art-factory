"""
Synchronous factory machine implementations for batch processing.
"""

import os
import requests
from django.conf import settings
from django.utils import timezone
from .models import Product, LogEntry


def safe_seed_value(seed):
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
        return 0


class SyncFalFactoryMachine:
    """Synchronous fal.ai factory machine for batch processing."""

    def __init__(self, machine_definition):
        self.machine_definition = machine_definition
        self.provider = "fal.ai"
        self.model_name = machine_definition.name

        # Configure fal client
        if settings.FAL_API_KEY:
            os.environ["FAL_KEY"] = settings.FAL_API_KEY

    def execute_sync(self, order_item):
        """Execute fal.ai generation synchronously with batch support."""
        try:
            import fal_client

            # Log start
            LogEntry.objects.create(
                level="INFO",
                message=f"Starting batch generation for order item {order_item.id}",
                order_item=order_item,
                extra_data={"batch_size": order_item.batch_size},
            )

            # Update status
            order_item.status = "processing"
            order_item.started_at = timezone.now()
            order_item.save()

            # Prepare arguments with batch support
            # Start with machine defaults, then override with order item parameters
            arguments = {
                "prompt": order_item.prompt,
                **self.machine_definition.default_parameters,  # Apply machine defaults first
                **order_item.parameters,  # Override with user-specified parameters
            }

            # Add negative prompt if provided
            if order_item.negative_prompt:
                arguments["negative_prompt"] = order_item.negative_prompt

            # Submit to fal.ai
            handle = fal_client.submit(self.model_name, arguments=arguments)
            result = handle.get()

            # Process batch results
            if result and "images" in result and result["images"]:
                products_created = []

                for idx, image_info in enumerate(result["images"]):
                    image_url = image_info["url"]

                    # Check if it's a base64 data URI
                    if image_url.startswith("data:"):
                        # Extract base64 data from data URI
                        import base64

                        # Format: data:image/jpeg;base64,/9j/4AAQ...
                        header, base64_data = image_url.split(",", 1)
                        image_content = base64.b64decode(base64_data)
                    else:
                        # Download image from URL
                        response = requests.get(image_url, timeout=30)
                        response.raise_for_status()
                        image_content = response.content

                    # Create product
                    file_name = f"fal_{order_item.id}_{idx}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    product = self._create_product(
                        order_item=order_item,
                        file_content=image_content,
                        file_name=file_name,
                        metadata={
                            "width": image_info.get("width"),
                            "height": image_info.get("height"),
                            "seed": safe_seed_value(result.get("seed", 0) + idx),
                            "provider_id": f"{result.get('request_id', '')}_{idx}",
                        },
                    )
                    products_created.append(product)

                # Update order item
                if products_created:
                    order_item.product = products_created[0]  # Backward compatibility
                    order_item.status = "completed"
                    order_item.completed_at = timezone.now()
                    order_item.batches_completed = 1
                    order_item.save()

                    LogEntry.objects.create(
                        level="INFO",
                        message=f"Batch generation completed: {len(products_created)} products created",
                        order_item=order_item,
                        extra_data={"products_created": len(products_created)},
                    )

                    # Update order status
                    self._update_order_status(order_item.order)

                return True
            else:
                raise Exception("No images returned from fal.ai")

        except Exception as e:
            error_msg = f"fal.ai batch generation failed: {str(e)}"
            order_item.status = "failed"
            order_item.error_message = error_msg
            order_item.completed_at = timezone.now()
            order_item.save()

            LogEntry.objects.create(level="ERROR", message=error_msg, order_item=order_item, extra_data={"exception": str(e)})

            # Update order status on failure
            self._update_order_status(order_item.order)

            return False

    def _create_product(self, order_item, file_content, file_name, metadata):
        """Create a Product record from generated content."""
        # Create product
        product = Product.objects.create(
            title=f"Generated by {self.machine_definition.display_name}",
            prompt=order_item.prompt,
            negative_prompt=order_item.negative_prompt,
            parameters=order_item.parameters,
            provider=self.provider,
            model_name=self.model_name,
            product_type="image",
            file_path="",
            file_size=len(file_content),
            file_format="jpg",
            width=metadata.get("width"),
            height=metadata.get("height"),
            seed=metadata.get("seed"),
            provider_id=metadata.get("provider_id", ""),
            order_item=order_item,  # Link to order item
        )

        # Save file
        import os
        from django.conf import settings

        media_dir = os.path.join(settings.MEDIA_ROOT, "generated", self.provider)
        os.makedirs(media_dir, exist_ok=True)

        file_path = f"generated/{self.provider}/{file_name}"
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        with open(full_path, "wb") as f:
            f.write(file_content)

        # Update product with file path
        product.file_path = file_path
        product.save()

        return product

    def _update_order_status(self, order):
        """Update order status based on its items."""
        items = order.orderitem_set.all()
        total_items = items.count()

        if total_items == 0:
            return

        completed_items = items.filter(status="completed").count()
        failed_items = items.filter(status="failed").count()

        if completed_items == total_items:
            order.status = "completed"
            order.completed_at = timezone.now()
        elif failed_items == total_items:
            order.status = "failed"
            order.completed_at = timezone.now()
        elif completed_items + failed_items == total_items:
            # All items finished, some succeeded and some failed
            if completed_items > 0:
                order.status = "partially_completed"
            else:
                order.status = "failed"
            order.completed_at = timezone.now()
        elif completed_items > 0 or failed_items > 0:
            order.status = "processing"

        order.save()


class SyncReplicateFactoryMachine:
    """Synchronous Replicate factory machine for batch processing."""

    def __init__(self, machine_definition):
        self.machine_definition = machine_definition
        self.provider = "replicate"
        self.model_name = machine_definition.name

        # Configure replicate
        if settings.REPLICATE_API_TOKEN:
            os.environ["REPLICATE_API_TOKEN"] = settings.REPLICATE_API_TOKEN

    def execute_sync(self, order_item):
        """Execute Replicate generation synchronously with batch support."""
        try:
            import replicate

            # Log start
            LogEntry.objects.create(
                level="INFO",
                message=f"Starting batch generation for order item {order_item.id}",
                order_item=order_item,
                extra_data={"batch_size": order_item.batch_size},
            )

            # Update status
            order_item.status = "processing"
            order_item.started_at = timezone.now()
            order_item.save()

            # Prepare input with batch support
            # Start with machine defaults, then override with order item parameters
            input_params = {
                "prompt": order_item.prompt,
                **self.machine_definition.default_parameters,  # Apply machine defaults first
                **order_item.parameters,  # Override with user-specified parameters
            }

            # Add negative prompt if provided
            if order_item.negative_prompt:
                input_params["negative_prompt"] = order_item.negative_prompt

            # Run prediction
            output = replicate.run(self.model_name, input=input_params)

            # Process batch results
            if output:
                products_created = []
                outputs_list = list(output) if hasattr(output, "__iter__") and not isinstance(output, str) else [output]

                for idx, single_output in enumerate(outputs_list):
                    if single_output:
                        # Download image
                        if hasattr(single_output, "read"):
                            image_content = single_output.read()
                        else:
                            response = requests.get(str(single_output), timeout=30)
                            response.raise_for_status()
                            image_content = response.content

                        # Create product
                        file_name = f"replicate_{order_item.id}_{idx}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        product = self._create_product(
                            order_item=order_item,
                            file_content=image_content,
                            file_name=file_name,
                            metadata={
                                "width": input_params.get("width", 1024),
                                "height": input_params.get("height", 1024),
                                "seed": (
                                    safe_seed_value(input_params.get("seed", 0) + idx) if input_params.get("seed") else None
                                ),
                                "provider_id": f"replicate_{timezone.now().timestamp()}_{idx}",
                            },
                        )
                        products_created.append(product)

                # Update order item
                if products_created:
                    order_item.product = products_created[0]  # Backward compatibility
                    order_item.status = "completed"
                    order_item.completed_at = timezone.now()
                    order_item.batches_completed = 1
                    order_item.save()

                    LogEntry.objects.create(
                        level="INFO",
                        message=f"Batch generation completed: {len(products_created)} products created",
                        order_item=order_item,
                        extra_data={"products_created": len(products_created)},
                    )

                    # Update order status
                    self._update_order_status(order_item.order)

                return True
            else:
                raise Exception("No output returned from Replicate")

        except Exception as e:
            error_msg = f"Replicate batch generation failed: {str(e)}"
            order_item.status = "failed"
            order_item.error_message = error_msg
            order_item.completed_at = timezone.now()
            order_item.save()

            LogEntry.objects.create(level="ERROR", message=error_msg, order_item=order_item, extra_data={"exception": str(e)})

            # Update order status on failure
            self._update_order_status(order_item.order)

            return False

    def _create_product(self, order_item, file_content, file_name, metadata):
        """Create a Product record from generated content."""
        # Create product
        product = Product.objects.create(
            title=f"Generated by {self.machine_definition.display_name}",
            prompt=order_item.prompt,
            negative_prompt=order_item.negative_prompt,
            parameters=order_item.parameters,
            provider=self.provider,
            model_name=self.model_name,
            product_type="image",
            file_path="",
            file_size=len(file_content),
            file_format="jpg",
            width=metadata.get("width"),
            height=metadata.get("height"),
            seed=metadata.get("seed"),
            provider_id=metadata.get("provider_id", ""),
            order_item=order_item,  # Link to order item
        )

        # Save file
        import os
        from django.conf import settings

        media_dir = os.path.join(settings.MEDIA_ROOT, "generated", self.provider)
        os.makedirs(media_dir, exist_ok=True)

        file_path = f"generated/{self.provider}/{file_name}"
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        with open(full_path, "wb") as f:
            f.write(file_content)

        # Update product with file path
        product.file_path = file_path
        product.save()

        return product

    def _update_order_status(self, order):
        """Update order status based on its items."""
        items = order.orderitem_set.all()
        total_items = items.count()

        if total_items == 0:
            return

        completed_items = items.filter(status="completed").count()
        failed_items = items.filter(status="failed").count()

        if completed_items == total_items:
            order.status = "completed"
            order.completed_at = timezone.now()
        elif failed_items == total_items:
            order.status = "failed"
            order.completed_at = timezone.now()
        elif completed_items + failed_items == total_items:
            # All items finished, some succeeded and some failed
            if completed_items > 0:
                order.status = "partially_completed"
            else:
                order.status = "failed"
            order.completed_at = timezone.now()
        elif completed_items > 0 or failed_items > 0:
            order.status = "processing"

        order.save()


def execute_order_item_sync_batch(order_item_id):
    """Execute a single order item synchronously with batch support."""
    try:
        from .models import OrderItem, FactoryMachineDefinition

        order_item = OrderItem.objects.get(id=order_item_id)
        machine_definition = FactoryMachineDefinition.objects.get(name=order_item.order.factory_machine_name)

        # Get appropriate sync factory machine
        if machine_definition.provider == "fal.ai":
            factory_machine = SyncFalFactoryMachine(machine_definition)
        elif machine_definition.provider == "replicate":
            factory_machine = SyncReplicateFactoryMachine(machine_definition)
        else:
            raise ValueError(f"Unknown provider: {machine_definition.provider}")

        # Execute synchronously
        return factory_machine.execute_sync(order_item)

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to execute order item {order_item_id}: {e}")
        return False
