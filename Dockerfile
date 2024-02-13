# Use the official MySQL 8.0 image as the base image
FROM mysql:8.0

# Set the root password for MySQL
ENV MYSQL_ROOT_PASSWORD=password

# Create a new database
ENV MYSQL_DATABASE=chatapp

# Copy the initial SQL file to the container
COPY schema.sql /docker-entrypoint-initdb.d/

# Expose the default MySQL port
EXPOSE 3306
