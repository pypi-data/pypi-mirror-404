"""
Tork Governance Framework Adapters

Provides integrations for popular Python frameworks:
- LangChain
- CrewAI
- AutoGen
- OpenAI Agents SDK
- FastAPI
- Django
- Flask
- MCP (Model Context Protocol)
- LlamaIndex
- Semantic Kernel
- Haystack
- Pydantic AI
- DSPy (Stanford)
- Instructor
- Guidance (Microsoft)
- LMQL
- Outlines
- Marvin
- SuperAGI
- MetaGPT
- BabyAGI
- AgentGPT
- Flowise
- Langflow
- Starlette
- Guardrails AI
- Dify
- LiteLLM
- NeMo Guardrails
- Ollama
- vLLM
- ChromaDB
- Pinecone
- Weaviate
- Qdrant
- Milvus
- LangSmith
- Helicone
- Weights & Biases (W&B)
- Arize
- Langfuse
"""

from .langchain import TorkCallbackHandler, TorkGovernedChain, create_governed_chain
from .guardrails_ai import TorkValidator, TorkGuard, TorkRail, with_tork_governance as guardrails_with_tork
from .dify import TorkDifyNode, TorkDifyHook, TorkDifyApp, dify_governed
from .litellm import TorkLiteLLMCallback, TorkLiteLLMProxy, govern_completion, agovern_completion, litellm_governed
from .nemo_guardrails import TorkNeMoAction, TorkRailsConfig, TorkNeMoMiddleware, govern_rails, register_tork_actions
from .ollama import TorkOllamaClient, AsyncTorkOllamaClient, govern_generate, govern_chat, ollama_governed
from .vllm import TorkVLLMEngine, AsyncTorkVLLMEngine, TorkSamplingParams, govern_generate as vllm_govern_generate, vllm_governed
from .chromadb import TorkChromaClient, TorkChromaCollection, govern_add, govern_query as chroma_govern_query, chromadb_governed
from .pinecone import TorkPineconeIndex, TorkPineconeClient, govern_upsert, govern_query as pinecone_govern_query, pinecone_governed
from .weaviate import TorkWeaviateClient, TorkWeaviateCollection, AsyncTorkWeaviateClient, govern_add as weaviate_govern_add, govern_query as weaviate_govern_query, govern_batch as weaviate_govern_batch, WeaviateGovernanceResult
from .qdrant import TorkQdrantClient, AsyncTorkQdrantClient, govern_upsert as qdrant_govern_upsert, govern_search as qdrant_govern_search, govern_scroll, govern_batch as qdrant_govern_batch, QdrantGovernanceResult
from .milvus import TorkMilvusClient, TorkMilvusCollection, AsyncTorkMilvusClient, govern_insert, govern_search as milvus_govern_search, govern_query as milvus_govern_query, MilvusGovernanceResult
from .langsmith import TorkLangSmithClient, TorkTracerCallback, govern_log_run, govern_feedback, create_governed_tracer, LangSmithGovernanceResult
from .helicone import TorkHeliconeClient, govern_log_request, govern_log_response, helicone_governed, HeliconeGovernanceResult
from .wandb import TorkWandbRun, TorkWandbCallback, govern_log, govern_table, wandb_governed, WandbGovernanceResult
from .arize import TorkArizeClient, govern_log_prediction, govern_log_embedding, arize_governed, ArizeGovernanceResult
from .langfuse import TorkLangfuseClient, TorkLangfuseCallback, govern_trace, govern_generation, govern_score, langfuse_governed, LangfuseGovernanceResult
from .crewai import TorkCrewAIMiddleware, GovernedAgent, GovernedCrew
from .autogen import TorkAutoGenMiddleware, GovernedAutoGenAgent
from .openai_agents import TorkOpenAIAgentsMiddleware, GovernedOpenAIAgent
from .fastapi import TorkFastAPIMiddleware, TorkFastAPIDependency
from .django import TorkDjangoMiddleware
from .flask import TorkFlask, tork_required
from .mcp import TorkMCPToolWrapper, TorkMCPServer, TorkMCPMiddleware
from .llamaindex import TorkLlamaIndexCallback, TorkQueryEngine, TorkRetriever
from .semantic_kernel import TorkSKFilter, TorkSKPlugin, TorkSKPromptFilter
from .haystack import TorkHaystackComponent, TorkHaystackPipeline, TorkDocumentProcessor
from .pydantic_ai import TorkPydanticAIMiddleware, TorkPydanticAITool, TorkAgentDependency
from .dspy import TorkDSPyModule, TorkDSPySignature, governed_predict
from .instructor import TorkInstructorClient, TorkInstructorPatch, governed_response
from .guidance import TorkGuidanceProgram, TorkGuidanceGen, governed_block
from .lmql import TorkLMQLQuery, TorkLMQLRuntime, governed_query
from .outlines import TorkOutlinesGenerator, TorkOutlinesModel, governed_generate
from .marvin import TorkMarvinAI, governed_fn, governed_classifier
from .superagi import TorkSuperAGIAgent, TorkSuperAGITool, TorkSuperAGIWorkflow
from .metagpt import TorkMetaGPTRole, TorkMetaGPTTeam, TorkMetaGPTAction
from .babyagi import TorkBabyAGIAgent, TorkBabyAGITaskManager, governed_task
from .agentgpt import TorkAgentGPTAgent, TorkAgentGPTTask, TorkAgentGPTGoal
from .flowise import TorkFlowiseNode, TorkFlowiseFlow, TorkFlowiseAPI
from .langflow import TorkLangflowComponent, TorkLangflowFlow, TorkLangflowAPI
from .starlette import TorkStarletteMiddleware, TorkStarletteRoute, tork_route

