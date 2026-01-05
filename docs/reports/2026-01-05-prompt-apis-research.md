# 🔍 Research: APIs y Datasets de Prompts Curados

**Fecha**: 2026-01-05
**Objetivo**: Encontrar APIs/datasets de prompts curados para generar prompts custom según preferencias de uso
**Estado**: Research completo ✅

---

## 📊 Resumen Ejecutivo

**Top 5 Opciones identificadas**:

| Opción | Tipo | API? | Dataset? | Coste | ROI |
|--------|------|------|----------|-------|-----|
| **LangChain Hub** | Platform | ✅ | ✅ | Free | 🔥🔥🔥 MÁXIMO |
| **PromptLayer** | SaaS | ✅ | ✅ | Paid | 🔥🔥 ALTO |
| **Langfuse** | Open Source | ✅ | ✅ | Free (self-hosted) | 🔥🔥 ALTO |
| **HuggingFace Datasets** | Dataset | ❌ | ✅ | Free | 🔥 MEDIO |
| **Awesome ChatGPT Prompts** | Repo | ❌ | ✅ | Free | 🔥 MEDIO |

---

## 🥇 Opción 1: LangChain Hub (RECOMENDADA)

**Fuente**: [smith.langchain.com/hub](https://smith.langchain.com/hub)

### ✅ Por qué es la mejor opción

- **Completamente gratuita** con API key de LangSmith
- **Prompts curados** por la comunidad
- **Version control integrado**
- **Acceso programático** vía Python SDK
- **GitHub sync** para backups
- **Integración nativa** con DSPy (ya usas LangChain)

### 🔧 Cómo integrarla

```python
# 1. Instalar SDK
pip install langchain

# 2. Crear API key en LangSmith
# https://smith.langchain.com/settings > API Keys > Create

# 3. Configurar en .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_xxx...

# 4. Usar en tu código
from langchain import hub

# Pull prompt del hub
prompt = hub.pull("hwchase17/react")  # Ejemplo

# O usar prompts custom para tu caso
prompt = hub.pull("felipegonzalez/prompt-improver")
```

### 📁 Prompts relevantes en LangChain Hub

```
hwchase17/react              # ReAct agent prompts
hwchase17/openai-functions  # Function calling
hwchase17/openai-tools-json # JSON structured outputs
```

### 🎯 Cómo usarla para tu DSPy backend

```python
# hemlov/adapters/langchain_hub_adapter.py
from langchain import hub
import dspy

class LangChainHubAdapter:
    """Adapter para usar LangChain Hub como fuente de prompts."""

    def __init__(self, hub_api_key: str):
        self.hub_api_key = hub_api_key

    def fetch_prompt_template(self, prompt_handle: str) -> str:
        """Fetch prompt template desde LangChain Hub."""
        prompt = hub.pull(prompt_handle)
        return prompt.template

    def list_available_prompts(self, category: str = "prompt-improver") -> list[str]:
        """List prompts disponibles por categoría."""
        # LangChain Hub tiene search endpoint
        pass

# Uso en DSPy
adapter = LangChainHubAdapter(os.getenv("LANGCHAIN_API_KEY"))
base_prompt = adapter.fetch_prompt_template("hwchase17/react")

# Usar como template en DSPy PromptImprover
improver = dspy.ChainOfThought(PromptImproverSignature)
improver.base_prompt = base_prompt
```

### 📚 Documentación

- [LangChain Hub Docs](https://docs.langchain.com/langsmith/manage-prompts-programmatically)
- [Manage prompts programmatically](https://docs.langchain.com/langsmith/manage-prompts-programmatically)

---

## 🥈 Opción 2: PromptLayer (SaaS - Paid)

**Fuente**: [docs.promptlayer.com](https://docs.promptlayer.com)

### ✅ Ventajas

- **Visual editor** para domain experts (no-code)
- **Prompt Registry** con Git-inspired version control
- **REST API** completa
- **Evaluation framework** integrado
- **Especializado en prompt management**

### ❌ Desventajas

- **No es gratis** (SaaS model, pricing no público)
- **Cloud-only** (no self-hosting)
- **Vendor lock-in**

### 🔧 REST API

```bash
# PromptLayer REST API endpoints
GET  /api/prompt_template/{prompt_name}  # Fetch prompt
POST /api/prompt_template                # Create prompt
PUT  /api/prompt_template/{prompt_name}  # Update prompt
GET  /api/prompt_template                # List all prompts
```

### 💻 Integración ejemplo

```python
import requests

PROMPTLAYER_API_KEY = "pl_xxx..."

def fetch_prompt(prompt_name: str) -> dict:
    """Fetch prompt desde PromptLayer."""
    response = requests.get(
        f"https://api.promptlayer.com/api/prompt_template/{prompt_name}",
        headers={"X-API-Key": PROMPTLAYER_API_KEY}
    )
    return response.json()

# Uso
prompt = fetch_prompt("prompt-improver-v2")
```

### 📚 Documentación

- [REST API Reference](https://docs.promptlayer.com/reference/rest-api-reference)
- [Quickstart Guide](https://docs.promptlayer.com/quickstart)

---

## 🥉 Opción 3: Langfuse (Open Source)

**Fuente**: [langfuse.com/docs](https://langfuse.com/docs)

### ✅ Ventajas

- **100% Open Source** (MIT License)
- **Self-hosting GRATIS** (Docker)
- **Prompt management** vía UI/SDK/API
- **LLM observability** incluida
- **Escalable** a billions de events

### ❌ Desventajas

- Requiere **self-hosting** (infra management)
- Más **complejo** que usar SaaS
- Menos feature-rich que PromptLayer para prompt management específico

### 🔧 API de Prompt Management

```python
from langfuse import Langfuse

# Inicializar
langfuse = Langfuse(
    secret_key="lfs-xxx...",
    public_key="pk-lf-xxx..."
)

# Crear prompt
prompt = langfuse.create_prompt(
    name="prompt-improver-v3",
    prompt="Actúa como experto en prompt engineering...",
    config={
        "model": "gpt-4",
        "temperature": 0.7
    }
)

# Fetch prompt
prompt = langfuse.get_prompt("prompt-improver-v3")
```

### 🐳 Self-hosting

```bash
# Docker Compose para self-hosting
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker-compose up -d
```

### 📚 Documentación

- [Open Source Prompt Management](https://langfuse.com/docs/prompt-management/overview)
- [Get Started](https://langfuse.com/docs/prompt-management/get-started)
- [Pricing](https://langfuse.com/pricing) (free self-hosted!)

---

## 🏆 Opción 4: HuggingFace Datasets (Datasets - Free)

**Fuente**: [huggingface.co/datasets](https://huggingface.co/datasets)

### ✅ Ventajas

- **100% Gratis** y open source
- **Datasets curados** de prompts
- **Programmatic access** vía datasets library
- **Sin vendor lock-in**

### 📁 Datasets relevantes

#### 1. **System Prompt Library**
- **URL**: [danielrosehill/System-Prompt-Library](https://huggingface.co/datasets/danielrosehill/System-Prompt-Library)
- **Descripción**: Library de system prompts para AI agents
- **Size**: 100+ prompts

```python
from datasets import load_dataset

dataset = load_dataset("danielrosehill/System-Prompt-Library")
for prompt in dataset['train']:
    print(prompt['text'])
```

#### 2. **MT Bench Prompts**
- **URL**: [HuggingFaceH4/mt_bench_prompts](https://huggingface.co/datasets/HuggingFaceH4/mt_bench_prompts)
- **Descripción**: Evaluation prompts para chat models
- **Size**: 80+ prompts

#### 3. **PromptSet Dataset**
- **URL**: [PromptSet Paper](https://arxiv.org/html/2402.16932v1)
- **Descripción**: 61,000+ developer prompts from open-source Python
- **Format**: JSON

### 🎯 Integración con tu pool actual

```python
from datasets import load_dataset
import dspy

def augment_pool_with_huggingface():
    """Augment few-shot pool con HuggingFace datasets."""

    # 1. Cargar System Prompt Library
    system_prompts = load_dataset("danielrosehill/System-Prompt-Library")

    # 2. Convertir a formato DSPy
    trainset = []
    for item in system_prompts['train']:
        example = dspy.Example(
            original_idea="System prompt for AI agent",
            context="",
            improved_prompt=item['text'],
            role="AI Assistant",
            directive=item['text'],
            framework="",
            guardrails="",
        ).with_inputs('original_idea', 'context')
        trainset.append(example)

    # 3. Merge con tu pool existente
    # datasets/exports/unified-fewshot-pool.json
    return trainset
```

---

## 📚 Opción 5: Awesome ChatGPT Prompts (GitHub Repo)

**Fuente**: [github.com/awesome-chatgpt-prompts/awesome_chatgpt](https://github.com/awesome-chatgpt-prompts/awesome_chatgpt)

### ✅ Ventajas

- **100% Gratis** y open source
- **Prompts curados** por la comunidad
- **Categorizados** por dominio
- **Fácil access** via GitHub raw URLs

### ❌ Desventajas

- **Sin API** (solo scraping de GitHub)
- **No estructurado** (requiere parsing)
- **Static** (no hay versioning dinámico)

### 🔧 Integración vía scraping

```python
import requests
import re

def scrape_awesome_chatgpt_prompts():
    """Scrape prompts desde GitHub README."""

    url = "https://raw.githubusercontent.com/awesome-chatgpt-prompts/awesome_chatgpt/main/README.md"
    response = requests.get(url)
    content = response.text

    # Parse prompts (ejemplo simple)
    prompts = []
    pattern = r'- \*\*([^*]+)\*\*: (.+)'

    for match in re.finditer(pattern, content):
        role = match.group(1)
        prompt_text = match.group(2)
        prompts.append({
            'role': role,
            'prompt': prompt_text
        })

    return prompts

# Uso
prompts = scrape_awesome_chatgpt_prompts()
```

---

## 📊 Comparison Matrix

| Feature | LangChain Hub | PromptLayer | Langfuse | HuggingFace | Awesome GitHub |
|---------|---------------|-------------|----------|-------------|----------------|
| **API Access** | ✅ Python SDK | ✅ REST API | ✅ Python SDK | ✅ Datasets API | ❌ Scraping only |
| **Free Tier** | ✅ Yes | ❌ Paid | ✅ Self-host free | ✅ Yes | ✅ Yes |
| **Prompt Curation** | ✅ Community | ✅ Premium | ✅ Community | ✅ Academic | ✅ Community |
| **Version Control** | ✅ Git-like | ✅ Git-inspired | ✅ Full history | ❌ No | ❌ No |
| **Visual Editor** | ❌ No | ✅ Yes | ✅ UI | ❌ No | ❌ No |
| **Evaluation** | ❌ No | ✅ Built-in | ✅ Metrics | ❌ No | ❌ No |
| **Self-hosting** | ❌ No | ❌ No | ✅ Yes | N/A | N/A |
| **DSPy Integration** | ✅ Native | ❌ Custom | ⚠️ Custom | ✅ Possible | ⚠️ Custom |
| **Setup Complexity** | 🟢 Low | 🟢 Low | 🟡 Medium | 🟢 Low | 🟢 Low |

---

## 🎯 Recomendación Estratégica

### Fase 1: Quick Win (1 día)

**Implementar LangChain Hub** como fuente primaria de prompts:

```python
# scripts/integrations/langchain_hub_integration.py
from langchain import hub
import dspy

class LangChainHubIntegration:
    """Integración de LangChain Hub con DSPy PromptImprover."""

    def __init__(self):
        self.hub = hub

    def augment_fewshot_pool(self, pool_path: str):
        """Augment existing pool con prompts desde LangChain Hub."""

        # Prompts curados relevantes para tu caso
        PROMPT_HANDLES = [
            "hwchase17/react",           # Chain-of-Thought reasoning
            "hwchase17/openai-functions", # Function calling
            # Agregar más cuando encuentres relevantes
        ]

        # Fetch prompts
        augmented = []
        for handle in PROMPT_HANDLES:
            try:
                prompt = hub.pull(handle)
                # Convertir a formato DSPy Example
                example = self._convert_to_dspy_example(prompt)
                augmented.append(example)
            except Exception as e:
                print(f"Failed to fetch {handle}: {e}")

        # Merge con pool existente
        # datasets/exports/unified-fewshot-pool.json
        return augmented

    def _convert_to_dspy_example(self, langchain_prompt) -> dspy.Example:
        """Convert LangChain prompt a DSPy Example."""
        return dspy.Example(
            original_idea=f"Prompt from LangChain Hub: {langchain_prompt.name}",
            context="",
            improved_prompt=langchain_prompt.template,
            role="AI Assistant",
            directive=langchain_prompt.template,
            framework="",
            guardrails="",
        ).with_inputs('original_idea', 'context')
```

### Fase 2: Aumentar Pool (1 semana)

**Integrar HuggingFace Datasets**:

1. System Prompt Library (100+ prompts)
2. MT Bench Prompts (80+ prompts)
3. PromptSet Dataset (61,000+ developer prompts - filtrar relevantes)

### Fase 3: Prompt Management Pro (opcional)

Si necesitas **prompt management avanzado**:

- **Para SaaS**: PromptLayer (paid)
- **Para Open Source**: Langfuse self-hosted

---

## 🚀 Plan de Acción Inmediato

### Paso 1: Configurar LangChain Hub (10 min)

```bash
# 1. Crear cuenta en LangSmith
# https://smith.langchain.com/

# 2. Crear API key
# Settings > API Keys > Create API Key

# 3. Agregar a .env
echo "LANGCHAIN_TRACING_V2=true" >> .env
echo "LANGCHAIN_API_KEY=lsv2_xxx..." >> .env

# 4. Instalar dependencias
pip install langchain langchain-openai
```

### Paso 2: Test integración (30 min)

```python
# scripts/tests/test_langchain_hub.py
from langchain import hub

def test_fetch_prompt():
    """Test fetching prompt from LangChain Hub."""
    prompt = hub.pull("hwchase17/react")
    assert prompt is not None
    print(f"✓ Fetched prompt: {prompt.name}")
    print(f"Template: {prompt.template[:100]}...")

if __name__ == "__main__":
    test_fetch_prompt()
```

### Paso 3: Augment few-shot pool (1-2h)

```python
# scripts/data/augment_pool_with_langchain.py
from pathlib import Path
import json
from langchain import hub
from scripts.integrations.langchain_hub_integration import LangChainHubIntegration

def main():
    """Augment few-shot pool con LangChain Hub prompts."""

    integrator = LangChainHubIntegration()

    # Load existing pool
    pool_path = Path("datasets/exports/unified-fewshot-pool.json")
    with open(pool_path) as f:
        existing_pool = json.load(f)

    # Augment with LangChain Hub
    new_examples = integrator.augment_fewshot_pool(pool_path)

    # Merge
    augmented_pool = {
        "metadata": existing_pool["metadata"],
        "examples": existing_pool["examples"] + new_examples
    }

    # Save
    output_path = Path("datasets/exports/unified-fewshot-pool-augmented.json")
    with open(output_path, 'w') as f:
        json.dump(augmented_pool, f, indent=2)

    print(f"✓ Pool augmentado: {len(existing_pool['examples'])} → {len(augmented_pool['examples'])}")

if __name__ == "__main__":
    main()
```

---

## 📚 Referencias

### APIs

- [LangChain Hub](https://smith.langchain.com/hub)
- [PromptLayer REST API](https://docs.promptlayer.com/languages/rest-api)
- [Langfuse Documentation](https://langfuse.com/docs)

### Datasets

- [PromptingGuide.ai Datasets](https://www.promptingguide.ai/datasets)
- [HuggingFace System Prompt Library](https://huggingface.co/datasets/danielrosehill/System-Prompt-Library)
- [HuggingFace MT Bench Prompts](https://huggingface.co/datasets/HuggingFaceH4/mt_bench_prompts)
- [PromptSet Dataset (61k prompts)](https://arxiv.org/html/2402.16932v1)

### Community Repos

- [Awesome ChatGPT Prompts](https://github.com/awesome-chatgpt-prompts/awesome_chatgpt)
- [Awesome Prompt Engineering](https://github.com/promptslab/Awesome-Prompt-Engineering)

---

**Conclusión**: LangChain Hub es la mejor opción para empezar - gratuita, nativa con DSPy, y con prompts curados por la comunidad. HuggingFace Datasets es excelente para augmentar el pool existente.
