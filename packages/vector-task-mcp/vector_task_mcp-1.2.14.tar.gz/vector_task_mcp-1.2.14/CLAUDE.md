# Vector Task MCP Server

## Project Overview
MCP (Model Context Protocol) Server для управління задачами з використанням sqlite-vec для семантичного пошуку.

## Technology Stack
- **Python**: 3.11.8 (requires >= 3.10)
- **Package Manager**: `uv` (сучасний Python package manager)
- **Database**: SQLite 3.43.2 + sqlite-vec extension
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384-dimensional vectors)
- **MCP Framework**: FastMCP >= 0.3.0

## Key Dependencies
- `mcp>=0.3.0` - Model Context Protocol framework
- `sqlite-vec>=0.1.6` - Vector search extension для SQLite
- `sentence-transformers>=2.2.2` - Embedding models

## Project Structure
- `main.py` - Entry point with uv script configuration
- `requirements.txt` - Python dependencies for pip/venv compatibility
- `pyproject.toml` - Modern Python project configuration
- `.python-version` - Python version specification (3.11)
- `claude-desktop-config.example.json` - Claude Desktop configuration template
- `src/models.py` - Data models and configuration
- `src/security.py` - Security validation and sanitization
- `src/task_store.py` - Vector task storage operations
- `tasks.db` - SQLite database for tasks

## How to Run

### Standalone
```bash
# Using uv (requires Python with SQLite extensions support)
uv run main.py --working-dir ./

# Alternative with conda Python (has SQLite extensions support)
~/miniconda3/envs/vector-mcp/bin/python main.py --working-dir ./
```

### Configuration Options

- `--working-dir` - Working directory for task database (required, default: current directory)
  - Specifies the project directory where the `memory/` subdirectory will be created
  - Database will be stored at `{working-dir}/memory/tasks.db`
  - Example: `--working-dir /path/to/project` → database at `/path/to/project/memory/tasks.db`

**⚠️ IMPORTANT for macOS Users:**
- Standard Python from python.org does NOT support SQLite loadable extensions
- Use conda/miniforge Python or compile Python with `--enable-loadable-sqlite-extensions`
- On Apple Silicon, ensure you're running native arm64 Python, not x86_64 through Rosetta

### Claude Desktop Integration
Використовуй `claude-desktop-config.example.json` як шаблон.

Конфігурація для Claude Desktop:
```json
{
  "mcpServers": {
    "vector-task": {
      "command": "uv",
      "args": [
        "run",
        "/absolute/path/to/main.py",
        "--working-dir",
        "/your/project/path"
      ]
    }
  }
}
```

**ВАЖЛИВО:**
- Використовуй абсолютні шляхи, не відносні!

## Database Architecture
- `task_metadata` - Метадані задач (title, content, status, priority, tags, timestamps)
- `task_vectors` - Векторна таблиця (vec0 virtual table)
- Індекси на status, priority, created_at, content_hash

## Task Management Features
- **Task Lifecycle**: draft → pending → in_progress → completed → tested → validated (or stopped/canceled at any point)
- **Statuses**: draft, pending, in_progress, completed, tested, validated, stopped, canceled
  - **draft**: Task draft (not ready for execution)
  - **pending**: Task ready but not started
  - **in_progress**: Currently being worked on
  - **completed**: Basic completion
  - **tested**: Completed and tested
  - **validated**: Completed, tested, and validated
  - **stopped**: Paused/blocked
  - **canceled**: Task canceled (will not be done)
- **Priorities**: low, medium, high, critical
- **Hierarchical Tasks**: Parent-child task relationships
- **Smart Search**: Semantic search using vector embeddings
- **Tags**: Organize tasks with custom tags
- **Comments**: Add notes to tasks without changing content

## Available MCP Tools
- `task_create` - Create new task
- `task_create_bulk` - Create multiple tasks
- `task_update` - Update task fields (status, priority, tags, comment with append, add_tag, remove_tag)
- `task_delete` / `task_delete_bulk` - Delete tasks
- `task_list` - List/search tasks with filters
- `task_get` - Get specific task by ID
- `task_next` - Get next task to work on
- `task_stats` - Get task statistics (includes unique_tags)

## Important Notes
- **sqlite-vec** працює як extension для SQLite, завантажується через `sqlite_vec.load(conn)`
- **uv** використовується замість venv - він керує ізольованим оточенням автоматично
- Векторний пошук використовує 384-вимірні embeddings
- База даних: `tasks.db` (location depends on `--working-dir`, see Configuration Options)

## Security Features
- Working directory validation
- Input sanitization
- Content hash для дедуплікації
- Resource limits для захисту від DoS
- Bulk operation limits (50 creates, 100 deletes max)

## Development Notes
- Проект налаштований як uv script з inline metadata (/// script ///)
- Не потрібно створювати venv вручну
- Всі залежності автоматично керуються через uv