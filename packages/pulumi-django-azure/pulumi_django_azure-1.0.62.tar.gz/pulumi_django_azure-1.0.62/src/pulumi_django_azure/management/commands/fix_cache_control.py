import os

from azure.storage.blob import BlobServiceClient
from django.conf import settings
from django.core.management.base import BaseCommand

from pulumi_django_azure.azure_helper import AZURE_CREDENTIAL

DEFAULT_CACHE_CONTROL = "public,max-age=31536000,immutable"


class Command(BaseCommand):
    help = "Loops over all files in the static and media containers and applies the cache-control setting if it is not set yet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cache-control",
            action="store",
            default=DEFAULT_CACHE_CONTROL,
            help="The cache-control setting to apply to the blobs",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without actually updating the blobs",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        cache_control = options["cache_control"]
        # Get storage account name and containers from settings
        storage_account_name = getattr(settings, "AZURE_ACCOUNT_NAME", None)
        if not storage_account_name:
            self.stderr.write(self.style.ERROR("AZURE_ACCOUNT_NAME is not set in settings."))
            return

        # Get containers from environment variables
        media_container = os.getenv("AZURE_STORAGE_CONTAINER_MEDIA")
        static_container = os.getenv("AZURE_STORAGE_CONTAINER_STATICFILES")

        containers = []
        if media_container:
            containers.append(("media", media_container))
        if static_container:
            containers.append(("static", static_container))

        if not containers:
            self.stderr.write(
                self.style.ERROR("No containers configured (AZURE_STORAGE_CONTAINER_MEDIA or AZURE_STORAGE_CONTAINER_STATICFILES).")
            )
            return

        # Get cache-control setting
        self.stdout.write(f"Using cache-control: {cache_control}")

        # Create BlobServiceClient
        account_url = f"https://{storage_account_name}.blob.core.windows.net"
        blob_service_client = BlobServiceClient(account_url=account_url, credential=AZURE_CREDENTIAL)

        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for container_type, container_name in containers:
            self.stdout.write(f"\nProcessing {container_type} container: {container_name}")
            try:
                container_client = blob_service_client.get_container_client(container_name)

                # List all blobs in the container
                blobs = container_client.list_blobs()
                blob_count = 0

                for blob in blobs:
                    blob_count += 1
                    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob.name)

                    # Get current blob properties
                    try:
                        properties = blob_client.get_blob_properties()
                        content_settings = properties.content_settings
                        current_cache_control = content_settings.cache_control if content_settings else None

                        # Check if cache-control is already set
                        if current_cache_control:
                            if dry_run:
                                self.stdout.write(f"  [SKIP] {blob.name} (already has cache-control: {current_cache_control})")
                            total_skipped += 1
                        else:
                            # Set cache-control if not set
                            if dry_run:
                                self.stdout.write(f"  [WOULD UPDATE] {blob.name}")
                            else:
                                # Create new content settings with the new cache-control
                                content_settings.cache_control = cache_control
                                blob_client.set_http_headers(content_settings=content_settings)
                                self.stdout.write(f"  [UPDATED] {blob.name}")
                            total_updated += 1

                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"  [ERROR] {blob.name}: {str(e)}"))
                        total_errors += 1

                self.stdout.write(f"Processed {blob_count} blobs in {container_name}")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error processing container {container_name}: {str(e)}"))
                total_errors += 1

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Summary:")
        if dry_run:
            self.stdout.write(f"  Would update: {total_updated} blobs")
        else:
            self.stdout.write(f"  Updated: {total_updated} blobs")
        self.stdout.write(f"  Skipped (already set): {total_skipped} blobs")
        self.stdout.write(f"  Errors: {total_errors} blobs")
        self.stdout.write("=" * 60)
