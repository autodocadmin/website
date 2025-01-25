# Use a base image with Python installed
FROM python:3.12-slim

# Install LibreOffice and dependencies
#RUN apt-get update && apt-get install -y libreoffice 

# Set the working directory inside the container
WORKDIR /app

# Copy your application's requirements.txt into the container
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt



# Expose the Flask default port
EXPOSE 5000

# Copy the rest of your application code into the container
COPY . .

# run the command to start the Flask app
#CMD ["python", "app.py"]

# Command to run Gunicorn with your Flask app (assumes your app is named `app.py` with `app` object) -w 4 -k gevent
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "app:app"]