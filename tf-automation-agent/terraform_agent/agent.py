import os
import subprocess
from pathlib import Path

try:
    from google.adk.agents import Agent
except ImportError:
    from google.adk.agents.llm_agent import Agent

# Support running both inside Docker (/app/workspace) and locally
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "/app/workspace")).resolve()
try:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    WORKSPACE_DIR = (Path(__file__).parent.parent / "workspace").resolve()
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_path(filename: str) -> Path:
    target = (WORKSPACE_DIR / filename).resolve()
    if not str(target).startswith(str(WORKSPACE_DIR)):
        raise ValueError("Path traversal outside workspace is not allowed.")
    return target


def write_tf_file(filename: str, content: str) -> str:
    """Writes Terraform HCL code to a .tf file in the workspace.

    Args:
        filename: Name of the file (e.g., 'main.tf', 'variables.tf').
        content: Valid Terraform HCL configuration string.
    """
    if not filename.endswith(".tf"):
        return "Error: Filename must end with .tf"
    path = _safe_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Successfully wrote {filename} ({len(content)} bytes)."


def verify_terraform() -> str:
    """Runs 'terraform fmt -recursive', 'terraform init', 'terraform validate', and 'terraform plan'.

    Always run this after writing .tf files and show the plan summary to the user.
    """
    commands = [
        ["terraform", "fmt", "-recursive"],
        ["terraform", "init", "-input=false"],
        ["terraform", "validate"],
        ["terraform", "plan", "-input=false", "-no-color"],
    ]
    outputs = []
    for cmd in commands:
        try:
            res = subprocess.run(
                cmd, cwd=WORKSPACE_DIR, capture_output=True, text=True, timeout=180
            )
            outputs.append(f"$ {' '.join(cmd)}\n{res.stdout}\n{res.stderr}")
            if res.returncode != 0:
                return "VERIFICATION FAILED:\n" + "\n".join(outputs)
        except FileNotFoundError:
            return (
                "VERIFICATION FAILED:\nTerraform CLI not found. Please ensure "
                "'terraform' is installed and in your PATH."
            )
        except subprocess.TimeoutExpired:
            return f"VERIFICATION FAILED:\nCommand '{' '.join(cmd)}' timed out after 180 seconds."

    return "VERIFICATION PASSED:\n" + "\n".join(outputs)


def apply_terraform(user_confirmed: bool) -> str:
    """Applies the verified Terraform plan to provision infrastructure.

    Args:
        user_confirmed: Must ONLY be True if the user explicitly replied 'yes' or 'approve'.
    """
    if not user_confirmed:
        return "APPLY ABORTED: Explicit user confirmation is required before running terraform apply."

    cmd = ["terraform", "apply", "-auto-approve", "-input=false", "-no-color"]
    try:
        res = subprocess.run(
            cmd, cwd=WORKSPACE_DIR, capture_output=True, text=True, timeout=300
        )
        output = f"$ {' '.join(cmd)}\n{res.stdout}\n{res.stderr}"
        if res.returncode != 0:
            return "APPLY FAILED:\n" + output
        return "APPLY SUCCESSFUL:\n" + output
    except FileNotFoundError:
        return (
            "APPLY FAILED:\nTerraform CLI not found. Please ensure "
            "'terraform' is installed and in your PATH."
        )
    except subprocess.TimeoutExpired:
        return "APPLY FAILED:\nCommand 'terraform apply' timed out after 300 seconds."


# ADK Root Agent Configuration
root_agent = Agent(
    name="terraform_agent",
    model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),
    description="Agent for generating, verifying, and applying Terraform configurations.",
    instruction=(
        "You are an infrastructure automation agent that manages Terraform configurations.\n\n"
        "Follow this exact workflow for all user requests:\n"
        "1. Write complete, valid Terraform HCL configuration files using `write_tf_file`.\n"
        "2. Always run `verify_terraform` after writing or updating files to format, initialize, validate, and plan changes.\n"
        "3. Review the verification output and summarize the execution plan (resources to add, change, or destroy) for the user.\n"
        "4. Explicitly ask the user for confirmation (e.g., 'yes' or 'approve') before running apply.\n"
        "5. ONLY invoke `apply_terraform(user_confirmed=True)` when the user explicitly grants approval. Never assume approval."
    ),
    tools=[write_tf_file, verify_terraform, apply_terraform],
)
