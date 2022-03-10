FROM rockylinux:8

# Set Work Directoy
WORKDIR /app

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

# Install Dependencies
RUN yum install -y python3
RUN python3 -m pip install --upgrade pip
COPY ./requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Copy Project
COPY . .
