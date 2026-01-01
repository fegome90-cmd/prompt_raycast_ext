#!/bin/bash

# Prompt Renderer Local - Setup Script
# Configura el entorno y deja el sistema corriendo

set -e

echo "🚀 Prompt Renderer Local - Setup"
echo "=================================="

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Verificar Ollama
echo ""
echo "1️⃣  Verificando Ollama..."
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Ollama no está instalado${NC}"
    echo "   Instala desde: https://ollama.com"
    exit 1
fi
echo -e "${GREEN}✅ Ollama instalado$(tput sgr0)"

# 2. Verificar que Ollama esté corriendo
echo ""
echo "2️⃣  Verificando Ollama daemon..."
if ! ollama list &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama no está corriendo, iniciando...${NC}"
    ollama serve > /tmp/ollama.log 2>&1 &
    echo "   Esperando a Ollama..."
    sleep 5
fi
echo -e "${GREEN}✅ Ollama corriendo$(tput sgr0)"

# 3. Verificar modelo
echo ""
echo "3️⃣  Verificando modelo Novaeus-Promptist-7B..."
MODEL_NAME="hf.co/mradermacher/Novaeus-Promptist-7B-Instruct-i1-GGUF"
if ! ollama list | grep -q "Novaeus-Promptist"; then
    echo -e "${YELLOW}⚠️  Modelo no encontrado, descargando...${NC}"
    echo "   Esto puede tomar varios minutos (5.4 GB)"
    ollama pull "$MODEL_NAME"
fi
echo -e "${GREEN}✅ Modelo instalado$(tput sgr0)"

# 4. Instalar dependencias Node
echo ""
echo "4️⃣  Instalando dependencias Node..."
if [ ! -d "node_modules" ]; then
    npm install
else
    echo -e "${GREEN}✅ Dependencias ya instaladas$(tput sgr0)"
fi

# 5. Verificar TypeScript
echo ""
echo "5️⃣  Verificando TypeScript..."
npx tsc --noEmit
echo -e "${GREEN}✅ TypeScript OK$(tput sgr0)"

# 6. Correr tests
echo ""
echo "6️⃣  Ejecutando tests..."
npm test -- src/core/llm/__tests__/novaeus-promptist.test.ts --run

# 7. Build
echo ""
echo "7️⃣  Build del proyecto..."
npm run build

# Resumen
echo ""
echo "=================================="
echo -e "${GREEN}✅ Setup completado!${NC}"
echo ""
echo "📦 Modelo: $MODEL_NAME"
echo "🌐 Ollama: http://localhost:11434"
echo ""
echo "🚀 Comandos útiles:"
echo "   npm run dev    - Iniciar extensión Raycast"
echo "   npm test       - Ejecutar tests"
echo "   npm run eval    - Ejecutar evaluador de calidad"
echo ""
echo "✨ ¡Listo para usar! Abre Raycast y busca 'Prompt Improver (Local)'"
