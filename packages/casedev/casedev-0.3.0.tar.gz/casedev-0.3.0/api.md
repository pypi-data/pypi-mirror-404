# Compute

## V1

Types:

```python
from casedev.types.compute import V1GetUsageResponse
```

Methods:

- <code title="get /compute/v1/pricing">client.compute.v1.<a href="./src/casedev/resources/compute/v1/v1.py">get_pricing</a>() -> None</code>
- <code title="get /compute/v1/usage">client.compute.v1.<a href="./src/casedev/resources/compute/v1/v1.py">get_usage</a>(\*\*<a href="src/casedev/types/compute/v1_get_usage_params.py">params</a>) -> <a href="./src/casedev/types/compute/v1_get_usage_response.py">V1GetUsageResponse</a></code>

### Environments

Types:

```python
from casedev.types.compute.v1 import (
    EnvironmentCreateResponse,
    EnvironmentRetrieveResponse,
    EnvironmentListResponse,
    EnvironmentDeleteResponse,
    EnvironmentSetDefaultResponse,
)
```

Methods:

- <code title="post /compute/v1/environments">client.compute.v1.environments.<a href="./src/casedev/resources/compute/v1/environments.py">create</a>(\*\*<a href="src/casedev/types/compute/v1/environment_create_params.py">params</a>) -> <a href="./src/casedev/types/compute/v1/environment_create_response.py">EnvironmentCreateResponse</a></code>
- <code title="get /compute/v1/environments/{name}">client.compute.v1.environments.<a href="./src/casedev/resources/compute/v1/environments.py">retrieve</a>(name) -> <a href="./src/casedev/types/compute/v1/environment_retrieve_response.py">EnvironmentRetrieveResponse</a></code>
- <code title="get /compute/v1/environments">client.compute.v1.environments.<a href="./src/casedev/resources/compute/v1/environments.py">list</a>() -> <a href="./src/casedev/types/compute/v1/environment_list_response.py">EnvironmentListResponse</a></code>
- <code title="delete /compute/v1/environments/{name}">client.compute.v1.environments.<a href="./src/casedev/resources/compute/v1/environments.py">delete</a>(name) -> <a href="./src/casedev/types/compute/v1/environment_delete_response.py">EnvironmentDeleteResponse</a></code>
- <code title="post /compute/v1/environments/{name}/default">client.compute.v1.environments.<a href="./src/casedev/resources/compute/v1/environments.py">set_default</a>(name) -> <a href="./src/casedev/types/compute/v1/environment_set_default_response.py">EnvironmentSetDefaultResponse</a></code>

### Secrets

Types:

```python
from casedev.types.compute.v1 import (
    SecretCreateResponse,
    SecretListResponse,
    SecretDeleteGroupResponse,
    SecretRetrieveGroupResponse,
    SecretUpdateGroupResponse,
)
```

Methods:

- <code title="post /compute/v1/secrets">client.compute.v1.secrets.<a href="./src/casedev/resources/compute/v1/secrets.py">create</a>(\*\*<a href="src/casedev/types/compute/v1/secret_create_params.py">params</a>) -> <a href="./src/casedev/types/compute/v1/secret_create_response.py">SecretCreateResponse</a></code>
- <code title="get /compute/v1/secrets">client.compute.v1.secrets.<a href="./src/casedev/resources/compute/v1/secrets.py">list</a>(\*\*<a href="src/casedev/types/compute/v1/secret_list_params.py">params</a>) -> <a href="./src/casedev/types/compute/v1/secret_list_response.py">SecretListResponse</a></code>
- <code title="delete /compute/v1/secrets/{group}">client.compute.v1.secrets.<a href="./src/casedev/resources/compute/v1/secrets.py">delete_group</a>(group, \*\*<a href="src/casedev/types/compute/v1/secret_delete_group_params.py">params</a>) -> <a href="./src/casedev/types/compute/v1/secret_delete_group_response.py">SecretDeleteGroupResponse</a></code>
- <code title="get /compute/v1/secrets/{group}">client.compute.v1.secrets.<a href="./src/casedev/resources/compute/v1/secrets.py">retrieve_group</a>(group, \*\*<a href="src/casedev/types/compute/v1/secret_retrieve_group_params.py">params</a>) -> <a href="./src/casedev/types/compute/v1/secret_retrieve_group_response.py">SecretRetrieveGroupResponse</a></code>
- <code title="put /compute/v1/secrets/{group}">client.compute.v1.secrets.<a href="./src/casedev/resources/compute/v1/secrets.py">update_group</a>(group, \*\*<a href="src/casedev/types/compute/v1/secret_update_group_params.py">params</a>) -> <a href="./src/casedev/types/compute/v1/secret_update_group_response.py">SecretUpdateGroupResponse</a></code>

