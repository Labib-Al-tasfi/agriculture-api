#Base image 
FROM python:3.11-slim

#et working directory inside the container 
WORKDIR /app

#Copy requirements first (Docker caches this layer)
COPY requirements.txt .

#Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

#Copy the rest of the project 
COPY . .

#Expose the port FastAPI will run on 
EXPOSE 8000

#Command to start the server 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
