# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /frontend

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Cloud Run will set this environment variable, but it's good practice
ENV PORT 8080

# Command to run your app
# This uses the $PORT variable and listens on 0.0.0.0, as required
# CMD uvicorn main:app --host 0.0.0.0 --port $PORT
CMD streamlit run streamlit_app.py --server.enableCORS false --server.enableXsrfProtection false