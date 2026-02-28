# Root Multi-Model Interface

A local and modular Python chat interface for llama.cpp models with clean separation of concerns.

## Project Structure

```
chat_interface/
├── main.py                         # Application entry point
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── models_config.json              # Model configurations
│
├── managers/                         # Model management
│   ├── __init__.py
│   ├── model_manager.py            # Model loading/inference
│   └── context_manager.py          # Context window management
│
├── conversation/                   # Conversation management
│   ├── __init__.py
│   ├── message_handler.py          # Message history
│   └── storage.py                  # Save/load conversations
│
├── ui/                             # User interface
│   ├── __init__.py
│   ├── main_window.py              # Main window orchestration
│   ├── chat_display.py             # Chat display widget
│   └── parameter_controls.py       # Parameter sliders/controls
│
└── utils/                          # Utilities
    ├── __init__.py
    ├── logger.py                   # Logging configuration
    └── file_importer.py            # File import functionality
```

## Architecture Overview

### Separation of Concerns

Each module has a **single responsibility**:

| Module | Responsibility |
|--------|----------------|
| `config.py` | Load/save model configurations |
| `managers/model_manager.py` | Load models, generate responses |
| `managers/context_manager.py` | Manage context window, chunking |
| `conversation/message_handler.py` | Track conversation history |
| `conversation/storage.py` | Save/load conversations |
| `ui/main_window.py` | Orchestrate UI and components |
| `ui/chat_display.py` | Display chat messages |
| `ui/parameter_controls.py` | Control generation parameters |
| `utils/logger.py` | Configure logging |
| `utils/file_importer.py` | Import various file types |

### Dependency Flow

```
main.py
  ├─> config.py
  ├─> managers/
  │   ├─> model_manager.py
  │   └─> context_manager.py (uses model_manager)
  ├─> conversation/
  │   ├─> message_handler.py
  │   └─> storage.py
  └─> ui/
      ├─> main_window.py (uses all above)
      ├─> chat_display.py
      └─> parameter_controls.py
```

## Getting Started

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create models_config.json (or it will be auto-created)
cp models_config.example.json models_config.json

# Edit model paths
nano models_config.json
```

### Running

```bash
python main.py
```

## Module Documentation

### Configuration (`config.py`)

Manages model configurations from JSON file.

```python
from config import Config

config = Config()
models = config.get_model_names()
model_config = config.get_model_config("o3")
```

**Methods:**
- `load()` - Load config from JSON
- `save()` - Save config to JSON
- `get_model_config(name)` - Get config for specific model
- `get_model_names()` - List all model names
- `add_model(name, config)` - Add new model
- `update_model(name, config)` - Update existing model

### Model Manager (`models/model_manager.py`)

Handles model loading and inference.

```python
from managers import ModelManager

manager = ModelManager(config)
manager.load_model("o3", on_complete=callback)

for text in manager.generate(messages, temperature=0.7, stream=True):
    print(text, end='', flush=True)
```

**Methods:**
- `load_model(name, on_progress, on_complete)` - Load model asynchronously
- `generate(messages, **params)` - Generate response (yields chunks)
- `estimate_tokens(text)` - Estimate token count
- `is_loaded()` - Check if model loaded
- `get_context_size()` - Get model's context size

### Context Manager (`models/context_manager.py`)

Manages conversation context to fit within model limits.

```python
from managers import ContextManager

ctx_manager = ContextManager(model_manager, max_context_length=4096)
managed_messages = ctx_manager.manage_context(messages)
stats = ctx_manager.calculate_stats(messages)
```

**Methods:**
- `manage_context(messages)` - Chunk/summarize to fit context
- `calculate_stats(messages)` - Get token usage statistics
- `update_max_context(size)` - Update context limit

### Message Handler (`conversation/message_handler.py`)

Tracks conversation history and message navigation.

```python
from conversation import MessageHandler

handler = MessageHandler()
handler.add_user_message("Hello!")
handler.add_assistant_message("Hi there!")
history = handler.get_history()
```

**Methods:**
- `add_message(role, content)` - Add any message
- `add_user_message(content)` - Add user message
- `add_assistant_message(content)` - Add assistant message
- `set_system_prompt(prompt)` - Update system prompt
- `get_history()` - Get full conversation
- `clear_history(keep_system)` - Clear messages
- `get_previous_input()` - Navigate input history (up arrow)

### Storage (`conversation/storage.py`)

Save/load conversations and export to formats.

```python
from conversation import ConversationStorage

storage = ConversationStorage()
storage.save_to_json("chat.json", history, model_name, params)
success, data, msg = storage.load_from_json("chat.json")
storage.export_to_markdown("chat.md", history, model_name, params)
```

**Methods:**
- `save_to_json(path, history, model, params)` - Save conversation
- `load_from_json(path)` - Load conversation
- `export_to_markdown(path, history, model, params)` - Export to MD
- `get_default_filename(ext)` - Generate timestamped filename

### Main Window (`ui/main_window.py`)

Orchestrates the entire application UI.

```python
from ui import MainWindow

app = MainWindow(root, config, model_manager, context_manager, 
                 message_handler, storage)
app.run()
```

**Responsibilities:**
- Creates all UI components
- Coordinates between models, conversation, and UI
- Handles user events
- Manages threading for async operations

## Testing Individual Modules

Each module can be tested independently:

### Test Config

```python
from config import Config

