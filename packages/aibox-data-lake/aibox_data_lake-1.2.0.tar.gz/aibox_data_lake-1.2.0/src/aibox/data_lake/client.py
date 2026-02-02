"""Client para interação
com o Data Lake.
"""

from typing import IO

from aibox.data_lake.config import Config
from aibox.data_lake.core import Blob, Bucket, TabularDataset
from aibox.data_lake.factory import get_bucket


class Client:
    """Classe para interação com
    o Data Lake.

    Permite acessar todas as funcionalidades
    do Data Lake, incluindo o carregamento
    de datasets, listagem de objetos, gerenciamento
    de metadados, entre outros.
    """

    def __init__(self, config: Config | None = None):
        self._config = config if config is not None else Config()
        self._buckets = {
            name: get_bucket(bucket_url)
            for name, bucket_url in self.config.registered_buckets.items()
        }

    @property
    def config(self) -> Config:
        return self._config

    @property
    def buckets(self) -> dict[str, Bucket]:
        return self._buckets

    def open_object(self, bucket: str, name: str, mode: str, **kwargs) -> IO:
        """Abre um objeto no modo escolhido.

        Args:
            bucket: nome de bucket registrado
                ou URL (e.g., s3://bucket,
                gs://bucket).
            name: nome do objeto.
            mode: modo de abertura.
            **kwargs: parâmetros extras.

        Returns:
            IO: file object.
        """
        return self._get_bucket(bucket).open(name, mode, **kwargs)

    def list_objects(
        self,
        bucket: str,
        prefix: str | None = None,
        glob: str | None = None,
    ) -> list[Blob]:
        """Lista todos os objetos em
        um dos buckets do Data Lake
        que satisfaçam os filtros.

        Args:
            bucket: nome de bucket registrado
                ou URL (e.g., s3://bucket,
                gs://bucket).
            prefix: prefixo dos objetos.
            glob: glob para match de objetos.

        Returns:
            list[Blob]: objetos que satisfazem
                os filtros.
        """
        return self._get_bucket(bucket).list(prefix=prefix, glob=glob)

    def get_tabular_dataset(
        self,
        bucket: str,
        dataset_prefix: str,
        extension: str = "parquet",
    ) -> TabularDataset:
        """Carrega uma fonte de dados estruturada
        através de um identificador da fonte de dados
        e o bucket.

        Args:
            bucket: nome de bucket registrado
                ou URL (e.g., s3://bucket,
                gs://bucket).
            dataset_prefix: prefixo dos dados para
                o dataset no bucket.
            extension: extensão dos dados do dataset.

        Returns:
            TabularDataset: dataset tabular.
        """
        return TabularDataset(self._get_bucket(bucket), dataset_prefix, extension)

    def _get_bucket(self, bucket: str) -> Bucket:
        try:
            return self.buckets[bucket]
        except KeyError:
            return get_bucket(bucket)
