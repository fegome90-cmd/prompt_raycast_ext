#!/bin/bash
# Script para configurar HF CLI con token

echo "🔑 Configurando Hugging Face CLI..."
echo ""
echo "Necesitas un token de Hugging Face para descargar el modelo."
echo ""
echo "1. Ve a: https://huggingface.co/settings/tokens"
echo "2. Crea un nuevo token (o usa uno existente)"
echo "3. Copia el token"
echo ""
read -p "Pega tu token HF aquí: " HF_TOKEN

if [ -z "$HF_TOKEN" ]; then
    echo "❌ Error: Token vacío"
    exit 1
fi

echo ""
echo "🔐 Guardando token..."
huggingface-cli login --token "$HF_TOKEN"

if [ $? -eq 0 ]; then
    echo "✅ Login exitoso. Token guardado en ~/.huggingface/token"
    echo ""
    echo "📦 Ya puedes descargar el modelo con:"
    echo "   huggingface-cli download cradermacher/Novaeus-Promptist-7B-Instruct-v1-GUF-Q5_K_M-28c9ae58de5f54.4GB"
else
    echo "❌ Error en login. Verifica el token."
    exit 1
fi
