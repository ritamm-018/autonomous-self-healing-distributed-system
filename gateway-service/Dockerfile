# STAGE 1: BUILD
FROM maven:3.8.5-openjdk-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
# We skip tests to speed up the build for this demo
RUN mvn clean package -DskipTests

# STAGE 2: RUN
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
