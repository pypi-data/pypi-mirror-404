import typer
import docker
import time
import os
import hashlib
from typing import Optional
from lucid_schemas import (
    LUCID_LABEL_AUDITOR,
    LUCID_LABEL_SCHEMA_VERSION,
    LUCID_LABEL_PHASE,
    LUCID_LABEL_INTERFACES
)

app = typer.Typer()

def get_docker_client():
    """Initialize and return a Docker client.

    Handles connection errors gracefully and exits if the Docker daemon
    is unreachable.

    Returns:
        docker.DockerClient: The connected Docker client.
    """
    try:
        return docker.from_env()
    except Exception as e:
        typer.echo(f"[!] Could not connect to Docker: {e}")
        raise typer.Exit(code=1)

@app.command()
def verify(image: str):
    """Verify an auditor image's contract and labels.

    This command performs a 'compliance probe' on a local container image to
    ensure it meets the Lucid Auditor Standard. It checks:
    1.  **OCI Labels**: Required metadata like fields, version, and phase.
    2.  **API Contract**: Starts an ephemeral instance and probes /health and /audit.

    Args:
        image: The tag of the local Docker image to verify (e.g., 'compliance-auditor:v1').
    """
    client = get_docker_client()
    
    # 1. Inspect Labels
    typer.echo(f"[*] Inspecting labels for {image}...")
    try:
        img = client.images.get(image)
        labels = img.labels
    except Exception as e:
        typer.echo(f"[!] Error inspecting image: {e}")
        raise typer.Exit(code=1)

    required_labels = [LUCID_LABEL_AUDITOR, LUCID_LABEL_SCHEMA_VERSION, LUCID_LABEL_PHASE]
    for label in required_labels:
        if label not in labels:
            typer.echo(f"[!] Missing required label: {label}")
            raise typer.Exit(code=1)
    
    typer.echo(f"[+] Basic labels found. Phase: {labels.get(LUCID_LABEL_PHASE)}")

    # 2. Compliance Probe (Health & Audit)
    typer.echo("[*] Starting ephemeral container for compliance probe...")
    container = None
    try:
        ports = labels.get(LUCID_LABEL_INTERFACES, "http:8080")
        internal_port = ports.split(":")[-1]
        
        container = client.containers.run(
            image, 
            detach=True, 
            publish_all_ports=True,
            environment={
                "TEE_PROVIDER": "NONE",
                "LUCID_VERIFIER_URL": ""
            }
        )
        
        container.reload()
        typer.echo(f"[*] Container ports mapping: {container.ports}")
        
        # Look for the internal_port in the mapping
        host_config = None
        for port_key, mapping in container.ports.items():
            if port_key.startswith(f"{internal_port}/"):
                host_config = mapping
                break
            
        if not host_config:
            raise Exception(f"Port {internal_port} not mapped to host. Ports: {container.ports}")
            
        host_port = host_config[0]['HostPort']
        url = f"http://localhost:{host_port}"
        
        # Wait for start (simple polling)
        success = False
        for _ in range(10):
            try:
                import httpx
                with httpx.Client() as http:
                    resp = http.get(f"{url}/health", timeout=2.0)
                    if resp.status_code == 200:
                        success = True
                        break
            except Exception:
                time.sleep(1)
        
        if not success:
            raise Exception("Auditor did not become healthy within 10 seconds")

        with httpx.Client() as http:
            # Check Audit endpoint (POST /audit)
            typer.echo(f"[*] Probing {url}/audit...")
            mock_event = {"event": "verify_probe", "payload": "ping"}
            resp = http.post(f"{url}/audit", json=mock_event, timeout=5.0)
            if resp.status_code not in [200, 201]:
                typer.echo(f"[!] Audit probe failed with status {resp.status_code}")
                raise typer.Exit(code=1)
            
        typer.echo("[+] Compliance probe successful!")
        
    except Exception as e:
        typer.echo(f"[!] Verification failed: {e}")
        raise typer.Exit(code=1)
    finally:
        if container:
            try:
                container.stop(timeout=2)
                container.remove()
            except Exception:
                pass

    typer.echo("[*] Verification complete. Auditor is compliant.")

