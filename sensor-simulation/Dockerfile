# Use an official Python runtime as a parent image
FROM python

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the shared folder into the container
COPY shared/ ./shared/

# Copy the current directory contents into the container

COPY sensor_docker.py /app/
COPY sensor_generator.py /app/

# Install requests module
RUN pip install requests

# Run the sensor_docker.py script when the container launches
CMD ["python", "sensor_docker.py"]
