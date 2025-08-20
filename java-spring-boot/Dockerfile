FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
# Clear cached failures and fetch deps with -U
RUN rm -rf /root/.m2/repository && mvn -q -U -DskipTests dependency:go-offline
COPY src /src/src
RUN mvn -q -U -DskipTests package && cp target/java-spring-boot-*.jar /app.jar

FROM eclipse-temurin:17-jre
RUN apt update && apt install -y curl
COPY --from=build /app.jar /app.jar
EXPOSE 8080
CMD ["java", "-jar", "/app.jar"]


