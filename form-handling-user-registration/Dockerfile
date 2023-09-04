# Use an official Python runtime as a parent image
FROM python

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the shared folder into the container
COPY shared/ /app/shared/

# Copy the current directory contents into the container

COPY new_user_form_service.py /app/
COPY form_new_doctor.html /app/
COPY templates /app/templates/

# Expose the form-handling-user-registration service port
EXPOSE 80

# Define environment variable
ENV NAME World

# Install requests module
RUN pip install requests

# Run the new_user_form_service.py script when the container launches
CMD ["python", "new_user_form_service.py"]
