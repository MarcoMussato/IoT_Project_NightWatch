# Use an official Python runtime as a parent image
FROM python

# Set the working directory
WORKDIR /app

# Update packages and install supervisor
RUN apt-get update && apt-get install -y supervisor

# Copy requirements.txt into the container
COPY requirements.txt /app/


# Install any needed packages specified in requirements.txt
RUN pip install  -r requirements.txt

# Copy the shared folder into the container
COPY shared/ ./shared/

# Copy the current directory contents into the container

COPY apnea_detection.py /app/
COPY data_process.py /app/
COPY data_storage.py /app/
COPY data_template.py /app/
COPY generate_weekly_report.py /app/
COPY KaTeX_Main-Bold.ed829b5f.ttf /app/
COPY stats.py /app/
COPY alert.py /app/

# Expose the data-processing-statistics service port
EXPOSE 8086

# Create a supervisord.conf file in the data-processing-statistics folder
COPY supervisord.conf /etc/

# Install requests module
RUN pip install requests

# Run the supervisord command to manage the data processing and statistics scripts when the container launches
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
