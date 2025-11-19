#!/bin/bash
echo "🚀 Deploying Email Classifier..."

# Parar container existente
docker stop email-classifier-api || true
docker rm email-classifier-api || true

# Build da imagem
docker build -t email-classifier-optimized .

# Rodar novo container
docker run -d \
  --name email-classifier-api \
  -p 8000:8000 \
  -e USE_ML_MODELS=true \
  --memory=1g \
  --cpus=1.0 \
  email-classifier-optimized

echo "✅ Deploy concluído!"
echo "📊 Logs: docker logs -f email-classifier-api"
echo "🌐 Health: curl http://localhost:8000/health"