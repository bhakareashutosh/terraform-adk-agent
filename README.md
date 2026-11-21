# ADK Terraform Automation Agent on Docker

A Gemini-powered infrastructure automation agent built with **Google Agent Development Kit (ADK)** and Docker. It autonomously generates Terraform configurations, verifies them through formatting, validation, and plan generation, and executes `terraform apply` only after explicit human approval.

---

## Project Structure

```
.
├── ADK Terraform Automation Agent on Docker.pdf
├── README.md
├── .gitignore
└── tf-automation-agent/
    ├── Dockerfile
    ├── requirements.txt
    ├── .env
    ├── .gitignore
    ├── workspace/               # Mounted volume where .tf files & state persist
    │   └── .gitkeep
    └── terraform_agent/
        ├── __init__.py
        └── agent.py             # Tools & ADK root_agent definition
```

---

## Agent Workflow & Human-in-the-Loop Safeguards

1. **Generation (`write_tf_file`)**: Writes valid HCL `.tf` files safely inside the sandboxed `/app/workspace` directory with path traversal protection.
2. **Verification (`verify_terraform`)**: Executes `terraform fmt -recursive`, `terraform init -input=false`, `terraform validate`, and `terraform plan -input=false -no-color`.
3. **Approval Gate (`apply_terraform`)**: The agent inspects the plan output, presents the resource diff to the user, and pauses for explicit human confirmation (`yes` or `approve`).
4. **Execution**: `apply_terraform` only runs when `user_confirmed=True`.

---

## Getting Started

### 1. Prerequisites
- Docker (or local Python 3.12+ with [Terraform CLI](https://developer.hashicorp.com/terraform/install))
- Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)
- Cloud provider credentials (e.g. AWS or GCP) if managing live cloud resources

### 2. Configure Environment
Edit `tf-automation-agent/.env`:
```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Cloud provider credentials
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### 3. Build & Run with Docker

```bash
cd tf-automation-agent

# Build Docker image
docker build -t adk-terraform-agent .

# Run container with volume mounted
docker run -it --rm \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/workspace:/app/workspace" \
  adk-terraform-agent
```

### 4. Interact with the Agent
- **Web UI:** Open [http://localhost:8000](http://localhost:8000) in your browser.
- **CLI Mode:** Alternatively run with `adk run terraform_agent`.