@app.command()
def publish(image: str, registry: Optional[str] = None):
    """Verify, sign, and push an auditor image.

    This is the primary way to release an Auditor to the Lucid network.
    It performs the following steps:
    1.  **Verify**: Runs the `lucid auditor verify` suite.
    2.  **Sign**: Calculates the image digest and signs it using the API key (HMAC).
    3.  **Push**: Uploads the image to the specified container registry.
    4.  **Notarize**: Registers the signed digest with the centralized Verifier service.

    Args:
        image: The local image tag to publish.
        registry: The target container registry (e.g., 'ghcr.io/my-org').
            If not provided, skips the push step and only notarizes.

    The API key is read from the LUCID_API_KEY environment variable,
    or prompted interactively if not set.
    """
    api_key = os.getenv("LUCID_API_KEY")
    if not api_key:
        api_key = typer.prompt("Lucid API Key", hide_input=True)

    verifier_url = os.getenv("LUCID_VERIFIER_URL", "http://localhost:8000")

    # 1. Verify Image Contract
    typer.echo(f"[*] Publishing {image}...")
    verify(image)

    # 2. Get Image Digest
    client = get_docker_client()
    img = client.images.get(image)
    digest = img.attrs.get('Id', 'unknown-digest')
    
    # 3. Sign Digest using HMAC-SHA256 with API key
    import hmac
    typer.echo(f"[*] Signing digest {digest[:12]}...")
    signature = hmac.new(
        api_key.encode(),
        digest.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # 4. Push to Registry (if provided)
    if registry:
        typer.echo(f"[*] Tagging and pushing image to {registry}...")
        try:
            repository = f"{registry}/{image.split('/')[-1]}"
            img.tag(repository)
            for line in client.images.push(repository, stream=True, decode=True):
                if 'status' in line:
                    typer.echo(f"    {line['status']}")
            typer.echo(f"[+] Image pushed to {repository}")
            push_url = repository
        except Exception as e:
            typer.echo(f"[!] Push failed: {e}")
            raise typer.Exit(code=1)
    else:
        typer.echo("[*] No registry provided, skipping push.")
        push_url = image

    # 5. Notarize in Lucid Registry
    # Register BOTH the image reference (tag) AND the SHA digest
    # This ensures matching regardless of how the auditor identifies itself
    typer.echo(f"[*] Registering notarization with Lucid Verifier at {verifier_url}...")
    try:
        import httpx
        with httpx.Client() as http:
            # Register by SHA digest
            notarize_req_digest = {
                "image_digest": digest,
                "image_url": push_url,
                "signature": signature,
                "signer_subject": f"api-key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
            }
            resp = http.post(
                f"{verifier_url}/notarize/api", 
                json=notarize_req_digest,
                headers={"X-API-Key": api_key}
            )
            if resp.status_code != 200:
                typer.echo(f"[!] Notarization failed: {resp.text}")
                raise typer.Exit(code=1)
            
            # Also register by image reference (for Operator injection compatibility)
            image_ref = push_url  # e.g., "lucid-auditor-sidecar:latest"
            if image_ref != digest:
                notarize_req_ref = {
                    "image_digest": image_ref,
                    "image_url": push_url,
                    "signature": signature,
                    "signer_subject": f"api-key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
                }
                resp = http.post(
                    f"{verifier_url}/notarize/api", 
                    json=notarize_req_ref,
                    headers={"X-API-Key": api_key}
                )
                # Ignore errors for duplicate registration
                if resp.status_code == 200:
                    typer.echo(f"[+] Also registered image reference: {image_ref}")
                    
    except Exception as e:
        typer.echo(f"[!] Registry connection failed: {e}")
        raise typer.Exit(code=1)

    # 6. Finalize
    typer.echo("[+] Auditor notarized successfully!")
    typer.echo(f"    Digest: {digest[:20]}...")
    typer.echo(f"    Image Ref: {push_url}")
    typer.echo(f"    Signature: {signature[:20]}...")

