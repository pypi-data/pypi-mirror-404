import io
from typing import TYPE_CHECKING, Any, Union

import polars as pl
from evaluation_embedder.src.connectors import DatasetConnector
from evaluation_embedder.src.settings import MinioDatasetConnectorSettings

from minio import Minio

if TYPE_CHECKING:
    from evaluation_embedder.src.datasets import Dataset


class MinioDatasetConnector(DatasetConnector[MinioDatasetConnectorSettings]):

    def __init__(self, config: MinioDatasetConnectorSettings):
        super().__init__(config)
        self.client = Minio(
            self.config.endpoint.replace("http://", "").replace("https://", ""),
            access_key=self.config.access_key.get_secret_value(),
            secret_key=self.config.secret_key.get_secret_value(),
            secure=self.config.endpoint.startswith("https://"),
        )

    def _load(self) -> Union[pl.DataFrame, pl.LazyFrame]:
        response = self.client.get_object(self.config.bucket, self.config.key)
        try:
            buffer = io.BytesIO(response.read())
        finally:
            response.close()
            response.release_conn()
        df = pl.read_parquet(buffer)
        return df

    def to(self, ds: "Dataset[Any]") -> None:
        df = ds.polars
        buffer = io.BytesIO()
        df.write_parquet(buffer)
        buffer.seek(0)
        self.client.put_object(
            bucket_name=self.config.bucket,
            object_name=self.config.key,
            data=buffer,
            length=buffer.getbuffer().nbytes,
            content_type="application/octet-stream",
        )
