# Управление сервером AI Product Enricher

## Быстрый запуск сервера в фоне

Сервер настроен как systemd сервис и автоматически запускается при загрузке системы.

### Управление сервером

#### Через systemd (рекомендуется)
```bash
sudo systemctl start ai-product-enricher    # Запуск
sudo systemctl stop ai-product-enricher     # Остановка
sudo systemctl restart ai-product-enricher  # Перезапуск
sudo systemctl status ai-product-enricher   # Статус
sudo systemctl enable ai-product-enricher   # Автозапуск при загрузке
```

#### Через удобный скрипт
```bash
./manage_server.sh start    # Запуск
./manage_server.sh stop     # Остановка
./manage_server.sh restart  # Перезапуск
./manage_server.sh status   # Статус
./manage_server.sh logs     # Последние логи
```

### Проверка работы

```bash
# Health check
curl http://128.199.126.60:8000/api/v1/health

# Swagger UI
curl http://128.199.126.60:8000/docs

# Тест API
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{"product": {"name": "iPhone 15", "country_origin": "CN"}}'
```

### Мониторинг

```bash
# Логи systemd
sudo journalctl -u ai-product-enricher -f

# Проверка порта
ss -tlnp | grep :8000

# Проверка процесса
ps aux | grep python | grep enricher
```

### Резервное копирование логов

```bash
# Сохранить логи в файл
sudo journalctl -u ai-product-enricher > server_logs_$(date +%Y%m%d_%H%M%S).txt
```

## Структура файлов

- `manage_server.sh` - скрипт управления сервером
- `/etc/systemd/system/ai-product-enricher.service` - systemd сервис
- `start_server.sh` - альтернативный скрипт запуска (не используется)

## Troubleshooting

### Сервер не запускается
```bash
# Проверить статус
sudo systemctl status ai-product-enricher

# Посмотреть логи
sudo journalctl -u ai-product-enricher -n 50
```

### Порт занят
```bash
# Найти процесс
lsof -i :8000

# Остановить
sudo systemctl stop ai-product-enricher
```

### Перезагрузка системы
Сервер автоматически запустится после перезагрузки благодаря `systemctl enable`.