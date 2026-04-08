# STAGE 1: BUILD
FROM maven:3.8.5-openjdk-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# STAGE 2: RUN
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

# TEACHER NOTE:
# This service needs to run 'docker restart'.
# So we need to install the docker client inside this container!
RUN apk add --no-cache docker-cli

ENTRYPOINT ["java", "-jar", "app.jar"]
