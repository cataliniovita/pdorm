FROM php:8.2-cli-alpine

RUN apk add --no-cache curl postgresql-dev \
 && docker-php-ext-install pdo pdo_mysql pdo_pgsql

WORKDIR /app
COPY index.php /app/index.php

EXPOSE 8080

CMD ["php", "-S", "0.0.0.0:8080", "/app/index.php"]


