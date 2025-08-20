FROM golang:1.22-alpine AS build
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY . .
# Ensure go.sum is generated for all deps
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux GOARCH=$(if [[ $(uname -m) == "aarch64" ]]; then echo arm64; else echo amd64; fi) go build -o server ./main.go

FROM alpine:3.19
RUN apk add --no-cache ca-certificates curl
WORKDIR /srv
COPY --from=build /app/server /srv/server
EXPOSE 8080
ENV INTERPOLATE=1
CMD ["/srv/server"]


