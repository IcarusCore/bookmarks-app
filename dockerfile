# Use the official Python 3.11 slim image as the base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app directory into the container
COPY . .

# Expose the port your Flask app will run on
EXPOSE 5000

# Command to run the Flask app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
