"""
NeuronOS Capabilities Library

A collection of provider-agnostic backend capabilities following hexagonal
architecture principles. Each capability exposes ports and adapters for
flexible backend infrastructure.

Available Capabilities:
    - SQLManager: Database management with ORM, migrations, and connection pooling

Example:
    from neuronos_capabilities import SQLManager

    config = {
        "host": "localhost",
        "database": "myapp",
        "user": "postgres",
        "password": "secret"
    }

    with SQLManager(config) as db:
        db.create_tables([User])
        user = db.insert(User, {"name": "Alice", "email": "alice@example.com"})
"""

from .__version__ import __version__
from .SQLManager import SQLManager

__all__ = ["SQLManager", "__version__"]
