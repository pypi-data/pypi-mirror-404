# NeuronOS Capabilities Library

A collection of provider-agnostic backend capabilities for Python applications, following hexagonal architecture principles. Each capability exposes well-defined ports and adapters for flexible backend infrastructure.

## Installation

```bash
pip install neuronos-capabilities
```

## Available Capabilities

### SQLManager - Database Management

A comprehensive SQL database management capability with:
- ✅ SQLAlchemy ORM support with type hints
- ✅ Alembic migrations (auto-generate, apply, rollback)
- ✅ Connection pooling with singleton pattern
- ✅ Async/await support
- ✅ PostgreSQL support (extensible to other databases)
- ✅ Transaction management
- ✅ Multi-schema support
- ✅ CRUD operations with filters

**Quick Example:**

```python
from neuronos_capabilities import SQLManager
from neuronos_capabilities.SQLManager import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

# Define your model
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)

# Configure database
config = {
    "host": "localhost",
    "database": "myapp",
    "user": "postgres",
    "password": "secret"
}

# Use with context manager
with SQLManager(config) as db:
    # Create tables
    db.create_tables([User])

    # Insert data
    user = db.insert(User, {"name": "Alice", "email": "alice@example.com"})

    # Query data
    users = db.query(User, {"name": "Alice"})
    print(f"Found user: {users[0].email}")
```

**Async Example:**

```python
async with SQLManager(config) as db:
    user = await db.insert_async(User, {"name": "Bob", "email": "bob@example.com"})
    users = await db.query_async(User, {"email": "bob@example.com"})
```

**Full Documentation**: [SQLManager/README.md](./neuronos_capabilities/SQLManager/README.md)

## Architecture

All capabilities follow **hexagonal architecture** (ports and adapters pattern):

```
Capability/
├── ports/              # Abstract interfaces (provider-agnostic contracts)
├── adapters/          # Provider-specific implementations
├── models/            # Data models and base classes
├── config/            # Configuration management
├── exceptions/        # Custom exception hierarchy
└── [capability]_manager.py  # Public API with singleton pattern
```

**Benefits:**
- 🔄 **Provider-agnostic**: Switch implementations without code changes
- ✅ **Testable**: Mock ports for unit testing
- 🔌 **Extensible**: Add new providers by implementing port interfaces
- 🧩 **Composable**: Combine capabilities in larger applications

## Development

### Local Installation

```bash
# Clone repository
git clone https://github.com/neuronos/neuronos_python_capabilities_library
cd neuronos_python_capabilities_library

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# All tests
pytest -v

# With coverage report
pytest --cov=neuronos_capabilities --cov-report=html

# Specific capability tests
pytest neuronos_capabilities/SQLManager/tests/ -v
```

### Building and Publishing

```bash
# Build distributions (wheel + source)
./build.sh

# Build and publish to PyPI (requires PyPI credentials)
./build.sh --deploy_pypi
```

## Roadmap

Future capabilities planned:
- **CacheManager**: Redis, Memcached, and in-memory caching
- **QueueManager**: RabbitMQ, AWS SQS, message queue abstraction
- **StorageManager**: S3, Azure Blob, file storage abstraction
- **AuthManager**: JWT, OAuth2, authentication/authorization

## Contributing

Contributions welcome! Please ensure:
1. Follow hexagonal architecture principles
2. Implement both sync and async methods
3. Include comprehensive tests
4. Add detailed documentation
5. Update CHANGELOG.md

## License

MIT License - see [LICENSE](./LICENSE) file for details.

## Links

- **Documentation**: https://docs.neuronos.dev/capabilities
- **Repository**: https://github.com/neuronos/neuronos_python_capabilities_library
- **Issues**: https://github.com/neuronos/neuronos_python_capabilities_library/issues
- **PyPI**: https://pypi.org/project/neuronos-capabilities/
