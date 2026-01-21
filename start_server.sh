#!/bin/bash

# Скрипт для запуска AI Product Enricher сервера в фоне
# Использование: ./start_server.sh

cd /root/ai_product_enricher

# Активация виртуального окружения
source .venv/bin/activate

# Установка переменных окружения
export APP_HOST=0.0.0.0
export APP_PORT=8000

# Запуск сервера
echo "Запуск AI Product Enricher сервера..."
python -m src.ai_product_enricher.main