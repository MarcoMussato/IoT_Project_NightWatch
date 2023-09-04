# Use an official Python runtime as a parent image
FROM python

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt

# Copy the shared folder into the container
COPY shared/ ./shared/

# Copy the current directory contents into the container
COPY data_extractor.py /app/
COPY db_data_adaptor.py /app/
COPY db_endpoints_adaptor.py /app/

# Expose the MongoDB adaptor service ports
EXPOSE 8081 8082

# Copy the supervisord.conf file into the container
COPY supervisord.conf /etc/

# Install requests module
RUN pip3 install requests

# Run the supervisord command to manage the MongoDB adaptor scripts when the container launches
CMD ["supervisord", "-c", "/etc/supervisord.conf"]

