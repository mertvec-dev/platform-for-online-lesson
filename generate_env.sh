set -e

ENV_FILE=".env"

generate_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

if [ -f "$ENV_FILE" ]; then
    echo "Файл $ENV_FILE уже существует."
    echo "Проверяю недостающие секреты..."

    for VAR in JWT_SECRET_KEY WEBHOOK_SECRET REDIS_PASSWORD; do
        if ! grep -q "^${VAR}=" "$ENV_FILE"; then
            SECRET=$(generate_secret)
            echo "${VAR}=${SECRET}" >> "$ENV_FILE"
            echo "  + Сгенерирован ${VAR}"
        else
            # Если переменная задана, но пустая — заполнить
            if grep -q "^${VAR}=$" "$ENV_FILE"; then
                SECRET=$(generate_secret)
                sed -i "s/^${VAR}=$/${VAR}=${SECRET}/" "$ENV_FILE"
                echo "  + Заполнен пустой ${VAR}"
            else
                echo "  • ${VAR} уже задан, пропускаю"
            fi
        fi
    done

    if ! grep -q "^POSTGRES_PASSWORD=" "$ENV_FILE" || grep -q "^POSTGRES_PASSWORD=$" "$ENV_FILE"; then
        echo "  ⚠️  POSTGRES_PASSWORD не задан! Укажи его вручную перед запуском."
    else
        # Проверка длины пароля PostgreSQL
        PGPASS=$(grep "^POSTGRES_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2-)
        if [ ${#PGPASS} -lt 12 ]; then
            echo "  ⚠️  POSTGRES_PASSWORD слишком короткий (${#PGPASS} < 12 символов)"
        else
            echo "  • POSTGRES_PASSWORD уже задан"
        fi
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

while true; do
    read -p "Введи пароль для Redis (минимум 12 символов): " REDIS_PASSWORD

    if [ -z "$REDIS_PASSWORD" ]; then
        echo "Ошибка: пароль не может быть пустым"
        continue
    fi

    if [ ${#REDIS_PASSWORD} -lt 12 ]; then
        echo "Ошибка: пароль Redis слишком короткий (минимум 12 символов)"
        continue
    fi

    if [ "$POSTGRES_PASSWORD" = "$REDIS_PASSWORD" ]; then
        echo "⚠️  Пароли не должны совпадать. Пожалуйста, придумай другой пароль для Redis."
        continue
    fi

    break
done

cat > "$ENV_FILE" <<EOF
# === База данных ===
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=db

# === Redis ===
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# === Безопасность API ===
JWT_SECRET_KEY=$(generate_secret)
WEBHOOK_SECRET=$(generate_secret)
EOF

echo ""
 echo "Файл $ENV_FILE создан."
 echo "Не забудь прописать тот же WEBHOOK_SECRET в конфигурации Livekit!"
