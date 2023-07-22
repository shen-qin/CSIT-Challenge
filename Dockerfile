# Use an official Python runtime as the base image
FROM python:3.9.16

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file and install the Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files into the container
COPY . .

# Expose the port that the Falcon application will listen on
EXPOSE 8080

# Run the Falcon application when the container starts
CMD ["python", "rest_server.py"]
