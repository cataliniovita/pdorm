FROM node:20-alpine

RUN apk add --no-cache curl

WORKDIR /app
COPY package.json package-lock.json* knexfile.js /app/
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY app.js /app/app.js

EXPOSE 3000
CMD ["node", "app.js"]


