# V1

## Memories

Types:

```python
from evermemos.types.v1 import (
    MemoryType,
    Metadata,
    MemoryDeleteResponse,
    MemoryAddResponse,
    MemoryGetResponse,
    MemorySearchResponse,
)
```

Methods:

- <code title="delete /api/v1/memories">client.v1.memories.<a href="./src/evermemos/resources/v1/memories/memories.py">delete</a>(\*\*<a href="src/evermemos/types/v1/memory_delete_params.py">params</a>) -> <a href="./src/evermemos/types/v1/memory_delete_response.py">MemoryDeleteResponse</a></code>
- <code title="post /api/v1/memories">client.v1.memories.<a href="./src/evermemos/resources/v1/memories/memories.py">add</a>(\*\*<a href="src/evermemos/types/v1/memory_add_params.py">params</a>) -> <a href="./src/evermemos/types/v1/memory_add_response.py">MemoryAddResponse</a></code>
- <code title="get /api/v1/memories">client.v1.memories.<a href="./src/evermemos/resources/v1/memories/memories.py">get</a>() -> <a href="./src/evermemos/types/v1/memory_get_response.py">MemoryGetResponse</a></code>
- <code title="get /api/v1/memories/search">client.v1.memories.<a href="./src/evermemos/resources/v1/memories/memories.py">search</a>() -> <a href="./src/evermemos/types/v1/memory_search_response.py">MemorySearchResponse</a></code>

### ConversationMeta

Types:

```python
from evermemos.types.v1.memories import (
    ConversationMetaCreateResponse,
    ConversationMetaUpdateResponse,
    ConversationMetaGetResponse,
)
```

Methods:

- <code title="post /api/v1/memories/conversation-meta">client.v1.memories.conversation_meta.<a href="./src/evermemos/resources/v1/memories/conversation_meta.py">create</a>(\*\*<a href="src/evermemos/types/v1/memories/conversation_meta_create_params.py">params</a>) -> <a href="./src/evermemos/types/v1/memories/conversation_meta_create_response.py">ConversationMetaCreateResponse</a></code>
- <code title="patch /api/v1/memories/conversation-meta">client.v1.memories.conversation_meta.<a href="./src/evermemos/resources/v1/memories/conversation_meta.py">update</a>(\*\*<a href="src/evermemos/types/v1/memories/conversation_meta_update_params.py">params</a>) -> <a href="./src/evermemos/types/v1/memories/conversation_meta_update_response.py">ConversationMetaUpdateResponse</a></code>
- <code title="get /api/v1/memories/conversation-meta">client.v1.memories.conversation_meta.<a href="./src/evermemos/resources/v1/memories/conversation_meta.py">get</a>() -> <a href="./src/evermemos/types/v1/memories/conversation_meta_get_response.py">ConversationMetaGetResponse</a></code>

## Status

### Request

Types:

```python
from evermemos.types.v1.status import RequestGetResponse
```

Methods:

- <code title="get /api/v1/status/request">client.v1.status.request.<a href="./src/evermemos/resources/v1/status/request.py">get</a>(\*\*<a href="src/evermemos/types/v1/status/request_get_params.py">params</a>) -> <a href="./src/evermemos/types/v1/status/request_get_response.py">RequestGetResponse</a></code>
