FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q -e -DskipTests package || true
COPY src /src/src
RUN mvn -q -DskipTests package && cp target/java-jdbc-*.jar /app.jar

FROM eclipse-temurin:17-jre-alpine
RUN apk add --no-cache curl
COPY --from=build /app.jar /app.jar
EXPOSE 8080
CMD ["java", "-jar", "/app.jar"]


