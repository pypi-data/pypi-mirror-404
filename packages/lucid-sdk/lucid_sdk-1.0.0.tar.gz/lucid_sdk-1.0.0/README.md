# Lucid SDK

The developer interface for building custom AI Auditors and composing secure **Auditor Chains**.

## Installation

### Private Git Install (Recommended for external users)

```bash
# Install with pip (requires GitHub access)
pip install "lucid-sdk @ git+https://github.com/Lucid-Computing/lucid-monorepo.git@main#subdirectory=packages/lucid-sdk"

# With optional extras
pip install "lucid-sdk[presidio-analyzer] @ git+https://github.com/Lucid-Computing/lucid-monorepo.git@main#subdirectory=packages/lucid-sdk"
```

For private repository access, configure git credentials:

```bash
# Using SSH
pip install "lucid-sdk @ git+ssh://git@github.com/Lucid-Computing/lucid-monorepo.git@main#subdirectory=packages/lucid-sdk"

# Using Personal Access Token
pip install "lucid-sdk @ git+https://${GITHUB_TOKEN}@github.com/Lucid-Computing/lucid-monorepo.git@main#subdirectory=packages/lucid-sdk"
```

### Monorepo Development

```bash
# From the monorepo root
uv sync

# Or using pip with editable installs
pip install -e packages/lucid-schemas
pip install -e packages/lucid-sdk
```

## 🌟 Role in Architecture
The **Lucid SDK** is the bridge between AI workloads and the Lucid Trust Platform. It provides:
1.  **Phase-Aware Instrumentation**: Specialized decorators for every stage of the AI lifecycle (Build, Prompt, Execution, Response).
2.  **Cryptographic Integrity**: Automatically handles evidence signing using integrated **Confidential Containers (CoCo)** Hardware Root of Trust.
3.  **Standardization**: Ensures all data conforms to `lucid-schemas` and includes critical context like execution phase.

## 🛠️ Lifecycle Phases & Example Auditor Gallery

