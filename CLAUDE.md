# Claude Code Assistant Guidelines

This document provides guidelines for AI assistants (like Claude) when analyzing and generating code for this project.

## Project Structure

```
.
├── src/                      # Source code directory
│   ├── lib/                  # Reusable library modules
│   │   └── db/              # Database utilities
│   │       ├── __init__.py
│   │       └── postgres.py  # PostgreSQL connection utilities
│   └── main.py              # Main application entry point
├── tests/                    # Test scripts
│   └── test_db.py           # Database connection tests
├── .env.local               # Environment configuration (not in git)
├── pyproject.toml           # Python project configuration
├── uv.lock                  # Dependency lock file
├── Dockerfile               # Multi-stage Docker build
├── .dockerignore            # Docker build context exclusions
├── build.sh                 # Docker image build script
├── run.sh                   # Docker container run script
├── test.sh                  # Run tests in Docker container
└── README.md                # Project documentation
```

## Core Principles

### 1. Package Management
- **Use `uv`** for all dependency management
- Python version: **3.13** (configured in pyproject.toml)
- Add dependencies to `pyproject.toml` dependencies list
- Run `uv sync` after adding dependencies
- Lock file (`uv.lock`) ensures reproducible builds

### 2. Environment Configuration
- **All configuration via `.env.local`** file
- Use `python-dotenv` to load environment variables
- Never hardcode credentials or environment-specific values
- Follow the pattern: `{SERVICE_PREFIX}_VARIABLE_NAME`

### 3. Database Utilities
- **Location**: `src/lib/db/postgres.py`
- **Pattern**: Global connection management with helper functions
- **Functions**:
  - `open_connection()`: Returns True/False (does not exit on failure)
  - `close_connection()`: Clean connection closure
  - `insert_record()`: Single record insertion
  - `insert_multiple_records()`: Bulk insertion with conflict handling
  - `execute_query()`: Generic query execution with select/update flags
- **Environment variables**:
  ```
  DB_SERVICE_PREFIX=MY_SERVICE
  MY_SERVICE_PG_DB_NAME=dbname
  MY_SERVICE_PG_DB_USER=user
  MY_SERVICE_PG_DB_PASSWORD=password
  MY_SERVICE_PG_DB_HOST=host
  MY_SERVICE_PG_DB_PORT=port
  ```

### 4. Docker Configuration
- **Multi-stage build** for optimal image size
- **Base image**: `python:{VERSION}-alpine3.22`
- **Builder stage**:
  - Install `uv` from official image
  - Cache dependencies separately from source code
  - Use cache mounts for faster rebuilds
- **Final stage**:
  - Minimal runtime image
  - Non-root user (`appuser`)
  - Only necessary files copied
- **Environment variables**:
  - `UV_COMPILE_BYTECODE=1`: Faster startup
  - `UV_LINK_MODE=copy`: Resolve symlink issues
  - `UV_PYTHON_DOWNLOADS=never`: Use system Python

### 5. Code Organization
- **`src/lib/`**: Reusable library modules (imported as `from lib.module import ...`)
- **`src/`**: Application-specific code
- **`tests/`**: Test scripts (not copied to Docker image, mounted as volume)
- **Avoid circular dependencies**: Library modules should be self-contained

### 6. Testing Strategy
- Tests live in `tests/` directory
- Tests are **mounted as volumes** when running in Docker (not baked into image)
- Set `PYTHONPATH=/app/src` to allow imports from `lib` modules
- Tests should handle connection failures gracefully
- Use `test.sh` to run tests in Docker environment

### 7. Error Handling
- **Return values over exceptions** for expected failures (e.g., connection errors)
- Library functions should return `False` or `-1` on failure, not `sys.exit()`
- Print informative error messages
- Tests should complete and show summary even on failures

### 8. Scripting Conventions
- **Shell scripts** use `#!/bin/sh` (POSIX-compatible)
- Read `DOCKER_IMAGE_TAG` from `.env.local`
- Use `eval` to expand environment variables in tag
- Make scripts executable: `chmod +x script.sh`

## Common Tasks

### Adding a New Dependency
```bash
# Add to pyproject.toml dependencies list
uv add package-name
# or manually edit pyproject.toml and run:
uv sync
```

### Running Tests Locally
```bash
python tests/test_db.py
```

### Running Tests in Docker
```bash
./build.sh  # Build image
./test.sh   # Run tests in container
```

### Adding New Database Utility Functions
- Add to `src/lib/db/postgres.py`
- Export in `src/lib/db/__init__.py`
- Follow existing patterns (global `_connection`, error handling)
- Document with docstrings

### Debugging Docker Build Issues
- Check `.dockerignore` if files aren't being copied
- Verify `pyproject.toml` has `[tool.hatch.build.targets.wheel]` configured
- Use `--no-cache` to force clean build: `docker build --no-cache .`

## Anti-Patterns to Avoid

❌ Don't use `sys.exit()` in library functions
❌ Don't hardcode environment-specific values
❌ Don't copy unnecessary files to Docker image
❌ Don't install dependencies globally (use virtual environment)
❌ Don't use `requirements.txt` (use `pyproject.toml` + `uv.lock`)
❌ Don't modify working directory assumptions in tests
❌ Don't create circular imports between modules

## When Generating Code

1. **Check existing patterns** in `src/lib/db/postgres.py` before creating new utilities
2. **Use type hints** where appropriate for better IDE support
3. **Add docstrings** to all functions explaining parameters and return values
4. **Follow the existing error handling pattern** (return False/None, print errors)
5. **Consider Docker implications** (paths, environment variables, permissions)
6. **Test both locally and in Docker** to ensure consistency

## Configuration Reference

### pyproject.toml
- Python version: `>=3.13`
- Build backend: `hatchling`
- Packages: `["src"]` (includes all of src/ including lib/)

### .env.local
- Docker image configuration
- Database credentials
- Application-specific environment variables

### Dockerfile
- Multi-stage: builder + final
- Working directory: `/app/src` (but tests run from `/app`)
- User: `appuser` (non-root)
- Entrypoint: `python` (flexible for different scripts)
