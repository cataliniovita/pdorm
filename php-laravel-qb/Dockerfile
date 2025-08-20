FROM php:8.2-cli-alpine

RUN apk add --no-cache bash git unzip curl \
    && docker-php-ext-install pdo pdo_mysql

WORKDIR /app

# Install Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

COPY composer.json /app/composer.json
RUN composer install --no-dev --no-progress --prefer-dist --no-interaction

COPY index.php /app/index.php

EXPOSE 8080
CMD ["php", "-S", "0.0.0.0:8080", "/app/index.php"]