# Format

## V1

Methods:

- <code title="post /format/v1/document">client.format.v1.<a href="./src/casedev/resources/format/v1/v1.py">create_document</a>(\*\*<a href="src/casedev/types/format/v1_create_document_params.py">params</a>) -> BinaryAPIResponse</code>

### Templates

Types:

```python
from casedev.types.format.v1 import (
    TemplateCreateResponse,
    TemplateRetrieveResponse,
    TemplateListResponse,
)
```

Methods:

- <code title="post /format/v1/templates">client.format.v1.templates.<a href="./src/casedev/resources/format/v1/templates.py">create</a>(\*\*<a href="src/casedev/types/format/v1/template_create_params.py">params</a>) -> <a href="./src/casedev/types/format/v1/template_create_response.py">TemplateCreateResponse</a></code>
- <code title="get /format/v1/templates/{id}">client.format.v1.templates.<a href="./src/casedev/resources/format/v1/templates.py">retrieve</a>(id) -> <a href="./src/casedev/types/format/v1/template_retrieve_response.py">TemplateRetrieveResponse</a></code>
- <code title="get /format/v1/templates">client.format.v1.templates.<a href="./src/casedev/resources/format/v1/templates.py">list</a>(\*\*<a href="src/casedev/types/format/v1/template_list_params.py">params</a>) -> <a href="./src/casedev/types/format/v1/template_list_response.py">TemplateListResponse</a></code>

# Llm

Types:

```python
from casedev.types import LlmGetConfigResponse
```

Methods:

- <code title="get /llm/config">client.llm.<a href="./src/casedev/resources/llm/llm.py">get_config</a>() -> <a href="./src/casedev/types/llm_get_config_response.py">LlmGetConfigResponse</a></code>

## V1

Types:

```python
from casedev.types.llm import V1CreateEmbeddingResponse, V1ListModelsResponse
```

Methods:

- <code title="post /llm/v1/embeddings">client.llm.v1.<a href="./src/casedev/resources/llm/v1/v1.py">create_embedding</a>(\*\*<a href="src/casedev/types/llm/v1_create_embedding_params.py">params</a>) -> <a href="./src/casedev/types/llm/v1_create_embedding_response.py">V1CreateEmbeddingResponse</a></code>
- <code title="get /llm/v1/models">client.llm.v1.<a href="./src/casedev/resources/llm/v1/v1.py">list_models</a>() -> <a href="./src/casedev/types/llm/v1_list_models_response.py">V1ListModelsResponse</a></code>

### Chat

Types:

```python
from casedev.types.llm.v1 import ChatCreateCompletionResponse
```

Methods:

- <code title="post /llm/v1/chat/completions">client.llm.v1.chat.<a href="./src/casedev/resources/llm/v1/chat.py">create_completion</a>(\*\*<a href="src/casedev/types/llm/v1/chat_create_completion_params.py">params</a>) -> <a href="./src/casedev/types/llm/v1/chat_create_completion_response.py">ChatCreateCompletionResponse</a></code>

# Ocr

## V1

Types:

```python
from casedev.types.ocr import V1RetrieveResponse, V1DownloadResponse, V1ProcessResponse
```

Methods:

- <code title="get /ocr/v1/{id}">client.ocr.v1.<a href="./src/casedev/resources/ocr/v1.py">retrieve</a>(id) -> <a href="./src/casedev/types/ocr/v1_retrieve_response.py">V1RetrieveResponse</a></code>
- <code title="get /ocr/v1/{id}/download/{type}">client.ocr.v1.<a href="./src/casedev/resources/ocr/v1.py">download</a>(type, \*, id) -> str</code>
- <code title="post /ocr/v1/process">client.ocr.v1.<a href="./src/casedev/resources/ocr/v1.py">process</a>(\*\*<a href="src/casedev/types/ocr/v1_process_params.py">params</a>) -> <a href="./src/casedev/types/ocr/v1_process_response.py">V1ProcessResponse</a></code>

