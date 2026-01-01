#!/usr/bin/env fish
# DSPy Backend Setup Script
# Quick setup for DSPy Prompt Improver backend

echo "🚀 Setting up DSPy Prompt Improver Backend..."

# Check if Python is installed
if not command -v python3 >/dev/null
    echo "❌ Python 3 is required. Please install Python 3.8+"
    exit 1
fi

# Check if uv is installed
if not command -v uv >/dev/null
    echo "❌ uv is required. Install it with: brew install uv"
    exit 1
fi

# Install dependencies
echo "📚 Installing dependencies..."
uv sync --all-extras

# Create environment file
if not test -f .env
    echo "📝 Creating environment configuration..."
    cp .env.example .env
    echo "✅ Created .env file - please review and update as needed"
fi

# Check if Ollama is installed and running
if command -v ollama >/dev/null
    echo "🦙 Ollama found"
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1
        echo "✅ Ollama is running"
    else
        echo "⚠️ Ollama installed but not running. Start with: ollama serve"
    fi
else
    echo "⚠️ Ollama not found. Install with: curl -fsSL https://ollama.ai/install.sh | sh"
fi

# Test imports
echo "🧪 Testing DSPy imports..."
uv run python -c "
try:
    import dspy
    import fastapi
    import uvicorn
    import pydantic_settings
    import litellm
    print('✅ All dependencies imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if test $status -eq 0
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Review .env file and update as needed"
    echo "2. Start Ollama: ollama serve"
    echo "3. Pull model: ollama pull llama3.1"
    echo "4. Start backend: python main.py"
    echo "5. Test with: curl http://localhost:8000/health"
    echo ""
    echo "📚 Full documentation: DSPY_BACKEND_README.md"
else
    echo "❌ Setup failed. Please check error messages above."
    exit 1
fi
