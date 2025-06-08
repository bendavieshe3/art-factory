import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Test fal.ai generation directly"

    def handle(self, *args, **options):
        # Check API key
        if not settings.FAL_API_KEY:
            self.stdout.write(self.style.ERROR("FAL_KEY not configured"))
            return

        self.stdout.write(f"FAL_KEY configured: {settings.FAL_API_KEY[:10]}...")

        # Test fal.ai directly
        try:
            import fal_client

            # Set up environment
            os.environ["FAL_KEY"] = settings.FAL_API_KEY

            self.stdout.write("Testing fal.ai connection...")

            # Simple synchronous test
            self.stdout.write("Submitting request to fal.ai...")
            result = fal_client.submit(
                "fal-ai/flux/schnell", arguments={"prompt": "a cute robot", "width": 512, "height": 512}
            )

            self.stdout.write(self.style.SUCCESS(f"Request submitted! Handle: {result}"))

            # Get the actual result
            if hasattr(result, "get"):
                final_result = result.get()
                self.stdout.write(f"Final result: {final_result}")

                if final_result and isinstance(final_result, dict) and "images" in final_result:
                    self.stdout.write(f'Generated {len(final_result["images"])} image(s)')
                    for i, img in enumerate(final_result["images"]):
                        self.stdout.write(f'  Image {i + 1}: {img.get("url", "No URL")}')
            else:
                self.stdout.write(f"Result type: {type(result)}, value: {result}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            import traceback

            self.stdout.write(traceback.format_exc())
