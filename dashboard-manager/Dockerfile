# Use an official Python runtime as a parent image
FROM python

# Set the working directory
WORKDIR /app

# Update packages and install supervisor
#RUN apt-get update && apt-get install -y supervisor

RUN apt-get update && apt-get install -y docker.io 
RUN curl -L https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Copy the shared folder into the container
COPY shared/ ./shared/

# Copy the current directory contents into the container
COPY nodered_adaptor.py /app/

# Expose the Node-RED and adaptor service ports
EXPOSE 8084

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the supervisord command to manage the Node-RED and adaptor script when the container launches
CMD ["python", "nodered_adaptor.py"]


