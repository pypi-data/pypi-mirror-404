# Projects

Types:

```python
from reminix.types import Project
```

Methods:

- <code title="get /projects/current">client.projects.<a href="./src/reminix/resources/projects.py">retrieve_current</a>() -> <a href="./src/reminix/types/project.py">Project</a></code>

# Agents

Types:

```python
from reminix.types import (
    Agent,
    AgentConfig,
    AgentKnowledgeBaseConfig,
    AgentMemoryConfig,
    ChatMessage,
    StreamChunk,
    AgentChatResponse,
    AgentInvokeResponse,
)
```

Methods:

- <code title="get /agents/{name}">client.agents.<a href="./src/reminix/resources/agents.py">retrieve</a>(name) -> <a href="./src/reminix/types/agent.py">Agent</a></code>
- <code title="get /agents">client.agents.<a href="./src/reminix/resources/agents.py">list</a>(\*\*<a href="src/reminix/types/agent_list_params.py">params</a>) -> <a href="./src/reminix/types/agent.py">SyncCursor[Agent]</a></code>
- <code title="post /agents/{name}/chat">client.agents.<a href="./src/reminix/resources/agents.py">chat</a>(name, \*\*<a href="src/reminix/types/agent_chat_params.py">params</a>) -> <a href="./src/reminix/types/agent_chat_response.py">AgentChatResponse</a></code>
- <code title="post /agents/{name}/invoke">client.agents.<a href="./src/reminix/resources/agents.py">invoke</a>(name, \*\*<a href="src/reminix/types/agent_invoke_params.py">params</a>) -> <a href="./src/reminix/types/agent_invoke_response.py">AgentInvokeResponse</a></code>

# Tools

Types:

```python
from reminix.types import Tool, ToolCallResponse
```

Methods:

- <code title="get /tools/{name}">client.tools.<a href="./src/reminix/resources/tools.py">retrieve</a>(name) -> <a href="./src/reminix/types/tool.py">Tool</a></code>
- <code title="get /tools">client.tools.<a href="./src/reminix/resources/tools.py">list</a>(\*\*<a href="src/reminix/types/tool_list_params.py">params</a>) -> <a href="./src/reminix/types/tool.py">SyncCursor[Tool]</a></code>
- <code title="post /tools/{name}/call">client.tools.<a href="./src/reminix/resources/tools.py">call</a>(name, \*\*<a href="src/reminix/types/tool_call_params.py">params</a>) -> <a href="./src/reminix/types/tool_call_response.py">ToolCallResponse</a></code>

# ClientTokens

Types:

```python
from reminix.types import ClientTokenCreateResponse
```

Methods:

- <code title="post /client-tokens">client.client_tokens.<a href="./src/reminix/resources/client_tokens.py">create</a>(\*\*<a href="src/reminix/types/client_token_create_params.py">params</a>) -> <a href="./src/reminix/types/client_token_create_response.py">ClientTokenCreateResponse</a></code>
- <code title="delete /client-tokens/{id}">client.client_tokens.<a href="./src/reminix/resources/client_tokens.py">revoke</a>(id) -> None</code>

# ExecutionLogs

Types:

```python
from reminix.types import ExecutionLog
```

Methods:

- <code title="get /execution-logs/{id}">client.execution_logs.<a href="./src/reminix/resources/execution_logs.py">retrieve</a>(id) -> <a href="./src/reminix/types/execution_log.py">ExecutionLog</a></code>
- <code title="get /execution-logs">client.execution_logs.<a href="./src/reminix/resources/execution_logs.py">list</a>(\*\*<a href="src/reminix/types/execution_log_list_params.py">params</a>) -> <a href="./src/reminix/types/execution_log.py">SyncCursor[ExecutionLog]</a></code>

# Conversations

Types:

```python
from reminix.types import Conversation, ConversationRetrieveResponse
```

Methods:

- <code title="get /conversations/{id}">client.conversations.<a href="./src/reminix/resources/conversations.py">retrieve</a>(id) -> <a href="./src/reminix/types/conversation_retrieve_response.py">ConversationRetrieveResponse</a></code>
- <code title="get /conversations">client.conversations.<a href="./src/reminix/resources/conversations.py">list</a>(\*\*<a href="src/reminix/types/conversation_list_params.py">params</a>) -> <a href="./src/reminix/types/conversation.py">SyncCursor[Conversation]</a></code>
- <code title="delete /conversations/{id}">client.conversations.<a href="./src/reminix/resources/conversations.py">delete</a>(id) -> None</code>

# Memory

Types:

```python
from reminix.types import Memory, MemoryListResponse, MemoryDeleteAllResponse
```

Methods:

