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
        self.container_name = self.config.get("container_name", "landing")
        self.filename_pattern = self.config.get("filename_pattern", "{stream}_{datetime}")
        self.filename = self.render_filename(self.filename_pattern, self.stream_name, start_dt) + '.csv'
        self.incomplete_filename = self.render_filename(f"{self.filename_pattern}__incomplete__", self.stream_name, start_dt) + '.csv'

        
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=self.incomplete_filename)

        return super().setup()

    def clean_up(self) -> None:

        final_blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=self.filename)
        final_blob_client.start_copy_from_url(self.blob_client.url)

        self.blob_client.delete_blob()

        return super().clean_up()

    # def start_batch(self, context: dict) -> None:
    #     """Start a batch.

    #     Developers may optionally add additional markers to the `context` dict,
    #     which is unique to this batch.

    #     Args:
    #         context: Stream partition or context dictionary.
    #     """
    #     # Sample:
    #     # ------
    #     # batch_key = context["batch_id"]
    #     # context["file_path"] = f"{batch_key}.csv"

    # def process_record(self, record: dict, context: dict) -> None:
    #     """Process the record.

    #     Developers may optionally read or write additional markers within the
    #     passed `context` dict from the current batch.

    #     Args:
    #         record: Individual record in the stream.
    #         context: Stream partition or context dictionary.
    #     """
    #     # Sample:
    #     # ------
    #     # with open(context["file_path"], "a") as csvfile:
    #     #     csvfile.write(record)

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
        
        # Sample:
        # ------
        # client.upload(context["file_path"])  # Upload file
        # Path(context["file_path"]).unlink()  # Delete local copy

    def render_filename(self, filename_pattern, stream_name: str, datetime: datetime = datetime.now()) -> str:
        """Render the filename for the current batch.
        """

        mapping = {"datetime": datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                   "date": datetime.strftime("%Y-%m-%d"),
                   "stream": stream_name}

        # TODO: handle multiple formats
        return f"{filename_pattern.format(**mapping)}"
