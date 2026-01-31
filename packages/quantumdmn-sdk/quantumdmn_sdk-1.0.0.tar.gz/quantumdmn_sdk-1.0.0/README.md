# QuantumDMN Python SDK

Python client library for the QuantumDMN decision engine API.

## Installation

```bash
pip install quantumdmn
```

Or install from source:

```bash
pip install -e .
```

## Quick Start

```python
from quantumdmn import DmnEngine, ZitadelTokenProvider, ApiClient, Configuration

# Authentication with Zitadel
auth = ZitadelTokenProvider(
    key_file_path="path/to/key.json",
    issuer_url="https://auth.quantumdmn.com",
    project_id="your-zitadel-project-id"
)

# Create API client
config = Configuration(host="https://api.quantumdmn.com")
client = ApiClient(config)
client.set_default_header("Authorization", f"Bearer {auth.get_token()}")

# Create DMN engine
engine = DmnEngine(client, project_id="your-dmn-project-id")

# Evaluate a decision
result = engine.evaluate(
    definition_id="your-definition-id",
    context={"input1": 100, "input2": "value"}
)

# Result is Dict[str, EvaluationResult]
for key, eval_result in result.items():
    value = eval_result.value.to_raw()  # Unwrap to Python type
    print(f"{key}: {value}")
```

## Authentication

### Zitadel JWT Profile Authentication

The SDK includes a `ZitadelTokenProvider` helper for authenticating using Zitadel service accounts:

```python
from quantumdmn import ZitadelTokenProvider

# Create token provider
auth = ZitadelTokenProvider(
    key_file_path="service-account-key.json",
    issuer_url="https://your-zitadel-instance.com",
    project_id="your-zitadel-project-id"
)

# Get access token (cached automatically)
token = auth.get_token()
```

The token provider automatically:
- Creates JWT assertions signed with your service account key
- Exchanges them for access tokens
- Caches tokens until they expire
- Includes required Zitadel scopes (`urn:zitadel:iam:user:resourceowner`, `urn:zitadel:iam:org:projects:roles`)

### SSL Certificate Verification

For local development with self-signed certificates:

```python
auth = ZitadelTokenProvider(
    key_file_path="key.json",
    issuer_url="https://auth.local",
    project_id="project-id",
    ssl_ca_cert="/path/to/ca-bundle.crt"  # Optional CA bundle
)

config = Configuration(host="https://api.local")
config.ssl_ca_cert = "/path/to/ca-bundle.crt"
```

## Using the DMN Engine

The `DmnEngine` class provides a simplified interface for DMN evaluation:

```python
from quantumdmn import DmnEngine, ApiClient, Configuration

# Setup
config = Configuration(host="https://api.quantumdmn.com")
client = ApiClient(config)
client.set_default_header("Authorization", f"Bearer {token}")

engine = DmnEngine(client, project_id="your-project-id")

# Evaluate by definition ID (UUID or XML ID)
result = engine.evaluate(
    definition_id="_myDecisionId",  # or UUID
    context={"age": 25, "income": 50000},
    version=None  # Optional: specify version number
)

# Result is Dict[str, EvaluationResult]
for key, eval_result in result.items():
    print(f"{key}:")
    print(f"  Value: {eval_result.value.to_raw()}")
    print(f"  Type: {eval_result.type}")
    print(f"  Decision ID: {eval_result.decision_id}")
```

### Context Conversion

The engine automatically converts Python types to FEEL values:

```python
context = {
    "string_val": "hello",
    "number_val": 42,
    "boolean_val": True,
    "list_val": [1, 2, 3],
    "dict_val": {"nested": "value"},
    "none_val": None
}

result = engine.evaluate("decision-id", context)
```

## Working with FeelValue

For advanced use cases, you can work directly with `FeelValue` objects:

```python
from quantumdmn import FeelValue

# Create FEEL values explicitly
num = FeelValue.of_number(42)
text = FeelValue.of_string("hello")
flag = FeelValue.of_boolean(True)
items = FeelValue.of_list([
    FeelValue.of_number(1),
    FeelValue.of_number(2)
])
ctx = FeelValue.of_context({
    "name": FeelValue.of_string("John"),
    "age": FeelValue.of_number(30)
})

# Auto-convert from Python
feel_val = FeelValue.from_python({"key": "value"})

# Convert to raw Python types
raw = feel_val.to_raw()  # Returns dict, list, str, int, bool, etc.

# Serialize for API
json_data = feel_val.to_dict()
```

## Direct API Access

For more control, use the generated API client directly:

```python
from quantumdmn import DefaultApi, ApiClient, Configuration
from quantumdmn.models import EvaluateStoredRequest

config = Configuration(host="https://api.quantumdmn.com")
client = ApiClient(config)
client.set_default_header("Authorization", f"Bearer {token}")

api = DefaultApi(client)

# Evaluate with full control
request = EvaluateStoredRequest(
    context={"input": 100},
    version=1
)

response = api.evaluate_stored(
    project_id="project-uuid",
    definition_id="definition-uuid",
    evaluate_stored_request=request
)

# Response is Dict[str, EvaluationResult]
for key, evaluation in response.items():
    print(f"{key}: {evaluation.value.to_raw()}")
```

## Error Handling

```python
from quantumdmn.exceptions import ApiException

try:
    result = engine.evaluate("definition-id", context)
except ApiException as e:
    print(f"API Error: {e.status} - {e.reason}")
    print(f"Response: {e.body}")
```

## Configuration Options

```python
from quantumdmn import Configuration

config = Configuration(
    host="https://api.quantumdmn.com",
    ssl_ca_cert="/path/to/ca.crt",  # SSL certificate verification
    verify_ssl=True,                 # Enable/disable SSL verification
    proxy="http://proxy:8080",       # HTTP proxy
    debug=False                       # Enable debug logging
)
```

## Complete Example

```python
import os
from quantumdmn import (
    DmnEngine,
    ZitadelTokenProvider,
    ApiClient,
    Configuration
)
from quantumdmn.exceptions import ApiException

def main():
    # Authentication
    auth = ZitadelTokenProvider(
        key_file_path=os.getenv("DMN_KEY_FILE"),
        issuer_url=os.getenv("DMN_AUTH_URL"),
        project_id=os.getenv("ZITADEL_PROJECT_ID")
    )
    
    # Setup client
    config = Configuration(host=os.getenv("DMN_API_URL"))
    client = ApiClient(config)
    
    # Get token and set authorization
    token = auth.get_token()
    client.set_default_header("Authorization", f"Bearer {token}")
    
    # Create engine
    engine = DmnEngine(client, project_id=os.getenv("DMN_PROJECT_ID"))
    
    # Evaluate
    try:
        result = engine.evaluate(
            definition_id=os.getenv("DMN_DEFINITION_ID"),
            context={
                "amount": 1000,
                "customer_type": "premium",
                "risk_score": 0.25
            }
        )
        
        print("Decision result:")
        for key, eval_result in result.items():
            value = eval_result.value.to_raw()
            print(f"  {key}: {value}")
            
    except ApiException as e:
        print(f"Evaluation failed: {e.status} {e.reason}")
        if e.body:
            print(f"Details: {e.body}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
```
