<h1 align="center">
  <br>
  <a href="https://aiboxlab.org/en/"><img src="https://aiboxlab.org/img/logo-aibox.png" alt="AiBox Lab" width="200"></a>
  <br>
  aibox-data-lake
  <br>
</h1>

<h4 align="center">AiBox Data Lake Toolkit.</h4>


[![Python](https://img.shields.io/pypi/pyversions/aibox-data-lake.svg)](https://badge.fury.io/py/aibox-data-lake)
[![PyPI](https://badge.fury.io/py/aibox-data-lake.svg)](https://badge.fury.io/py/aibox-data-lake)

# Quickstart

O AiBox Data Lake Toolkit é uma biblioteca enxuta que fornece acesso uniforme a Data Lakes em provedores de nuvem (e.g., GCP). Essa biblioteca foi desenvolvida para uso interno, mas grande parte do código-fonte e dos padrões adotados são comuns e podem ser aplicados a outros contextos.

A biblioteca pode ser instalada usando o seu gerenciador de pacotes preferido:

```sh
uv add aibox-data-lake
uv pip install aibox-data-lake
pip install aibox-data-lake
```

Depois de instalada, a biblioteca pode ser configurada através do `aibox-dl config`. A biblioteca fornece um registro simples de buckets, que associa a URL de um bucket (e.g., `gs://my-bucket`) a um nome (e.g., `bronze`). As credenciais da nuvem devem ser configuradas pelas bibliotecas cliente do provedor (e.g., `google-cloud-storage`, `boto3`). A CLI também oferece outros recursos, como listagem de objetos e leitura de metadados de datasets.

Também é possível utilizar a biblioteca com a URL do bucket diretamente, sem a necessidade de configuração extra.

A principal classe para acesso e manipulação programática do Data Lake é a [aibox.data_lake.Client](./src/aibox/data_lake/client.py). Essa classe fornece métodos para operações comuns no Data Lake, como leitura de arquivos específicos ou carregamento de datasets. Exemplo de uso:

```python
from aibox.data_lake import Client

# Load the configuration and authenticates
#   to the cloud providers.
client = Client()

# List all objects on a bucket
client.list_objects("<bucket-name>")

# Loads a structured data source (e.g.,
#   .parquet, .csv).
ds = client.get_tabular_dataset("<bucket-name>", "<dataset-prefix>")

# A structured data source can be easily
#   loaded to a DataFrame
ds.to_frame()
```
