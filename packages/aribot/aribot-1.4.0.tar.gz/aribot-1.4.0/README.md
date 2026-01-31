# Aribot Python SDK

Official Python SDK for the Aribot Security Platform by Aristiun & Ayurak.

[![PyPI](https://img.shields.io/pypi/v/aribot)](https://pypi.org/project/aribot/)
[![Python](https://img.shields.io/pypi/pyversions/aribot)](https://pypi.org/project/aribot/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Installation

```bash
pip install aribot
```

## Quick Start

```python
from aribot import Aribot

client = Aribot(api_key="your_api_key")

# Analyze architecture diagram for threats
result = client.threat_modeling.analyze_diagram("architecture.png")
print(f"Found {result['threat_count']} threats")

# Get detailed threats
threats = client.threat_modeling.get_threats(result['diagram_id'])
for threat in threats:
    print(f"[{threat['severity']}] {threat['title']}")

# Digital Twin - List cloud providers
providers = client.digital_twin.get_providers()
for p in providers:
    print(f"Provider: {p['name']} - {p['display_name']}")

# Economics - Get dashboard
dashboard = client.economics.get_dashboard()
print(f"Total Monthly Cost: ${dashboard['company_summary']['total_monthly']}")

# Red Team - Get methodologies
methodologies = client.redteam.get_methodologies()
for m in methodologies:
    print(f"Methodology: {m['name']}")
```

## Features

- **Threat Modeling** - Upload diagrams, detect components, identify threats
- **Compliance Scanning** - ISO 27001, SOC2, GDPR, HIPAA, PCI-DSS, NIST
- **Cloud Security** - Scan AWS, Azure, GCP for misconfigurations
- **Pipeline Security** - SAST, SCA, secrets detection in CI/CD
- **Digital Twin** - Cloud provider integration, resource discovery, health monitoring
- **Economics** - Cost analysis, ROI calculations, market intelligence
- **Red Team** - Attack simulations, methodologies, threat intelligence

## API Reference

### Threat Modeling

```python
# Upload and analyze a diagram
result = client.threat_modeling.analyze_diagram(
    "architecture.png",
    analysis_depth="comprehensive",  # basic, comprehensive, detailed
    wait=True,                       # wait for analysis to complete
    timeout=300                      # max wait time in seconds
)

# List diagrams
diagrams = client.threat_modeling.list(page=1, limit=25)

# Get diagram details
diagram = client.threat_modeling.get(diagram_id)

# Get threats for a diagram
threats = client.threat_modeling.get_threats(diagram_id)

# Get detected components
components = client.threat_modeling.get_components(diagram_id)

# Run AI-powered analysis
ai_result = client.threat_modeling.analyze_with_ai(
    diagram_id,
    analysis_types=["attack_paths", "data_flow"]
)

# Delete a diagram
client.threat_modeling.delete(diagram_id)

# Get dashboard metrics
dashboard = client.threat_modeling.dashboard(period="month")
```

### Compliance Scanning

```python
# Run compliance scan
result = client.compliance.scan(
    diagram_id,
    standards=["ISO27001", "SOC2", "GDPR"],
    include_recommendations=True
)
print(f"Compliance score: {result['overall_score']}%")

# Get compliance report
report = client.compliance.get_report(diagram_id, format="json")

# List available standards
standards = client.compliance.list_standards()

# Get standard details
iso = client.compliance.get_standard("ISO27001")

# List controls for a standard
controls = client.compliance.list_controls("SOC2", category="access_control")

# Get compliance gaps
gaps = client.compliance.get_gaps(diagram_id, standard_id="ISO27001")

# Create custom standard
custom = client.compliance.add_custom_standard(
    name="Internal Security Policy",
    description="Company security requirements",
    controls=[
        {
            "id": "ISP-001",
            "name": "Data Encryption",
            "description": "All data must be encrypted at rest",
            "severity": "high"
        }
    ]
)

# Get compliance dashboard
dashboard = client.compliance.dashboard(period="quarter")
```

### Cloud Security

```python
# Run cloud security scan
scan = client.cloud.scan(
    project_id="123456789012",
    provider="aws",
    services=["iam", "s3", "ec2"],
    compliance_standards=["CIS-AWS"]
)

# Get scan results
scan = client.cloud.get_scan(scan_id)

# List scans
scans = client.cloud.list_scans(provider="aws", status="completed")

# Get findings
findings = client.cloud.get_findings(
    scan_id,
    severity="critical",
    service="s3"
)

# Connect AWS account
account = client.cloud.connect_account(
    provider="aws",
    credentials={
        "role_arn": "arn:aws:iam::123456789012:role/AribotSecurityRole",
        "external_id": "your-external-id"
    },
    name="Production AWS"
)

# Connect GCP project
account = client.cloud.connect_account(
    provider="gcp",
    credentials={
        "service_account_key": "{ ... }",
        "project_id": "my-project-123"
    }
)

# Connect Azure subscription
account = client.cloud.connect_account(
    provider="azure",
    credentials={
        "tenant_id": "...",
        "client_id": "...",
        "client_secret": "..."
    }
)

# List connected accounts
accounts = client.cloud.list_accounts(provider="aws")

# Get remediation steps
remediation = client.cloud.get_remediation(finding_id)

# Resolve a finding
client.cloud.resolve_finding(
    finding_id,
    resolution="fixed",
    notes="Patched in deployment v1.2.3"
)

# Suppress a finding
client.cloud.suppress_finding(
    finding_id,
    reason="Accepted risk per security review",
    duration_days=90
)

# Get cloud security dashboard
dashboard = client.cloud.dashboard(project_id="123456789012")
```

### Pipeline Security

```python
# Create a project
project = client.pipeline.create_project(
    name="my-api",
    repository_url="https://github.com/org/my-api",
    scan_types=["sast", "sca", "secrets"]
)

# Run security scan
result = client.pipeline.scan(
    project_id,
    commit_sha="abc123def456",
    branch="main",
    scan_types=["sast", "sca", "secrets"],
    fail_on_severity="high",
    wait=True
)

if result['status'] == 'failed':
    print("Security gate failed!")
    for finding in result['blocking_findings']:
        print(f"  [{finding['severity']}] {finding['title']}")

# Get scan details
scan = client.pipeline.get_scan(scan_id)

# Get specific finding types
sast_findings = client.pipeline.get_sast_findings(scan_id)
sca_findings = client.pipeline.get_sca_findings(scan_id)
secrets = client.pipeline.get_secrets_findings(scan_id)

# Configure security gates
client.pipeline.configure_gates(
    project_id,
    gates={
        "fail_on_critical": True,
        "fail_on_high": True,
        "max_high_findings": 5,
        "block_secrets": True,
        "required_scan_types": ["sast", "secrets"]
    }
)

# Set baseline (suppress existing findings)
client.pipeline.add_baseline(project_id, scan_id)

# Suppress a finding
client.pipeline.suppress_finding(
    finding_id,
    reason="False positive - validated manually"
)

# Get pipeline dashboard
dashboard = client.pipeline.dashboard(project_id=project_id)
```

### Digital Twin

```python
# Get cloud providers
providers = client.digital_twin.get_providers()
# Returns: [{'id': '...', 'name': 'aws', 'display_name': 'Amazon Web Services', 'connected': False}, ...]

# Get provider health
health = client.digital_twin.get_health()
# Returns: {'status': 'ok', 'configured': True, 'infrastructure': {...}, 'capabilities': [...]}

# Get analytics
analytics = client.digital_twin.get_analytics()
# Returns: {'configured': True, 'graph_statistics': {...}, 'entities_by_type': {...}}

# Get resources
resources = client.digital_twin.get_resources(limit=50)
# Returns: [{'id': '...', 'name': 'my-bucket', 'provider': 'aws', 'resource_type': 's3'}, ...]

# Sync resources from provider
result = client.digital_twin.sync_resources(provider_id='aws-123')
# Returns: {'status': 'syncing', 'resources_found': 150}

# Discover new resources
discovery = client.digital_twin.discover_resources(provider_id='aws-123')
# Returns: {'status': 'discovered', 'new_resources': 25}
```

### Economics

```python
# Get economics dashboard
dashboard = client.economics.get_dashboard(period='month')
# Returns: {'success': True, 'company_summary': {'total_monthly': 5000, 'total_annual': 60000}, ...}

# Get diagram cost analysis
cost = client.economics.get_diagram_cost_analysis(diagram_id)
# Returns: {'monthly_cost': 1500, 'annual_cost': 18000, 'cost_breakdown': [...]}

# Get component cost
component_cost = client.economics.get_component_cost(component_id)
# Returns: {'component': 'EC2 Instance', 'monthly_cost': 200, 'recommendations': [...]}

# Get economic intelligence
intel = client.economics.get_economic_intelligence()
# Returns: {'status': 'success', 'provider': 'aws', 'pricing': {...}}

# Get market intelligence
market = client.economics.get_market_intelligence()
# Returns: {'trends': [...], 'benchmarks': {...}, 'recommendations': [...]}

# Calculate ROI
roi = client.economics.calculate_roi(
    investment=100000,
    risks_addressed=['risk-1', 'risk-2'],
    timeframe_days=365
)
# Returns: {'roi_percentage': 250, 'npv': 150000, 'payback_months': 8}
```

### Red Team

```python
# Get threat modeling methodologies
methodologies = client.redteam.get_methodologies()
# Returns: [{'id': 'stride', 'name': 'STRIDE', 'description': '...'}, ...]

# Get simulations
simulations = client.redteam.get_simulations(limit=10)
# Returns: [{'id': '...', 'name': 'APT29 Simulation', 'status': 'completed'}, ...]

# Get threat intelligence
intel = client.redteam.get_intelligence()
# Returns: {'threats': [...], 'indicators': [...], 'campaigns': [...]}

# Generate attack paths for a diagram
paths = client.redteam.generate_attack_paths(
    diagram_id,
    scope='single',
    include_compliance=True
)
# Returns: {'status': 'success', 'paths': [{'title': '...', 'risk_score': 85, 'steps': [...]}]}

# Get security requirements
requirements = client.redteam.get_security_requirements(diagram_id)
# Returns: [{'id': '...', 'requirement': '...', 'priority': 'high'}, ...]
```

## Error Handling

```python
from aribot import (
    Aribot,
    AribotError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError
)

client = Aribot(api_key="your_api_key")

try:
    result = client.threat_modeling.analyze_diagram("diagram.png")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Invalid request: {e.errors}")
except NotFoundError:
    print("Resource not found")
except ServerError:
    print("Server error - try again later")
except AribotError as e:
    print(f"API error: {e.message}")
```

## Configuration

```python
# Custom base URL (for on-premise deployments)
client = Aribot(
    api_key="your_api_key",
    base_url="https://aribot.internal.company.com/api",
    timeout=60
)

# Check API health
health = client.health()

# Get current user info
user = client.me()

# Get usage stats
usage = client.usage(period="month")
print(f"API calls used: {usage['calls_used']}/{usage['calls_limit']}")
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Security Scan
  env:
    AYURAK_API_KEY: ${{ secrets.AYURAK_API_KEY }}
  run: |
    pip install aribot
    python -c "
    from aribot import Aribot
    client = Aribot(api_key='$AYURAK_API_KEY')
    result = client.pipeline.scan(
        project_id='${{ vars.PROJECT_ID }}',
        commit_sha='${{ github.sha }}',
        fail_on_severity='high',
        wait=True
    )
    if result['status'] == 'failed':
        exit(1)
    "
```

### GitLab CI

```yaml
security_scan:
  script:
    - pip install aribot
    - python scripts/security_scan.py
  variables:
    AYURAK_API_KEY: $AYURAK_API_KEY
```

## Support

- Documentation: https://developers.aribot.com/docs/python-sdk
- API Reference: https://developers.aribot.com/api
- Issues: https://github.com/AribotAI/aribot-python/issues

## Changelog

### v1.4.0
- Updated base URL to `api.aribot.ayurak.com`
- Added AI module (`client.ai`) - usage, quota, models, configure, analyze, queue status
- Added SBOM module (`client.sbom`) - document management and vulnerability scanning
- Added Dashboard module (`client.dashboard`) - overview, recent activity, risk summary
- Added FinOps module (`client.finops`) - cost optimization recommendations and tracking
- Added Marketplace module (`client.marketplace`) - templates, categories, featured content
- Added API Keys module (`client.api_keys`) - key listing and revocation

### v1.1.0
- Added Digital Twin, Economics, and Red Team modules
- Added Remediation module

### v1.0.0
- Initial release with Threat Modeling, Compliance, Cloud Security, and Pipeline modules

## License

MIT
