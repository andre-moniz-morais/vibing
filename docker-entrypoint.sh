#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Fallback para criar eventuais pastas necessárias se não existirem
mkdir -p /app/media /app/staticfiles

# Executa o comando principal recebido do CMD (ex: daphne)
exec "$@"
