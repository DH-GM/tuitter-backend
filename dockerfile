# AWS Lambda Python base (has the runtime interface client built-in)
FROM public.ecr.aws/lambda/python:3.11

# Lambda expects code under /var/task
WORKDIR /var/task

# Install deps
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (so /var/task/main.py exists)
COPY ./backend/ .

# Lambda will call your Mangum handler directly
CMD ["main.handler"]
