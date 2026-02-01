"""Serve Tantra runnables as HTTP APIs.

Provides a FastAPI-based server with session management, chat, and
streaming. Requires the ``[serve]`` extra::

    pip install tantra[serve]

Quick start::

    from tantra import Agent
    from tantra.serve import serve

    agent = Agent("openai:gpt-4o", system_prompt="You are helpful.")
    app = serve(agent)

    if __name__ == "__main__":
        serve(agent, run=True)
"""

from .app import RunnableServer, serve
from .factory import PostgresRunnableFactory, RunnableFactory

__all__ = ["RunnableServer", "serve", "RunnableFactory", "PostgresRunnableFactory"]