__all__ = [
    # LangChain
    "TorkCallbackHandler",
    "TorkGovernedChain",
    "create_governed_chain",
    # CrewAI
    "TorkCrewAIMiddleware",
    "GovernedAgent",
    "GovernedCrew",
    # AutoGen
    "TorkAutoGenMiddleware",
    "GovernedAutoGenAgent",
    # OpenAI Agents
    "TorkOpenAIAgentsMiddleware",
    "GovernedOpenAIAgent",
    # FastAPI
    "TorkFastAPIMiddleware",
    "TorkFastAPIDependency",
    # Django
    "TorkDjangoMiddleware",
    # Flask
    "TorkFlask",
    "tork_required",
    # MCP (Model Context Protocol)
    "TorkMCPToolWrapper",
    "TorkMCPServer",
    "TorkMCPMiddleware",
    # LlamaIndex
    "TorkLlamaIndexCallback",
    "TorkQueryEngine",
    "TorkRetriever",
    # Semantic Kernel
    "TorkSKFilter",
    "TorkSKPlugin",
    "TorkSKPromptFilter",
    # Haystack
    "TorkHaystackComponent",
    "TorkHaystackPipeline",
    "TorkDocumentProcessor",
    # Pydantic AI
    "TorkPydanticAIMiddleware",
    "TorkPydanticAITool",
    "TorkAgentDependency",
    # DSPy
    "TorkDSPyModule",
    "TorkDSPySignature",
    "governed_predict",
    # Instructor
    "TorkInstructorClient",
    "TorkInstructorPatch",
    "governed_response",
    # Guidance
    "TorkGuidanceProgram",
    "TorkGuidanceGen",
    "governed_block",
    # LMQL
    "TorkLMQLQuery",
    "TorkLMQLRuntime",
    "governed_query",
    # Outlines
    "TorkOutlinesGenerator",
    "TorkOutlinesModel",
    "governed_generate",
    # Marvin
    "TorkMarvinAI",
    "governed_fn",
    "governed_classifier",
    # SuperAGI
    "TorkSuperAGIAgent",
    "TorkSuperAGITool",
    "TorkSuperAGIWorkflow",
    # MetaGPT
    "TorkMetaGPTRole",
    "TorkMetaGPTTeam",
    "TorkMetaGPTAction",
    # BabyAGI
    "TorkBabyAGIAgent",
    "TorkBabyAGITaskManager",
    "governed_task",
    # AgentGPT
    "TorkAgentGPTAgent",
    "TorkAgentGPTTask",
    "TorkAgentGPTGoal",
    # Flowise
    "TorkFlowiseNode",
    "TorkFlowiseFlow",
    "TorkFlowiseAPI",
    # Langflow
    "TorkLangflowComponent",
    "TorkLangflowFlow",
    "TorkLangflowAPI",
    # Starlette
    "TorkStarletteMiddleware",
    "TorkStarletteRoute",
    "tork_route",
    # Guardrails AI
    "TorkValidator",
    "TorkGuard",
    "TorkRail",
    "guardrails_with_tork",
    # Dify
    "TorkDifyNode",
    "TorkDifyHook",
    "TorkDifyApp",
    "dify_governed",
    # LiteLLM
    "TorkLiteLLMCallback",
    "TorkLiteLLMProxy",
    "govern_completion",
    "agovern_completion",
    "litellm_governed",
    # NeMo Guardrails
    "TorkNeMoAction",
    "TorkRailsConfig",
    "TorkNeMoMiddleware",
    "govern_rails",
    "register_tork_actions",
    # Ollama
    "TorkOllamaClient",
    "AsyncTorkOllamaClient",
    "govern_generate",
    "govern_chat",
    "ollama_governed",
    # vLLM
    "TorkVLLMEngine",
    "AsyncTorkVLLMEngine",
    "TorkSamplingParams",
    "vllm_govern_generate",
    "vllm_governed",
    # ChromaDB
    "TorkChromaClient",
    "TorkChromaCollection",
    "govern_add",
    "chroma_govern_query",
    "chromadb_governed",
    # Pinecone
    "TorkPineconeIndex",
    "TorkPineconeClient",
    "govern_upsert",
    "pinecone_govern_query",
    "pinecone_governed",
    # Weaviate
    "TorkWeaviateClient",
    "TorkWeaviateCollection",
    "AsyncTorkWeaviateClient",
    "weaviate_govern_add",
    "weaviate_govern_query",
    "weaviate_govern_batch",
    "WeaviateGovernanceResult",
    # Qdrant
    "TorkQdrantClient",
    "AsyncTorkQdrantClient",
    "qdrant_govern_upsert",
    "qdrant_govern_search",
    "govern_scroll",
    "qdrant_govern_batch",
    "QdrantGovernanceResult",
    # Milvus
    "TorkMilvusClient",
    "TorkMilvusCollection",
    "AsyncTorkMilvusClient",
    "govern_insert",
    "milvus_govern_search",
    "milvus_govern_query",
    "MilvusGovernanceResult",
    # LangSmith
    "TorkLangSmithClient",
    "TorkTracerCallback",
    "govern_log_run",
    "govern_feedback",
    "create_governed_tracer",
    "LangSmithGovernanceResult",
    # Helicone
    "TorkHeliconeClient",
    "govern_log_request",
    "govern_log_response",
    "helicone_governed",
    "HeliconeGovernanceResult",
    # Weights & Biases
    "TorkWandbRun",
    "TorkWandbCallback",
    "govern_log",
    "govern_table",
    "wandb_governed",
    "WandbGovernanceResult",
    # Arize
    "TorkArizeClient",
    "govern_log_prediction",
    "govern_log_embedding",
    "arize_governed",
    "ArizeGovernanceResult",
    # Langfuse
    "TorkLangfuseClient",
    "TorkLangfuseCallback",
    "govern_trace",
    "govern_generation",
    "govern_score",
    "langfuse_governed",
    "LangfuseGovernanceResult",
]
