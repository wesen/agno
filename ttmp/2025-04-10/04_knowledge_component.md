# Agno Knowledge Component

The Knowledge component of Agno enables agents to retrieve and use information from various sources. This functionality, often referred to as Retrieval Augmented Generation (RAG), allows agents to access domain-specific knowledge beyond their training data.

## Core Architecture

The Knowledge component is built around several key abstractions:

- **AgentKnowledge**: Base class for all knowledge implementations
- **Document**: Represents a chunk of text with metadata
- **VectorDb**: Interface for vector database implementations
- **Embedder**: Interface for embedding models
- **ChunkingStrategy**: Interface for document chunking strategies
- **Reader**: Interface for document reading from various sources

This modular design allows for flexible combinations of knowledge sources, vector stores, embedding models, and processing strategies.

## Knowledge Sources

Agno supports a wide range of knowledge sources through specialized implementations:

- **TextKnowledgeBase**: Plain text files
- **PDFKnowledgeBase**: Local PDF files
- **PDFUrlKnowledgeBase**: PDFs from URLs
- **WebsiteKnowledgeBase**: Web pages with HTML processing
- **CSVKnowledgeBase**: Structured data in CSV format
- **JSONKnowledgeBase**: JSON data structures
- **DocKnowledgeBase**: Word documents (DOC)
- **DocxKnowledgeBase**: Word documents (DOCX)
- **ArxivKnowledgeBase**: Research papers from arXiv
- **WikipediaKnowledgeBase**: Articles from Wikipedia
- **YouTubeKnowledgeBase**: Transcripts from YouTube videos
- **S3PDFKnowledgeBase**: PDFs stored in S3 buckets
- **S3TextKnowledgeBase**: Text files stored in S3
- **FirecrawlKnowledgeBase**: Web content via the Firecrawl service

Each knowledge source handles:
- Loading content from its specific medium
- Processing text for optimal retrieval
- Chunking content into manageable pieces
- Embedding chunks for vector search
- Storing chunks in a vector database

## Vector Databases

The framework integrates with numerous vector databases through the `VectorDb` interface:

- **PgVector**: PostgreSQL with pgvector extension
- **ChromaDb**: ChromaDB vector database
- **QdrantDb**: Qdrant vector database
- **PineconeDb**: Pinecone vector database
- **CassandraDb**: Apache Cassandra
- **ClickhouseDb**: Clickhouse database
- **SinglestoreDb**: SingleStore database
- **UpstashDb**: Upstash Redis vector database
- **LanceDb**: LanceDB embedded vector database

The vector database implementation handles:
- Creating and managing collections
- Storing document embeddings
- Performing similarity searches
- Filtering results based on metadata
- Managing document updates and deletions

## Embedding Models

Text embedding is handled through the `Embedder` interface with implementations for various providers:

- **OpenAIEmbedder**: OpenAI embedding models
- **CohereEmbedder**: Cohere embedding models
- **MistralEmbedder**: Mistral embedding models
- **AzureEmbedder**: Azure OpenAI embedding models
- **GeminiEmbedder**: Google's Gemini embedding models
- **HuggingfaceEmbedder**: Hugging Face models
- **SentenceTransformerEmbedder**: Sentence Transformers library
- **TogetherEmbedder**: Together AI embedding models
- **OllamaEmbedder**: Local embedding models via Ollama
- **FireworksEmbedder**: Fireworks AI embedding models
- **VoyageAIEmbedder**: VoyageAI embedding models
- **QdrantFastEmbedder**: FastEmbed integration with Qdrant

## Chunking Strategies

Document chunking is crucial for effective retrieval. Agno offers several strategies:

- **FixedSizeChunking**: Simple chunking by character count
- **DocumentChunking**: Preserves document structure
- **SemanticChunking**: Creates chunks based on semantic meaning
- **RecursiveChunking**: Recursively splits documents
- **AgenticChunking**: Uses an AI agent to determine optimal chunking

## Search Types

Agno supports different search strategies:

- **VectorSearch**: Traditional embedding-based similarity search
- **KeywordSearch**: Text-based keyword matching
- **HybridSearch**: Combines vector and keyword search for better results

## Integration with Agents

Knowledge bases integrate with agents through a simple interface:

```python
agent = Agent(
    model=OpenAIChat(),
    instructions="Use the knowledge base to answer questions.",
    knowledge=knowledge_base,
    search_knowledge=True,
    num_knowledge_results=5,
    add_references=True,
    search_type="hybrid"
)
```

