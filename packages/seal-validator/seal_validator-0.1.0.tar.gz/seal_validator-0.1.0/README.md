# Seal Validator

[![PyPI version](https://badge.fury.io/py/seal-validator.svg)](https://badge.fury.io/py/seal-validator)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Seal Validator** is a lightweight Python library for structured output validation in LLM applications. It ensures your LLM outputs conform to defined schemas with automatic correction and retry mechanisms.

## 🌟 Features

- **🔒 Schema Validation**: Pydantic-based schema definitions with comprehensive validation
- **🔄 Auto-Correction**: Multiple correction strategies (fix prompts, type conversion, default values)
- **🤖 LLM Integration**: Built-in adapters for popular LLM providers (DeepSeek, OpenAI-compatible)
- **📊 Type Safety**: Full type hints and generic support
- **⚡ Lightweight**: Minimal dependencies, focused on core functionality
- **📝 Audit Trail**: Complete execution logging for debugging and monitoring

## 📦 Installation

```bash
pip install seal-validator
```

## 🚀 Quick Start

### 1. Define Your Schema

```python
from seal import SealModel, Field
from typing import List, Optional

class UserProfile(SealModel):
    """User profile schema with validation constraints."""
    
    name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=0, le=150)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    interests: List[str] = Field(default_factory=list)
```

### 2. Validate Data

```python
from seal import Validator

validator = Validator(UserProfile)

# Valid data
result = validator.validate({
    'name': 'Alice Johnson',
    'age': 28,
    'email': 'alice@example.com',
    'interests': ['reading', 'hiking']
})
print(result.is_valid)  # True

# Invalid data
result = validator.validate({
    'name': '',  # Empty name
    'age': 200,  # Age too high
    'email': 'invalid-email'
})
print(result.is_valid)  # False
print(result.errors)    # List of validation errors
```

### 3. Generate LLM Format Instructions

```python
from seal import build_format_instructions

instructions = build_format_instructions(UserProfile)
print(instructions)
```

Output:
```json
{
  "name": "string (required, min_length: 1, max_length: 50)",
  "age": "integer (required, ge: 0, le: 150)",
  "email": "string or null (optional, pattern: regex)",
  "interests": "array of string (default: [])"
}
```

### 4. Full Automation with SealEngine

```python
from seal import SealEngine, DeepSeekAIAdapter, DeepSeekConfig
from seal import JsonParser, Validator, FixPromptStrategy

# Configure LLM adapter
config = DeepSeekConfig(api_key="your-api-key", model="deepseek-chat")
llm_adapter = DeepSeekAIAdapter(config)

# Setup engine components
parser = JsonParser()
validator = Validator(UserProfile)
corrector = FixPromptStrategy(max_retries=3)

# Create engine
engine = SealEngine[UserProfile](
    model=UserProfile,
    llm_adapter=llm_adapter,
    parser=parser,
    validator=validator,
    correctors=[corrector]
)

# Generate structured output
result = engine.run_sync("Create a user profile for a software developer named Alex, age 30")

if result.success:
    user = result.data
    print(f"Name: {user.name}, Age: {user.age}")
else:
    print(f"Failed: {result.errors}")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SealEngine                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Prompt  │→ │   LLM    │→ │  Parser  │→ │ Validator│   │
│  │ Builder  │  │ Adapter  │  │ (JSON)   │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘   │
│                                                  │         │
│                           ┌──────────────────────┘         │
│                           ↓                                │
│                    ┌──────────────┐                        │
│                    │  Corrector   │                        │
│                    │  (if invalid)│                        │
│                    └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## 📚 Core Components

### Schema Definition
- `SealModel`: Pydantic-based model with extended features
- `Field`: Field definitions with constraints and examples
- `build_format_instructions()`: Generate LLM-friendly format instructions

### Validation
- `Validator`: Validate data against schemas
- `ValidationResult`: Structured validation results with error details

### Correction Strategies
- `FixPromptStrategy`: Generate correction prompts for LLM re-prompting
- `TypeConversionStrategy`: Automatic type coercion
- `DefaultValueStrategy`: Fill missing values with defaults

### LLM Adapters
- `DeepSeekAIAdapter`: DeepSeek AI integration
- `LLMAdapter`: Base class for custom adapters

### Engine
- `SealEngine`: Orchestrates the entire validation pipeline
- Supports sync and async operations
- Configurable retry logic

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=seal tests/

# Run specific module tests
python -m pytest tests/codes/validation/
```

## 📖 Examples

See the [demo/quick_start.py](seal/demo/quick_start.py) file for a comprehensive example.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Documentation](https://github.com/yourusername/seal/wiki)
- [Issue Tracker](https://github.com/yourusername/seal/issues)
- [Changelog](CHANGELOG.md)

## 💡 Why Seal?

LLMs are powerful but their outputs can be unpredictable. Seal bridges the gap between LLM creativity and application requirements by:

1. **Guaranteeing Structure**: Ensures outputs match your defined schemas
2. **Auto-Correcting**: Automatically fixes common errors without human intervention
3. **Providing Visibility**: Complete audit trails for debugging
4. **Being Lightweight**: No heavy dependencies, easy to integrate

---

**Made with ❤️ for the LLM community**
