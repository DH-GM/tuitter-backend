# Use a slim Python 3.11 image as the base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies first.
# This allows Docker to cache this layer if requirements.txt hasn't changed.
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script to the container.
COPY ./entrypoint.sh .
# Ensure the entrypoint script is executable.
RUN chmod +rx ./entrypoint.sh

# Set the entrypoint to the full path of the script.
# This script will run when the container starts.
ENTRYPOINT ["./entrypoint.sh"]

# Copy the rest of the application files.
COPY ./backend/ .

# Expose the port for the application
EXPOSE 8000

# Define the command that will be passed as arguments to the entrypoint.
# The entrypoint script will then execute this.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

