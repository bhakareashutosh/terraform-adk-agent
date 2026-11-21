FROM python:3.12-slim

# Install dependencies and HashiCorp Terraform CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg lsb-release ca-certificates git \
    && curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o \
/usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
       > /etc/apt/sources.list.d/hashicorp.list \
    && apt-get update && apt-get install -y --no-install-recommends terraform \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY terraform_agent/ ./terraform_agent/
RUN mkdir -p /app/workspace

EXPOSE 8000

# Launch the ADK Web UI accessible from the host
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000"]
