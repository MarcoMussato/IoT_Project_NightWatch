# Use an official Python runtime as a parent image
FROM python

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared folder into the container
COPY shared/ /app/shared/

# Copy the current directory contents into the container
COPY bot_patient.py /app/
COPY bot_doctor.py /app/

# Copy the supervisord configuration file into the container
COPY supervisord.conf /etc/

# Install requests module
RUN pip3 install requests

# Run supervisord when the container launches
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
