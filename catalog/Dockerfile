# Use an official Python runtime as a parent image
FROM python

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared folder into the container
COPY shared/ ./shared/

# Copy the current directory contents into the container
COPY catalog.py /app/
COPY config_catalog.json /app/


# Expose the catalog service port
EXPOSE 8080

# Define environment variable
ENV NAME World

# Install requests module
RUN pip install requests

# Run the catalog.py script when the container launches
CMD ["python", "catalog.py"]