When a user asks a question, the agent:
1. Converts the question into a search query
2. Searches the knowledge base for relevant information
3. Incorporates the retrieved information into its context
4. Generates a response based on both the model's knowledge and the retrieved information
5. Optionally includes references to source material

## Key Files

- `/libs/agno/agno/knowledge/base.py`: Core AgentKnowledge class
- `/libs/agno/agno/knowledge/document.py`: Document representation
- `/libs/agno/agno/knowledge/vector_dbs/`: Vector database implementations
- `/libs/agno/agno/knowledge/embedders/`: Embedding model implementations
- `/libs/agno/agno/knowledge/chunking/`: Chunking strategy implementations
- `/libs/agno/agno/knowledge/readers/`: Document reader implementations
- `/libs/agno/agno/knowledge/search_type/`: Search strategy implementations

## Usage Examples

### Basic Text Knowledge Base

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge import TextKnowledgeBase
from agno.knowledge.vector_dbs import ChromaDb

# Create a knowledge base with text content
knowledge_base = TextKnowledgeBase(
    content="Einstein developed the theory of relativity in 1905...",
    vector_db=ChromaDb(collection="physics"),
)

# Load the knowledge into the vector database
knowledge_base.load()

# Create an agent that uses this knowledge
agent = Agent(
    model=OpenAIChat(),
    instructions="You are a physics tutor.",
    knowledge=knowledge_base,
    search_knowledge=True,
    add_references=True,
)

# The agent will now use the knowledge base to answer questions
response = agent.run("When did Einstein develop relativity?")
```

### PDF Knowledge Base

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge import PDFKnowledgeBase
from agno.knowledge.vector_dbs import PgVector
from agno.knowledge.chunking import DocumentChunking

# Create a knowledge base with PDF files
knowledge_base = PDFKnowledgeBase(
    files=["document1.pdf", "document2.pdf"],
    vector_db=PgVector(table_name="pdf_docs", db_url="postgresql://user:pass@localhost/db"),
    chunking_strategy=DocumentChunking(chunk_size=500, chunk_overlap=50),
)

# Load the knowledge into the vector database
knowledge_base.load()

# Create an agent that uses this knowledge
agent = Agent(
    model=OpenAIChat(),
    instructions="Answer questions based on the PDF documents.",
    knowledge=knowledge_base,
)
```

### Website Knowledge Base

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.knowledge import WebsiteKnowledgeBase
from agno.knowledge.vector_dbs import LanceDb
from agno.knowledge.embedders import OpenAIEmbedder

# Create a knowledge base from websites
knowledge_base = WebsiteKnowledgeBase(
    urls=["https://example.com/page1", "https://example.com/page2"],
    vector_db=LanceDb(uri="db", table_name="website_content"),
    embedder=OpenAIEmbedder(),
    max_links=10,
    max_depth=2,
)

# Load the knowledge into the vector database
knowledge_base.load()

# Create an agent that uses this knowledge
agent = Agent(
    model=Claude(),
    instructions="Answer questions based on the website content.",
    knowledge=knowledge_base,
    num_knowledge_results=3,
)
```

### Combined Knowledge Base

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge import CombinedKnowledgeBase
from agno.knowledge import PDFKnowledgeBase, WikipediaKnowledgeBase
from agno.knowledge.vector_dbs import ChromaDb

# Create individual knowledge bases
pdf_kb = PDFKnowledgeBase(
    files=["doc1.pdf", "doc2.pdf"],
    vector_db=ChromaDb(collection="pdfs"),
)

wiki_kb = WikipediaKnowledgeBase(
    topics=["Artificial Intelligence", "Machine Learning"],
    vector_db=ChromaDb(collection="wiki"),
)

# Combine them into a unified knowledge base
combined_kb = CombinedKnowledgeBase(
    sources=[pdf_kb, wiki_kb],
    vector_db=ChromaDb(collection="combined"),
)

# Load all knowledge sources
combined_kb.load()

# Create an agent with the combined knowledge
agent = Agent(
    model=OpenAIChat(),
    instructions="You have access to PDF documents and Wikipedia articles.",
    knowledge=combined_kb,
)
```

## Summary

- **Flexible Architecture**: Modular design for combining different knowledge sources, vector stores, and embedders
- **Multiple Data Sources**: Support for PDFs, text, websites, APIs, and structured data
- **Vector Database Integration**: Works with 10+ vector databases
- **Embedding Options**: Compatible with all major embedding providers
- **Advanced Chunking**: Sophisticated strategies for document processing
- **Search Capabilities**: Vector, keyword, and hybrid search options
- **Seamless Agent Integration**: Simple interface for adding knowledge to agents