- <code title="get /memory/{key}">client.memory.<a href="./src/reminix/resources/memory.py">retrieve</a>(key) -> <a href="./src/reminix/types/memory.py">Memory</a></code>
- <code title="get /memory">client.memory.<a href="./src/reminix/resources/memory.py">list</a>() -> <a href="./src/reminix/types/memory_list_response.py">MemoryListResponse</a></code>
- <code title="delete /memory/{key}">client.memory.<a href="./src/reminix/resources/memory.py">delete</a>(key) -> None</code>
- <code title="delete /memory">client.memory.<a href="./src/reminix/resources/memory.py">delete_all</a>() -> <a href="./src/reminix/types/memory_delete_all_response.py">MemoryDeleteAllResponse</a></code>
- <code title="post /memory">client.memory.<a href="./src/reminix/resources/memory.py">store</a>(\*\*<a href="src/reminix/types/memory_store_params.py">params</a>) -> <a href="./src/reminix/types/memory.py">Memory</a></code>

# Knowledge

Types:

```python
from reminix.types import KnowledgeSearchResponse
```

Methods:

- <code title="post /knowledge/search">client.knowledge.<a href="./src/reminix/resources/knowledge/knowledge.py">search</a>(\*\*<a href="src/reminix/types/knowledge_search_params.py">params</a>) -> <a href="./src/reminix/types/knowledge_search_response.py">KnowledgeSearchResponse</a></code>

## Collections

Types:

```python
from reminix.types.knowledge import KnowledgeCollection
```

Methods:

- <code title="post /knowledge/collections">client.knowledge.collections.<a href="./src/reminix/resources/knowledge/collections/collections.py">create</a>(\*\*<a href="src/reminix/types/knowledge/collection_create_params.py">params</a>) -> <a href="./src/reminix/types/knowledge/knowledge_collection.py">KnowledgeCollection</a></code>
- <code title="get /knowledge/collections/{id}">client.knowledge.collections.<a href="./src/reminix/resources/knowledge/collections/collections.py">retrieve</a>(id) -> <a href="./src/reminix/types/knowledge/knowledge_collection.py">KnowledgeCollection</a></code>
- <code title="patch /knowledge/collections/{id}">client.knowledge.collections.<a href="./src/reminix/resources/knowledge/collections/collections.py">update</a>(id, \*\*<a href="src/reminix/types/knowledge/collection_update_params.py">params</a>) -> <a href="./src/reminix/types/knowledge/knowledge_collection.py">KnowledgeCollection</a></code>
- <code title="get /knowledge/collections">client.knowledge.collections.<a href="./src/reminix/resources/knowledge/collections/collections.py">list</a>(\*\*<a href="src/reminix/types/knowledge/collection_list_params.py">params</a>) -> <a href="./src/reminix/types/knowledge/knowledge_collection.py">SyncCursor[KnowledgeCollection]</a></code>
- <code title="delete /knowledge/collections/{id}">client.knowledge.collections.<a href="./src/reminix/resources/knowledge/collections/collections.py">delete</a>(id) -> None</code>

### Documents

Types:

```python
from reminix.types.knowledge.collections import (
    KnowledgeDocument,
    DocumentProcessResponse,
    DocumentUploadResponse,
)
```

Methods:

- <code title="get /knowledge/collections/{collectionId}/documents/{documentId}">client.knowledge.collections.documents.<a href="./src/reminix/resources/knowledge/collections/documents.py">retrieve</a>(document_id, \*, collection_id) -> <a href="./src/reminix/types/knowledge/collections/knowledge_document.py">KnowledgeDocument</a></code>
- <code title="get /knowledge/collections/{id}/documents">client.knowledge.collections.documents.<a href="./src/reminix/resources/knowledge/collections/documents.py">list</a>(id, \*\*<a href="src/reminix/types/knowledge/collections/document_list_params.py">params</a>) -> <a href="./src/reminix/types/knowledge/collections/knowledge_document.py">SyncCursor[KnowledgeDocument]</a></code>
- <code title="delete /knowledge/collections/{collectionId}/documents/{documentId}">client.knowledge.collections.documents.<a href="./src/reminix/resources/knowledge/collections/documents.py">delete</a>(document_id, \*, collection_id) -> None</code>
- <code title="post /knowledge/collections/{collectionId}/documents/{documentId}/process">client.knowledge.collections.documents.<a href="./src/reminix/resources/knowledge/collections/documents.py">process</a>(document_id, \*, collection_id, \*\*<a href="src/reminix/types/knowledge/collections/document_process_params.py">params</a>) -> <a href="./src/reminix/types/knowledge/collections/document_process_response.py">DocumentProcessResponse</a></code>
- <code title="post /knowledge/collections/{id}/documents">client.knowledge.collections.documents.<a href="./src/reminix/resources/knowledge/collections/documents.py">upload</a>(id, \*\*<a href="src/reminix/types/knowledge/collections/document_upload_params.py">params</a>) -> <a href="./src/reminix/types/knowledge/collections/document_upload_response.py">DocumentUploadResponse</a></code>
