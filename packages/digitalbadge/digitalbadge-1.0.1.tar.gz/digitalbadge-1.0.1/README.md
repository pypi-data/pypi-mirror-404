<p align="center">
  <img src="https://issuebadge.com/icons/android-chrome-192x192.png" alt="Issue Badge Logo" width="120">
</p>

# Digital Badge - Python Certificate Generator SDK

[![PyPI version](https://badge.fury.io/py/digitalbadge.svg)](https://badge.fury.io/py/digitalbadge)
[![Python Versions](https://img.shields.io/pypi/pyversions/digitalbadge.svg)](https://pypi.org/project/digitalbadge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Official Python SDK for digital badge and certificate generation.** Create, issue, and manage digital certificates and badges programmatically with the Issue Badge API.

## Features

- **Certificate Generator** - Create professional digital certificates programmatically
- **Bulk Certificate Generation** - Issue certificates to multiple recipients at scale
- **Badge Creator** - Design and issue digital badges for achievements
- **Custom Fields** - Add custom metadata like scores, dates, employee IDs
- **Image Upload** - Attach photos or images to certificates (Base64)
- **Expiration Management** - Set expiration dates for time-limited credentials
- **Idempotent Operations** - Safe retry logic with idempotency keys
- **Type Hints** - Full type annotation support for better IDE integration

## Installation

```bash
pip install digitalbadge
```

## Quick Start

```python
from issuebadge import IssueBadge

# Initialize the client
client = IssueBadge('YOUR_API_TOKEN')

# Issue a certificate
result = client.issue_badge({
    'badge_id': 'your_badge_template_id',
    'name': 'John Doe',
    'email': 'john@example.com',
    'idempotency_key': 'unique_key_12345'
})

print(f"Certificate URL: {result['publicUrl']}")
```

## Use Cases

- **Training Certificates** - Automatically issue completion certificates for online courses
- **Employee Recognition** - Generate achievement badges for HR programs
- **Event Certificates** - Bulk generate attendance certificates for webinars and conferences
- **Academic Credentials** - Issue digital diplomas and course completion certificates
- **Professional Certifications** - Create verifiable professional credentials
- **Competition Awards** - Generate winner certificates and participation badges

## API Reference

### Initialize Client

```python
from issuebadge import IssueBadge

# Basic initialization
client = IssueBadge('YOUR_API_TOKEN')

# With custom settings
client = IssueBadge(
    api_token='YOUR_API_TOKEN',
    api_url='https://app.issuebadge.com',  # Optional: custom API URL
    timeout=60  # Optional: request timeout in seconds
)
```

### Validate API Key

```python
result = client.validate_key()
print(f"Valid: {result.get('valid')}")
```

### Create Badge Template

```python
result = client.create_badge({
    'name': 'Python Developer Certification',
    'description': 'Certified Python Developer badge'
})
badge_id = result['badge_id']
```

### Get All Badge Templates

```python
badges = client.get_all_badges()
for badge in badges.get('data', []):
    print(f"{badge['name']}: {badge['badge_id']}")
```

### Issue Certificate

```python
# Basic certificate
result = client.issue_badge({
    'badge_id': 'abc123',
    'name': 'John Doe',
    'email': 'john@example.com',
    'idempotency_key': 'unique_key_12345'
})
print(f"Certificate: {result['publicUrl']}")
```

### Issue Certificate with Expiration

```python
from datetime import datetime, timedelta

# Certificate valid for 2 years
expire_date = (datetime.now() + timedelta(days=730)).strftime('%Y-%m-%d')

result = client.issue_badge({
    'badge_id': 'abc123',
    'name': 'Jane Smith',
    'email': 'jane@example.com',
    'expire_date': expire_date,
    'idempotency_key': 'cert_jane_2024'
})
```

### Issue Certificate with Custom Fields

```python
result = client.issue_badge({
    'badge_id': 'abc123',
    'name': 'Bob Wilson',
    'email': 'bob@example.com',
    'idempotency_key': 'cert_bob_001',
    'metadata': {
        'course_name': 'Advanced Python Programming',
        'score': 95,
        'completion_date': '2024-11-15',
        'instructor': 'Dr. Smith',
        'certificate_number': 'CERT-2024-001'
    }
})
```

### Issue Certificate with Photo

```python
import base64

# Read and encode image
with open('recipient_photo.jpg', 'rb') as image_file:
    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    photo_base64 = f'data:image/jpeg;base64,{image_data}'

result = client.issue_badge({
    'badge_id': 'abc123',
    'name': 'Alice Johnson',
    'email': 'alice@example.com',
    'idempotency_key': 'cert_alice_photo',
    'metadata': {
        'certificate_photo': photo_base64
    }
})
```

### Bulk Certificate Generation

```python
# Issue certificates to multiple recipients
recipients = [
    {'name': 'John Doe', 'email': 'john@example.com', 'idempotency_key': 'bulk_1'},
    {'name': 'Jane Smith', 'email': 'jane@example.com', 'idempotency_key': 'bulk_2'},
    {'name': 'Bob Wilson', 'email': 'bob@example.com', 'idempotency_key': 'bulk_3'},
]

results = client.issue_badges_bulk('your_badge_id', recipients)

for result in results:
    if result['success']:
        print(f"Issued: {result['publicUrl']}")
    else:
        print(f"Failed: {result['error']}")
```

### Webhook-Style Issuance (GET)

```python
# Issue via GET request (useful for webhooks)
result = client.issue_badge_get({
    'badge_id': 'abc123',
    'name': 'John Doe',
    'email': 'john@example.com',
    'idempotency_key': 'webhook_123'
})
```

## Error Handling

```python
try:
    result = client.issue_badge({
        'badge_id': 'abc123',
        'name': 'John Doe',
        'email': 'john@example.com'
    })
    print(f"Success: {result['publicUrl']}")
except Exception as e:
    print(f"Error: {str(e)}")
```

## Requirements

- Python 3.6 or higher
- `requests` library (installed automatically)

## Links

- **Homepage**: [https://issuebadge.com](https://issuebadge.com)
- **Documentation**: [https://issuebadge.com/h/developer](https://issuebadge.com/h/developer)
- **Dashboard**: [https://app.issuebadge.com](https://app.issuebadge.com)

## Support

- Email: support@issuebadge.com
- Documentation: [https://issuebadge.com/h/developer](https://issuebadge.com/h/developer)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Keywords

certificate generator, bulk certificate generator, digital badge, digital certificate, badge generator, certificate maker, certificate creator, credential management, certificate automation, online certificate, e-certificate, training certificate, course certificate, verifiable credentials, open badge, badge API, certificate API
