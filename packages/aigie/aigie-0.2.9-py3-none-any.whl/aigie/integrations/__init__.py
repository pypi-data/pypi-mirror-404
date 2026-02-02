"""
Aigie Framework Integrations

This module contains integrations for various AI agent frameworks.

Available integrations:
- langchain: Full workflow tracing for LangChain chains, agents, and tools
- langgraph: Full workflow tracing for LangGraph stateful graphs
- browser_use: Full workflow tracing for browser-use browser automation
- crewai: Multi-agent orchestration tracing for CrewAI
- autogen: Multi-agent conversation tracing for AutoGen/AG2
- llamaindex: RAG workflow tracing for LlamaIndex
- openai_agents: Agent workflow tracing for OpenAI Agents SDK
- dspy: Program tracing for DSPy modules, predictions, and optimizations
- claude_agent_sdk: Tracing for Anthropic Claude Agent SDK (query, sessions, tools)
- instructor: Tracing for Instructor structured output library
- semantic_kernel: Tracing for Microsoft Semantic Kernel
"""

__all__ = [
    "langchain",
    "langgraph",
    "browser_use",
    "crewai",
    "autogen",
    "llamaindex",
    "openai_agents",
    "dspy",
    "claude_agent_sdk",
    "instructor",
    "semantic_kernel",
]