# Search

## V1

Types:

```python
from casedev.types.search import (
    V1AnswerResponse,
    V1ContentsResponse,
    V1ResearchResponse,
    V1RetrieveResearchResponse,
    V1SearchResponse,
    V1SimilarResponse,
)
```

Methods:

- <code title="post /search/v1/answer">client.search.v1.<a href="./src/casedev/resources/search/v1.py">answer</a>(\*\*<a href="src/casedev/types/search/v1_answer_params.py">params</a>) -> <a href="./src/casedev/types/search/v1_answer_response.py">V1AnswerResponse</a></code>
- <code title="post /search/v1/contents">client.search.v1.<a href="./src/casedev/resources/search/v1.py">contents</a>(\*\*<a href="src/casedev/types/search/v1_contents_params.py">params</a>) -> <a href="./src/casedev/types/search/v1_contents_response.py">V1ContentsResponse</a></code>
- <code title="post /search/v1/research">client.search.v1.<a href="./src/casedev/resources/search/v1.py">research</a>(\*\*<a href="src/casedev/types/search/v1_research_params.py">params</a>) -> <a href="./src/casedev/types/search/v1_research_response.py">V1ResearchResponse</a></code>
- <code title="get /search/v1/research/{id}">client.search.v1.<a href="./src/casedev/resources/search/v1.py">retrieve_research</a>(id, \*\*<a href="src/casedev/types/search/v1_retrieve_research_params.py">params</a>) -> <a href="./src/casedev/types/search/v1_retrieve_research_response.py">V1RetrieveResearchResponse</a></code>
- <code title="post /search/v1/search">client.search.v1.<a href="./src/casedev/resources/search/v1.py">search</a>(\*\*<a href="src/casedev/types/search/v1_search_params.py">params</a>) -> <a href="./src/casedev/types/search/v1_search_response.py">V1SearchResponse</a></code>
- <code title="post /search/v1/similar">client.search.v1.<a href="./src/casedev/resources/search/v1.py">similar</a>(\*\*<a href="src/casedev/types/search/v1_similar_params.py">params</a>) -> <a href="./src/casedev/types/search/v1_similar_response.py">V1SimilarResponse</a></code>

# Vault

Types:

```python
from casedev.types import (
    VaultCreateResponse,
    VaultRetrieveResponse,
    VaultListResponse,
    VaultIngestResponse,
    VaultSearchResponse,
    VaultUploadResponse,
)
```

Methods:

- <code title="post /vault">client.vault.<a href="./src/casedev/resources/vault/vault.py">create</a>(\*\*<a href="src/casedev/types/vault_create_params.py">params</a>) -> <a href="./src/casedev/types/vault_create_response.py">VaultCreateResponse</a></code>
- <code title="get /vault/{id}">client.vault.<a href="./src/casedev/resources/vault/vault.py">retrieve</a>(id) -> <a href="./src/casedev/types/vault_retrieve_response.py">VaultRetrieveResponse</a></code>
- <code title="get /vault">client.vault.<a href="./src/casedev/resources/vault/vault.py">list</a>() -> <a href="./src/casedev/types/vault_list_response.py">VaultListResponse</a></code>
- <code title="post /vault/{id}/ingest/{objectId}">client.vault.<a href="./src/casedev/resources/vault/vault.py">ingest</a>(object_id, \*, id) -> <a href="./src/casedev/types/vault_ingest_response.py">VaultIngestResponse</a></code>
- <code title="post /vault/{id}/search">client.vault.<a href="./src/casedev/resources/vault/vault.py">search</a>(id, \*\*<a href="src/casedev/types/vault_search_params.py">params</a>) -> <a href="./src/casedev/types/vault_search_response.py">VaultSearchResponse</a></code>
- <code title="post /vault/{id}/upload">client.vault.<a href="./src/casedev/resources/vault/vault.py">upload</a>(id, \*\*<a href="src/casedev/types/vault_upload_params.py">params</a>) -> <a href="./src/casedev/types/vault_upload_response.py">VaultUploadResponse</a></code>

## Graphrag

Types:

