set -e

ENV_FILE=".env"

generate_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

if [ -f "$ENV_FILE" ]; then
    echo "Файл $ENV_FILE уже существует."
    echo "Проверяю недостающие секреты..."

    for VAR in JWT_SECRET_KEY WEBHOOK_SECRET; do
        if ! grep -q "^${VAR}=" "$ENV_FILE"; then
            SECRET=$(generate_secret)
            echo "${VAR}=${SECRET}" >> "$ENV_FILE"
            echo "  + Сгенерирован ${VAR}"
        else
            echo "  • ${VAR} уже задан, пропускаю"
        fi
    done

    if ! grep -q "^POSTGRES_PASSWORD=" "$ENV_FILE" || grep -q "^POSTGRES_PASSWORD=$" "$ENV_FILE"; then
        echo "  ⚠️  POSTGRES_PASSWORD не задан! Укажи его вручную перед запуском."
    else
        echo "  • POSTGRES_PASSWORD уже задан"
    fi

    echo "Готово."
    exit 0
fi

echo "Создаю $ENV_FILE..."
echo ""
read -p "Введи пароль для PostgreSQL (минимум 12 символов): " POSTGRES_PASSWORD

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "Ошибка: пароль не может быть пустым"
    exit 1
fi

if [ ${#POSTGRES_PASSWORD} -lt 12 ]; then
    echo "Ошибка: пароль слишком короткий (минимум 12 символов)"
    exit 1
fi

cat > "$ENV_FILE" <<EOF
# === База данных ===
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=db

# === Безопасность API ===
JWT_SECRET_KEY=$(generate_secret)
WEBHOOK_SECRET=$(generate_secret)
EOF

echo ""
echo "Файл $ENV_FILE создан."
echo "Не забудь прописать тот же WEBHOOK_SECRET в конфигурации Livekit!"
