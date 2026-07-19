# =============================================================================
# ПЕРВЫЙ ЗАПУСК CERTBOT
# Выполняется ОДИН РАЗ вручную на сервере для получения TLS-сертификатов.
# После этого certbot будет обновлять их автоматически раз в 12 часов.
#
# Требования:
#   1. В .env задан DOMAIN_NAME (реальный домен, указывающий на сервер)
#   2. Порт 80 открыт (для ACME-челленджа)
#   3. docker compose up -d уже выполнен (nginx работает на порту 80)
#
# Использование:
#   chmod +x certbot_init.sh
#   ./certbot_init.sh
# =============================================================================

set -e

DOMAIN=$(grep "^DOMAIN_NAME=" .env | cut -d'=' -f2 | cut -d'#' -f1 | tr -d ' ')

if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "example.com" ]; then
    echo "ОШИБКА: DOMAIN_NAME не задан в .env или равен 'example.com'"
    echo "Укажи реальный домен в .env и повтори."
    exit 1
fi

echo "Запрашиваю TLS-сертификат для домена: $DOMAIN"

docker compose run --rm certbot \
    certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "${CERTBOT_EMAIL:-admin@$DOMAIN}" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

echo ""
echo "Сертификат получен! Перезапускаю nginx..."
docker compose restart nginx

echo ""
echo "Готово. HTTPS работает."
echo "Проверь: https://$DOMAIN/"
