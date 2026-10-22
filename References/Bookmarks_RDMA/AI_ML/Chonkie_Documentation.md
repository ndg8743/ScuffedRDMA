# Chonkie Documentation

- **Source:** https://docs.chonkie.ai/common/open-source#tokenchunker
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

*✨Look Inside! We’re Open Source!✨*

**Chonkie’s Open Source library**provides lightweight, and high-performance features for building modern RAG applications. Install it locally, run anywhere, and keep full control over your chunking pipeline.

## Why Chonkie OSS?

## Completely Free

Released under the MIT license. Use however you like.

## Privacy First

All processing happens locally. Your data never leaves your infrastructure.

## Production Ready

Battle-tested algorithms used by thousands of developers. Optimized for
speed and reliability.

## Lightning Fast

Optimized with caching, parallel processing, and fast tokenizers. Process
millions of chunks efficiently.

## Core Capabilities

### Advanced Chunkers

Chonkie OSS includes a comprehensive suite of chunking algorithms, each designed for specific document types and use cases:
## TokenChunker


**Best for**: General-purpose chunking, most use casesSplits text into fixed-size token chunks with configurable overlap. The most straightforward and reliable chunking strategy.Available in: Python, JavaScript

## SentenceChunker


**Best for**: Q&A systems, maintaining complete thoughtsChunks at sentence boundaries while respecting token limits. Ensures sentences are never split mid-thought.Available in: Python, JavaScript

## RecursiveChunker


**Best for**: Markdown, structured documents, hierarchical contentHierarchically chunks using multiple delimiters—paragraphs, then sentences, then words. Preserves document structure naturally.Available in: Python, JavaScript

## FastChunker


**Best for**: High-throughput pipelines, large-scale document processingSIMD-accelerated chunking with 100+ GB/s throughput. Uses byte-size limits for extreme performance without tokenization overhead.Available in: Python, JavaScript

## TableChunker


**Best for**: Markdown tables, tabular dataSplits large tables into manageable chunks by rows while preserving headers. Perfect for data-heavy documents.Available in: Python, JavaScript

## SemanticChunker


**Best for**: Multi-topic documents, maintaining topical coherenceUses embeddings to identify natural topic boundaries. Creates chunks based on semantic similarity, not just structure. Includes Savitzky-Golay filtering and skip-window merging for advanced boundary detection.Available in: Python, JavaScript

## LateChunker


**Best for**: Retrieval optimization, higher recall RAG systemsImplements the Late Chunking algorithm from research. Generates document-level embeddings first, then derives chunk embeddings for richer contextual representation.Available in: Python

## CodeChunker


**Best for**: Source code, API documentation, technical contentLanguage-aware chunking using Abstract Syntax Trees (AST). Preserves function and class boundaries for better code understanding.Available in: Python, JavaScript

## NeuralChunker


**Best for**: Maximum quality, complex documents with subtle topic shiftsUses a fine-tuned BERT model to detect semantic shifts in text. ML-powered boundary detection for topic-coherent chunks.Available in: Python

## SlumberChunker


**Best for**: Books, research papers, when quality matters mostAgentic chunking powered by LLMs via the Genie interface. Uses generative models (Gemini, OpenAI, etc.) to intelligently determine optimal chunk boundaries.Available in: Python

### Embedding Providers

Flexible embedding support for semantic chunking and refineries:
- **AutoEmbeddings** - Automatically select the best embeddings for your use case
- **Model2VecEmbeddings** - Ultra-fast static embeddings (default for semantic chunking)
- **SentenceTransformerEmbeddings** - Hugging Face Sentence Transformers models
- **OpenAIEmbeddings** - OpenAI’s text-embedding models
- **AzureOpenAIEmbeddings** - Azure-hosted OpenAI embeddings
- **CohereEmbeddings** - Cohere’s embedding models
- **JinaEmbeddings** - Jina AI embeddings
- **GeminiEmbeddings** - Google Gemini embeddings
- **VoyageAIEmbeddings** - Voyage AI embeddings
- **Custom Embeddings** - Bring your own embedding model

All embeddings follow a consistent interface and can be swapped seamlessly.

### Refineries

Enhance your chunks with additional context and embeddings:
## OverlapRefinery

Adds contextual overlap between chunks to prevent information loss at boundaries. Configurable overlap sizes for optimal retrieval.

## EmbeddingsRefinery

Generates and attaches vector embeddings to your chunks. Supports all major embedding providers with automatic dimension detection.

### Database Handshakes

Seamlessly connect Chonkie to your favorite database:
## ChromaDB

Ephemeral or persistent ChromaDB instances

## Qdrant

High-performance vector search with Qdrant

## Weaviate

Knowledge graph + vector search with Weaviate

## Turbopuffer

Serverless vector database by Turbopuffer

## Pinecone

Managed vector database with Pinecone

## pgvector

PostgreSQL with pgvector extension

## MongoDB

MongoDB Atlas Vector Search

## Elastic

Elasticsearch vector search

### Chefs

Chefs automatically prepare raw data for chunking:
- **TableChef** - Extracts tables from markdown text
- **TextChef** - Processes plain text files into structured Documents
- **MarkdownChef** - Parses markdown with tables, code blocks, and images

### Porters

Export chunks to common formats:
- **JSONPorter** - Export chunks to JSON for storage or processing
- **DatasetsPorter** - Export to Hugging Face Datasets format

### Utils

- **Visualizer** - Rich text visualization of chunks with color-coded boundaries
- **Hubbie** - Hugging Face Hub integration for sharing and loading chunkers

## Language Support

- Python
- JavaScript/TypeScript

**Full Feature Set**All chunkers, embedding providers, refineries, handshakes, chefs, and porters available. Choose from minimal to full installations based on your needs.

- Default install: Token, Sentence, Recursive, Table chunkers
- Semantic install: + SemanticChunker, LateChunker, NeuralChunker with Model2Vec
- All install: Every feature available

## Performance Characteristics

Chonkie OSS is optimized for speed:
- **Pipelining** - Efficient multi-stage processing
- **Caching** - Smart caching to avoid recomputation
- **Fast Tokenizers** - TikToken and AutoTikTokenizer for speed
- **Parallel Processing** - Multi-threaded batch operations
- **Ultra-fast Embeddings** - Model2Vec static embeddings (default)
- **Token Estimate-Validate** - Efficient feedback loops for optimal chunk sizes

Process thousands of documents per second on commodity hardware.

## Next Steps

Ready to get started with Chonkie OSS?
## Quick Start

Install and create your first chunk in under 2 minutes

## Installation Guide

Detailed installation options for all features

## Chunkers Overview

Explore all chunking algorithms in detail

## GitHub Repository

Star the repo and contribute to the project

Need hosted chunking with zero setup? Check out our [Chunking API](/oss/api/overview) for a managed solution.