"""
LLM Provider package.

WHY: Groups all language model implementations together.
     The factory is the only public API — callers never
     instantiate providers directly.

     from app.providers.llm import get_llm_provider
"""