```python
from casedev.types.vault import GraphragGetStatsResponse, GraphragInitResponse
```

Methods:

- <code title="get /vault/{id}/graphrag/stats">client.vault.graphrag.<a href="./src/casedev/resources/vault/graphrag.py">get_stats</a>(id) -> <a href="./src/casedev/types/vault/graphrag_get_stats_response.py">GraphragGetStatsResponse</a></code>
- <code title="post /vault/{id}/graphrag/init">client.vault.graphrag.<a href="./src/casedev/resources/vault/graphrag.py">init</a>(id) -> <a href="./src/casedev/types/vault/graphrag_init_response.py">GraphragInitResponse</a></code>

## Objects

Types:

```python
from casedev.types.vault import (
    ObjectRetrieveResponse,
    ObjectListResponse,
    ObjectCreatePresignedURLResponse,
    ObjectDownloadResponse,
    ObjectGetTextResponse,
)
```

Methods:

- <code title="get /vault/{id}/objects/{objectId}">client.vault.objects.<a href="./src/casedev/resources/vault/objects.py">retrieve</a>(object_id, \*, id) -> <a href="./src/casedev/types/vault/object_retrieve_response.py">ObjectRetrieveResponse</a></code>
- <code title="get /vault/{id}/objects">client.vault.objects.<a href="./src/casedev/resources/vault/objects.py">list</a>(id) -> <a href="./src/casedev/types/vault/object_list_response.py">ObjectListResponse</a></code>
- <code title="post /vault/{id}/objects/{objectId}/presigned-url">client.vault.objects.<a href="./src/casedev/resources/vault/objects.py">create_presigned_url</a>(object_id, \*, id, \*\*<a href="src/casedev/types/vault/object_create_presigned_url_params.py">params</a>) -> <a href="./src/casedev/types/vault/object_create_presigned_url_response.py">ObjectCreatePresignedURLResponse</a></code>
- <code title="get /vault/{id}/objects/{objectId}/download">client.vault.objects.<a href="./src/casedev/resources/vault/objects.py">download</a>(object_id, \*, id) -> str</code>
- <code title="get /vault/{id}/objects/{objectId}/text">client.vault.objects.<a href="./src/casedev/resources/vault/objects.py">get_text</a>(object_id, \*, id) -> <a href="./src/casedev/types/vault/object_get_text_response.py">ObjectGetTextResponse</a></code>

# Voice

## Streaming

Types:

```python
from casedev.types.voice import StreamingGetURLResponse
```

Methods:

- <code title="get /voice/streaming/url">client.voice.streaming.<a href="./src/casedev/resources/voice/streaming.py">get_url</a>() -> <a href="./src/casedev/types/voice/streaming_get_url_response.py">StreamingGetURLResponse</a></code>

## Transcription

Types:

```python
from casedev.types.voice import TranscriptionCreateResponse, TranscriptionRetrieveResponse
```

Methods:

- <code title="post /voice/transcription">client.voice.transcription.<a href="./src/casedev/resources/voice/transcription.py">create</a>(\*\*<a href="src/casedev/types/voice/transcription_create_params.py">params</a>) -> <a href="./src/casedev/types/voice/transcription_create_response.py">TranscriptionCreateResponse</a></code>
- <code title="get /voice/transcription/{id}">client.voice.transcription.<a href="./src/casedev/resources/voice/transcription.py">retrieve</a>(id) -> <a href="./src/casedev/types/voice/transcription_retrieve_response.py">TranscriptionRetrieveResponse</a></code>

## V1

Types:

```python
from casedev.types.voice import V1ListVoicesResponse
```

Methods:

- <code title="get /voice/v1/voices">client.voice.v1.<a href="./src/casedev/resources/voice/v1/v1.py">list_voices</a>(\*\*<a href="src/casedev/types/voice/v1_list_voices_params.py">params</a>) -> <a href="./src/casedev/types/voice/v1_list_voices_response.py">V1ListVoicesResponse</a></code>

### Speak

Methods:

- <code title="post /voice/v1/speak">client.voice.v1.speak.<a href="./src/casedev/resources/voice/v1/speak.py">create</a>(\*\*<a href="src/casedev/types/voice/v1/speak_create_params.py">params</a>) -> BinaryAPIResponse</code>
