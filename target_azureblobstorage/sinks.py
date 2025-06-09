"""target-azureblobstorage target sink class, which handles writing streams."""

from __future__ import annotations
from typing import Any, Sequence

from singer_sdk import Target
from singer_sdk.sinks import BatchSink
from azure.storage.blob import BlobServiceClient, BlobClient
import pandas as pd
from datetime import datetime

class TargetAzureBlobStorageSink(BatchSink):
    """target-azureblobstorage target sink class."""

    max_size = 100000  # Max records to write in one batch

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self) -> None:

        start_dt = datetime.now()

        self.connection_string = self.config.get("azure_storage_account_connection_string", None)
        self.container_name = self.config.get("container_name")
        self.filename_pattern = self.config.get("filename_pattern")
        self.filename = self.render_filename(self.filename_pattern, self.stream_name, start_dt) + '.csv'
        self.incomplete_filename = self.render_filename(f"{self.filename_pattern}__incomplete__", self.stream_name, start_dt) + '.csv'

        
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=self.incomplete_filename)

        return super().setup()

    def clean_up(self) -> None:

        if self.blob_client.exists():
            # Wrap up with the correct name (no rename operation?)
            final_blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=self.filename)
            final_blob_client.start_copy_from_url(self.blob_client.url)

            self.blob_client.delete_blob()

        return super().clean_up()


    def process_batch(self, context: dict) -> None:
        """Write out any prepped records and return once fully written.

        Args:
            context: Stream partition or context dictionary.
        """

        if "records" not in context:
            raise ValueError("No records found in context. Ensure records are being processed correctly.")
        
        csv_string = pd.DataFrame(context["records"]).to_csv()
        csv_bytes = str.encode(csv_string)

        if not self.blob_client.exists():
            self.blob_client.create_append_blob()

        self.blob_client.append_block(csv_bytes)
        

    def render_filename(self, filename_pattern, stream_name: str, datetime: datetime = datetime.now()) -> str:
        """Render the filename for the current batch.
        """

        mapping = {"datetime": datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                   "date": datetime.strftime("%Y-%m-%d"),
                   "stream": stream_name}

        # TODO: handle multiple formats
        return f"{filename_pattern.format(**mapping)}"
