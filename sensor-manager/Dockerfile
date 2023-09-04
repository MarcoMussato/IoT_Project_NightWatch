# Use an official Python runtime as a parent image
FROM python

RUN apt-get update && apt-get install -y docker.io 
RUN curl -L https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the shared folder into the container
COPY shared/ ./shared/

# Copy the current directory contents into the container

COPY sensor_adaptor.py /app/

# Expose the sensor-simulation service port
EXPOSE 8085

# Run the sensor_docker.py script when the container launches
CMD ["python", "sensor_adaptor.py"]