config = Config("test_config.json")
assert "o3" in config.get_model_names()
print("Config works!")
```

### Test Model Manager

```python
from config import Config
from managers import ModelManager

config = Config()
manager = ModelManager(config)


def on_complete(success, message):
    print(f"Load result: {message}")


manager.load_model("o3", on_complete=on_complete)
```

### Test Message Handler

```python
from conversation import MessageHandler

handler = MessageHandler()
handler.add_user_message("Test message")
assert len(handler.get_history()) == 2  # system + user
print("Message handler works!")
```

## Extending the Application

### Adding a New Model

1. Edit `models_config.json`:
```json
{
  "My New Model": {
    "path": "./managers/my_model.gguf",
    "n_ctx": 8192,
    "n_gpu_layers": -1,
    "n_threads": 8
  }
}
```

2. Restart the application - it will appear in the dropdown

### Adding a New UI Component

1. Create `ui/my_widget.py`:
```python
import tkinter as tk
from utils.logger import get_logger

class MyWidget:
    def __init__(self, parent, bg_color):
        self.logger = get_logger("MyWidget")
        self.frame = tk.Frame(parent, bg=bg_color)
        # ... create widgets
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
```

2. Import in `ui/__init__.py`:
```python
from .my_widget import MyWidget
__all__ = [..., 'MyWidget']
```

3. Use in `ui/main_window.py`:
```python
from .my_widget import MyWidget

# In __init__:
self.my_widget = MyWidget(self.root, self.bg_color)
self.my_widget.pack(...)
```

### Adding New File Types

Edit `utils/file_importer.py`:

```python
# Add to supported_extensions
self.supported_extensions['new_type'] = ['.ext1', '.ext2']

# Add import method
def _import_new_type(self, file_path, file_name):
    # ... process file
    return True, content, message
```

## Benefits of Modular Architecture

### 1. Testability
```bash
# Test individual components
python -c "from config import Config; print(Config().get_model_names())"
python -c "from conversation import MessageHandler; h = MessageHandler(); print('OK')"
```

### 2. Reusability

```python
# Use ModelManager in another project
from managers import ModelManager
from config import Config

config = Config()
manager = ModelManager(config)
# ... use in CLI, web app, etc.
```

### 3. Maintainability
- Bug in model loading? → Fix `models/model_manager.py`
- Bug in chat display? → Fix `ui/chat_display.py`
- Each file is small (~100-300 lines)

### 4. Team Collaboration
- Person A: Work on UI (`ui/`)
- Person B: Work on models (`models/`)
- Person C: Work on storage (`conversation/`)
- No merge conflicts!

### 5. Easy to Understand
- New developer? Read `main.py` to see architecture
- Need to understand generation? Read `models/model_manager.py`
- Clear separation makes onboarding fast

## Comparison: Monolithic vs Modular

| Aspect | Monolithic (900 lines) | Modular (10 files) |
|--------|------------------------|-------------------|
| File size | 900 lines | 100-300 lines each |
| Testing | Hard (need full app) | Easy (test modules) |
| Reusability | None | High (import modules) |
| Debugging | Find bug in 900 lines | Find bug in ~200 lines |
| Team work | Merge conflicts | Parallel work |
| Understanding | Read entire file | Read relevant module |

## Code Quality Features

### Logging
Every module logs its operations:
```python
from utils.logger import get_logger

logger = get_logger("MyModule")
logger.info("Operation started")
logger.error("Something failed", exc_info=True)
```

Logs are saved to `logs/chat_YYYYMMDD.log`

### Error Handling
All modules use try-except with logging:
```python
try:
    result = risky_operation()
except Exception as e:
    self.logger.error(f"Failed: {str(e)}", exc_info=True)
    return False, None, f"Error: {str(e)}"
```

### Type Hints (Optional Enhancement)
You can add type hints for better IDE support:
```python
def load_model(self, model_name: str, 
               on_progress: Callable[[str], None] = None,
               on_complete: Callable[[bool, str], None] = None) -> bool:
```

## Performance Considerations

### Threading
- Model loading: Background thread
- Response generation: Background thread
- UI updates: Main thread via `root.after()`

### Memory Management
- Context manager automatically chunks long conversations
- Models can be unloaded to free VRAM
- Conversation files are loaded on-demand

## Best Practices

1. **Always use `root.after()` for GUI updates from threads**
2. **Log important operations** (loading, errors, etc.)
3. **Return tuples for operations**: `(success: bool, data, message: str)`
4. **Keep modules focused** - one responsibility per module
5. **Use dependency injection** - pass dependencies to `__init__`

## When to Use Each Version

**Use Monolithic** (`chat_interface_improved.py`):
- Quick prototyping
- Single developer
- Won't maintain long-term
- Simple customization

**Use Modular** (this version):
- Professional project
- Team development
- Long-term maintenance
- Need to reuse components
- Planning to add many features

## Further Reading

- [Clean Code by Robert Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Python Project Structure](https://docs.python-guide.org/writing/structure/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

## Contributing

To add features:
1. Identify the appropriate module
2. Add your functionality
3. Update `__init__.py` if adding new classes
4. Test the module independently
5. Test integration with the full app

## License

Use freely for personal or commercial projects.
