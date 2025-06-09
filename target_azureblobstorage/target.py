"""target-azureblobstorage target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_azureblobstorage.sinks import (
    TargetAzureBlobStorageSink,
)


class TargetAzureBlobStorage(Target):
    """Sample target for target-azureblobstorage."""

    name = "target-azureblobstorage"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "azure_storage_account_connection_string",
            th.StringType(nullable=False),
            secret=True,  # Flag config as protected.
            required=True,
            title="Azure Storage Account Connection String",
            description="The connection string for the Azure Storage Account",
        ),
        th.Property(
            "filename_pattern",
            th.StringType(nullable=True, default="{stream}_{datetime}"),
            required=False,
            title="Destination file naming pattern",
            description="The naming pattern for the destination files in Azure Blob Storage. Defaults to '{stream}_{datetime}.csv. Possible substitutions: {stream},{date},{datetime}.'",
        ),
        th.Property(
            "container_name",
            th.StringType(nullable=True, default="landing"),
            required=False,
            title="Azure Blob Storage Container Name",
            description="The name of the Azure Blob Storage container where data will be stored. Defaults to 'landing'.",
        )
    ).to_dict()

    # TODO: support different types of authentication
    # TODO: support different file formats (Parquet first)


    default_sink_class = TargetAzureBlobStorageSink


if __name__ == "__main__":
    TargetAzureBlobStorage.cli()