The following auditors are **examples** of the types of specialized safety nodes you can build using the Lucid SDK. By leveraging **dependency injection** of external packages (via the SDK's "extras"), developers can quickly wrap world-class safety tools into verifiable TEE sidecars.

Auditors are categorized into four distinct lifecycle phases:

### Phase 1: Artifact Safety (`@sdk.on_artifact()`)
**Goal:** Verify the "factory" and the "product" before execution. These auditors validate supply chains, signatures, and safety benchmarks.

- **`lucid-eval-auditor`** (`lucid-sdk[inspect-ai]`): Runs rigorous safety benchmarks using UK Government's [inspect-ai](https://github.com/UKGovernmentBEIS/inspect_ai). Proves model passes safety thresholds (e.g., Bioweapons refusal) before deployment.
- **`lucid-integrity-auditor`** (`lucid-sdk[sigstore]`): Validates cryptographic signatures of weights and images via [Sigstore](https://www.sigstore.dev/). Prevents "Model Poisoning" by ensuring artifacts match research team signatures.
- **`lucid-sbom-auditor`** (`lucid-sdk[cyclonedx-python-lib]`): Generates/validates SBOMs and checks for CVEs using [cyclonedx-python-lib](https://github.com/CycloneDX/cyclonedx-python-lib). Ensures no vulnerable libraries are present.

### Phase 2: Input Guarding (`@sdk.on_request()`)
**Goal:** Sanitize and filter inputs before they reach the model.

- **`lucid-pii-auditor`** (`lucid-sdk[presidio-analyzer]`): Detects/redacts 70+ PII types using [Microsoft Presidio](https://microsoft.github.io/presidio/). Essential for HIPAA/GDPR compliance.
- **`lucid-injection-auditor`** (`lucid-sdk[llm-guard]`): Uses BERT classifiers (via [LLM Guard](https://github.com/protectai/llm-guard)) to detect prompt injections, jailbreaks, and adversarial patterns.

### Phase 3: Execution Monitoring (`@sdk.on_execution()`)
**Goal:** Monitor agent behavior and resource usage during inference.

- **`lucid-gpu-auditor`** (`lucid-sdk[opentelemetry-api]`): Monitors GPU power draw and memory via [OpenTelemetry](https://opentelemetry.io/). Proves "Green AI" footprints and detects simulation attacks.
- **`lucid-interpretability-auditor`** (`lucid-sdk[goodfire]`): Inspects internal activations using [Goodfire](https://github.com/goodfire-ai/goodfire-sdk) to detect "deception" or hidden concept activations.

### Phase 4: Output Policy (`@sdk.on_response()`)
**Goal:** Validate the quality and safety of generated content, and embed provenance watermarks.

- **`lucid-rag-auditor`** (`lucid-sdk[ragas]`): Calculates Faithfulness and Relevance scores using [Ragas](https://github.com/explodinggradients/ragas). Prevents hallucinations by comparing output to retrieved context.
- **`lucid-fairness-auditor`** (`lucid-sdk[fairlearn]`): Analyzes demographic bias in outputs using [Fairlearn](https://fairlearn.org/). Ensures compliance with algorithmic fairness laws.
- **`lucid-toxicity-auditor`** (`lucid-sdk[detoxify]`): Scores response toxicity (hate speech, threats) using [Detoxify](https://github.com/unitaryai/detoxify) models before delivery.
- **`lucid-text-watermark-auditor`** (`lucid-sdk[transformers]`): Embeds statistical watermarks into LLM token generation using [HuggingFace Transformers WatermarkLogitsProcessor](https://github.com/huggingface/transformers). TEE-attested provenance for AI-generated text.
- **`lucid-image-watermark-auditor`** (`lucid-sdk[c2pa-python]`): Embeds [C2PA Content Credentials](https://opensource.contentauthenticity.org/docs/c2pa-python/) and [TrustMark](https://github.com/adobe/trustmark) invisible watermarks for image provenance.
- **`lucid-video-watermark-auditor`** (`lucid-sdk[c2pa-python,ffmpeg-python]`): Embeds C2PA manifests and frame-level watermarks for video content authenticity.

---

## 🔗 Auditor Chains
Auditors are designed to be composed into chains. Each auditor in a chain evaluates the data and returns a result that determines the next step:

- **Pass (`Proceed`)**: Data is safe; continue to the next auditor or the model.
- **Deny (`Deny`)**: Violation detected; block the request immediately.
- **Modify (`Modify`)**: Data was sanitized (e.g., PII removed); continue with the *modified* data.

---

## 👩‍💻 Developing Auditors

Developing an auditor is as simple as defining a Python function and wrapping it with a phase decorator. The SDK handles the heavy lifting of TEE interaction and evidence signing. Developers are encouraged to use **dependency injection** by bringing in specialized external safety libraries (like `presidio`, `llm-guard`, or `ragas`) to implement powerful logic with minimal overhead.

### Step 1: Initialize the Auditor
Use the `create_auditor` factory to get a builder.
```python
from lucid_sdk import create_auditor
builder = create_auditor(auditor_id="my-custom-auditor")
```

### Step 2: Define Your Logic
Wrap your safety logic with the `@on_request` or `@on_response` decorators.
```python
from lucid_sdk import Proceed, Deny

@builder.on_request
def safety_check(data: dict):
    # Logic to evaluate the request
    if "harmful content" in data.get("prompt", "").lower():
        return Deny("Harmful content detected")
    return Proceed("Safe to proceed")

# Build the auditor instance
auditor = builder.build()
```

### Step 3: Return a Result
Always return one of the structured result types: `Proceed`, `Deny`, or `Modify`. You can also include optional `telemetry` dictionaries for extra visibility.

---

## 🔌 Extended Capabilities (Optional Extras)

The Lucid SDK supports numerous optional packages via "extras". Install them based on your auditor's specialized needs:

```bash
# For a PII Redactor
pip install "lucid-sdk[presidio-analyzer]"

# For a Hallucination Detector
pip install "lucid-sdk[ragas]"

# For comprehensive safety evaluation
pip install "lucid-sdk[inspect-ai,sigstore,llm-guard]"
```

---

## 🚀 Examples

### PII Redactor (Redaction)
```python
import re
from lucid_sdk import create_auditor, Redact, Proceed

builder = create_auditor(auditor_id="pii-redactor")

@builder.on_request
def redact_social_security(data: dict):
    prompt = data.get("prompt", "")
    redacted = re.sub(r"\d{3}-\d{2}-\d{4}", "[SSN_REDACTED]", prompt)
    if redacted != prompt:
        return Redact(modifications={"prompt": redacted}, reason="SSN Redacted")
    return Proceed()

auditor = builder.build()
```

## 🔗 Auditor Composition
You can chain multiple auditors into a single logical pipeline that stops at the first `Deny`.

```python
from lucid_sdk import create_chain

# Create a chain of pre-registered auditors
audit_chain = create_chain(
    chain_id="production-policy",
    auditor_ids=["pii-redactor", "injection-detector", "firewall"]
)

# Run the entire chain
result = audit_chain.check_request(request_data)
# evidence = audit_chain.get_evidence() # Signed evidence bundles for all steps
```

### ⚙️ Unique Configuration
Auditors can receive unit-specific configuration via the `config` argument in handlers. This is injected by the Lucid Operator from your `lucid.yaml`.

```python
@builder.on_request
def pattern_check(data, config):
    # 'config' is automatically loaded from your YAML/Environment
    regex = config.get("custom_pattern", r".*")
    # ... logic ...
```

### 🌊 Dataflow (Context Propagation)
Auditors can pass data to subsequent nodes in the chain. Data returned in the `data` field of a result is nested under the auditor's ID in the `lucid_context`.

```python
# Auditor 1
@builder.on_request
def scanner(data):
    return Proceed(data={"score": 0.95})

# Auditor 2
@builder.on_request
def threshold_check(data, lucid_context):
    prev_score = lucid_context.get("scanner", {}).get("score", 0)
    if prev_score > 0.9:
        return Deny("Score too high")
    return Proceed()
```

## 🏗️ Deployment
Auditors typically run as **sidecars** within a Trusted Execution Environment (TEE). The SDK ensures that every result is signed by the hardware, allowing a remote **Verifier** to prove that the entire Auditor Chain was executed faithfully on genuine hardware.

---

## Version Compatibility

### Package Dependencies

| lucid-sdk | lucid-schemas | Python | Notes |
|-----------|---------------|--------|-------|
| 1.0.x | 1.0.x | >=3.12 | Initial stable release |

### Schema Version Compatibility

The SDK creates evidence using RATS-compliant schemas from `lucid-schemas`. All evidence created by SDK 2.0.x uses `schema_version = "2.0.0"`.

```python
from lucid_schemas import SCHEMA_VERSION_EVIDENCE

# Verify schema compatibility when consuming evidence
def process_evidence(evidence_data: dict):
    version = evidence_data.get("schema_version", "2.0.0")
    if version.split(".")[0] != SCHEMA_VERSION_EVIDENCE.split(".")[0]:
        raise ValueError(f"Incompatible schema version: {version}")
```

See [CHANGELOG.md](./CHANGELOG.md) for migration guides and detailed version history.

---

## 🏭 Auditor Infrastructure Utilities

The SDK provides infrastructure utilities for building production-ready auditor services with standardized configuration, logging, HTTP clients, and resilience patterns.

### BaseAuditorConfig

A dataclass for managing auditor configuration from environment variables:

```python
from dataclasses import dataclass, field
from lucid_sdk import BaseAuditorConfig, get_env_bool, get_env_float

@dataclass
class MyAuditorConfig(BaseAuditorConfig):
    """Configuration for my custom auditor."""
    threshold: float = field(
        default_factory=lambda: get_env_float("MY_THRESHOLD", 0.8)
    )
    block_on_detection: bool = field(
        default_factory=lambda: get_env_bool("MY_BLOCK_ON_DETECTION", True)
    )

# Create config (reads from environment)
config = MyAuditorConfig()
config.auditor_id = "my-custom-auditor"
```

**Built-in fields:** `auditor_id`, `session_id`, `verifier_url`, `model_id`, `http_timeout`, `http_chain_timeout`, `port`

**Environment helpers:** `get_env_bool()`, `get_env_float()`, `get_env_int()`, `get_env_list()`

### create_auditor_app

Factory for creating FastAPI applications with standard endpoints and lifecycle management:

```python
from lucid_sdk import create_auditor_app, run_auditor

config = MyAuditorConfig()
app = create_auditor_app("My Custom Auditor", config)

# Access shared resources
logger = app.state.logger           # Structured JSON logger
http_factory = app.state.http_factory  # Resilient HTTP client

@app.post("/audit")
async def audit(request: Request):
    data = await request.json()
    # Your audit logic here
    return {"decision": "proceed"}

if __name__ == "__main__":
    run_auditor(app, config)
```

**Included endpoints:**
- `GET /health` - Liveness check
- `GET /ready` - Readiness check
- Global exception handler with structured logging

### HTTPClientFactory

Resilient HTTP client with retry logic and circuit breaker support:

```python
http_factory = app.state.http_factory

# POST with automatic retry on 5xx/timeout
response = await http_factory.post_with_retry(
    url="https://api.example.com/analyze",
    json_data={"text": "content to analyze"},
    max_retries=3
)

# Call next auditor in chain
result = await http_factory.chain_call(
    next_auditor_url="http://next-auditor:8090/audit",
    data=request_data,
    lucid_context=context
)

# Submit evidence to verifier
success = await http_factory.submit_evidence(
    auditor_id=config.auditor_id,
    model_id=config.model_id,
    session_id=session_id,
    nonce=nonce,
    decision="proceed",
    metadata={"score": 0.95}
)
```

### Resilience Decorators

Decorators for building fault-tolerant external service calls:

```python
from lucid_sdk import retry_with_backoff, circuit_breaker, resilient

# Retry with exponential backoff
@retry_with_backoff(max_retries=3, base_delay=1.0)
async def call_external_api():
    ...

# Circuit breaker pattern
@circuit_breaker("external_service", failure_threshold=5, recovery_timeout=60)
async def call_flaky_service():
    ...

# Combined: circuit breaker + retry + timeout
@resilient(
    circuit_name="ml_service",
    max_retries=3,
    timeout=10.0,
    failure_threshold=5
)
async def call_ml_service():
    ...
```

**Available utilities:**
- `retry_with_backoff` - Automatic retries with exponential backoff and jitter
- `circuit_breaker` - Prevents cascading failures with automatic recovery
- `with_timeout` - Adds timeout to async functions
- `resilient` - Combined decorator for full resilience pattern
- `get_circuit_status()` - Monitor circuit breaker states
- `reset_circuit(name)` - Manually reset a circuit breaker

---

## Policy Engine (LPL)

The SDK includes a RATS RFC 9334 compliant policy engine for declarative claim validation using the Lucid Policy Language (LPL).

### Loading and Evaluating Policies

```python
from lucid_sdk import PolicyEngine, load_policy
from lucid_schemas import Claim, MeasurementType, AuditDecision

# Load policy from YAML
policy = load_policy("policies/my-policy.yaml")
engine = PolicyEngine(policy)

# Evaluate claims
claims = [
    Claim(name="location.country", type=MeasurementType.conformity, value="IN", ...)
]

result = engine.evaluate(claims)
print(f"Decision: {result.decision}")  # PROCEED, DENY, WARN, REDACT
print(f"Reason: {engine.get_reason()}")
```

### RATS-Compliant Evidence Appraisal

For RFC 9334 compliance, use `appraise_evidence()` to set EAR trust tiers:

```python
from lucid_schemas import Evidence

# Appraise Evidence - sets trust_tier and generates per-claim appraisal
appraised = engine.appraise_evidence(evidence)

print(f"Trust Tier: {appraised.trust_tier}")  # AFFIRMING, WARNING, CONTRAINDICATED

# Per-claim breakdown (EAR-compliant)
for claim in appraised.appraisal_record['claim_appraisals']:
    print(f"  {claim['claim_name']}: {claim['status']}")
    print(f"    Value: {claim['claim_value']} vs Expected: {claim['reference_value']}")
```

### Appraising AttestationResults

```python
from lucid_schemas.attestation import AttestationResult

# Appraise all Evidence in an AttestationResult
result = engine.appraise_attestation_result(attestation_result)

print(f"Authorized: {result.deployment_authorized}")
print(f"Reason: {result.authorization_reason}")
```

### Policy YAML Format

```yaml
policy_id: my-policy-v1
version: "1.0.0"
name: "My Policy"
description: "Policy description"
verification_method: "my-auditor"

required_claims:
  - name: location.country
    type: conformity
    required: true
    min_confidence: 0.8

rules:
  - id: check-location
    description: "Verify location"
    condition: "claims['location.country'].value == 'IN'"
    action: deny
    message: "Location must be India"

enforcement: block  # block | warn | log | audit
```

See [Policy as Code Guide](../../packages/lucid-docs/guides/policy-as-code.md) for complete documentation.

---

## Zero-Knowledge Proof Support

The SDK includes optional support for zero-knowledge proofs, enabling auditors to generate verifiable proofs of their computations without revealing sensitive data.

### Installation

```bash
# Install with ZK extras
pip install lucid-sdk[zk]

# Or from git
pip install "lucid-sdk[zk] @ git+https://github.com/Lucid-Computing/lucid-monorepo.git@main#subdirectory=packages/lucid-sdk"
```

### ZK Module Overview

The `lucid_sdk.zk` module provides:

- **`ZKCircuit`**: Load and use circom circuits for proof generation
- **`ZKProof`**: Represent and serialize ZK proofs
- **`ZKEvidence`**: Helper for creating Evidence with ZK proofs

### Basic Usage

```python
from lucid_sdk.zk import ZKCircuit, ZKMeasurement
from lucid_schemas import MeasurementType

# Load a circuit from files
circuit = ZKCircuit.from_files(
    circuit_id="pii-detector-v1",
    proving_key_path="./circuits/pii_detector.zkey",
    verification_key_path="./circuits/pii_detector_vkey.json",
    wasm_path="./circuits/pii_detector.wasm",
)

# Generate a proof directly
proof = circuit.prove(
    private_inputs={"input_hash": 12345},
    public_inputs={"threshold": 50},
)

# Verify locally
is_valid = circuit.verify(proof)
```

### Creating Evidence with ZK Proofs

```python
from lucid_sdk.zk import ZKCircuit, ZKEvidence
from lucid_schemas import MeasurementType

# Load circuit
circuit = ZKCircuit.from_files(...)

# Create helper for ZK evidence
zk_helper = ZKEvidence(
    name="pii_detection",
    measurement_type=MeasurementType.quantity,
    circuit=circuit,
    auditor_id="pii-auditor@sha256:abc123",
)

# Create evidence with an attached ZK proof
evidence = zk_helper.create_evidence(
    value={"pii_detected": False, "score": 0.0},
    private_inputs={"input_text_hash": hash_value},
    public_inputs={"threshold": 50},
    phase="request",
)

# The evidence now has a zk_proof field that will be verified by the Verifier
```

### Supported Proof Systems

- **Groth16** - Fast verification, requires trusted setup
- **PLONK** - Universal setup, larger proofs
- **fflonk** - Variant of PLONK with smaller proofs

### Registering Circuits with the Verifier

Before proofs can be verified, the circuit's verification key must be registered:

```bash
# Register via API
curl -X POST https://verifier.example.com/v1/zk/circuits \
  -H "Content-Type: application/json" \
  -d '{
    "circuit_id": "pii-detector-v1",
    "circuit_name": "PII Detection Circuit",
    "version": "1.0.0",
    "proof_system": "groth16",
    "verification_key": "<base64-encoded-vkey>",
    "num_public_inputs": 3
  }'
```

Or programmatically:

```python
import httpx
from lucid_sdk.zk import ZKCircuit

circuit = ZKCircuit.from_files(...)
metadata = circuit.to_metadata()

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://verifier.example.com/v1/zk/circuits",
        json={
            "circuit_id": metadata.circuit_id,
            "circuit_name": metadata.circuit_name,
            "version": metadata.version,
            "proof_system": metadata.proof_system.value,
            "verification_key": metadata.verification_key,
            "num_public_inputs": metadata.num_public_inputs,
        }
    )
```

### Error Handling

```python
from lucid_sdk.zk import (
    ZKError,
    ZKNotAvailableError,
    ZKCircuitError,
    ZKProvingError,
    ZKVerificationError,
)

try:
    proof = circuit.prove(inputs)
except ZKNotAvailableError:
    # snarkjs not installed
    pass
except ZKCircuitError as e:
    # Problem with circuit files
    print(f"Circuit error: {e.circuit_id} - {e.file_path}")
except ZKProvingError as e:
    # Proof generation failed
    print(f"Proving error: {e.circuit_id} - {e.input_name}")
```
