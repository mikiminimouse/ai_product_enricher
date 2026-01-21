#!/bin/bash

# Скрипт для управления AI Product Enricher сервером
# Использование: ./manage_server.sh [start|stop|restart|status|logs]

SERVICE_NAME="ai-product-enricher"

case "$1" in
    start)
        echo "Запуск сервера..."
        sudo systemctl start $SERVICE_NAME
        sleep 2
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    stop)
        echo "Остановка сервера..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Перезапуск сервера..."
        sudo systemctl restart $SERVICE_NAME
        sleep 2
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    status)
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    logs)
        echo "Последние логи сервера:"
        sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Примеры:"
        echo "  $0 start    - запустить сервер"
        echo "  $0 stop     - остановить сервер"
        echo "  $0 restart  - перезапустить сервер"
        echo "  $0 status   - статус сервера"
        echo "  $0 logs     - последние логи"
        exit 1
        ;;
esac