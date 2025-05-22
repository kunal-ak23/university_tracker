# Leads Module Documentation

## Overview
The Leads module provides functionality for managing leads in the system. It includes features for creating, viewing, updating, and deleting leads, with role-based access control and filtering capabilities.

## Model Structure
The Lead model includes the following fields:
- `name`: Lead's name
- `mobile`: Contact number
- `email`: Email address
- `address`: Physical address
- `status`: Current status of the lead
- `notes`: Additional information
- `agent`: The agent assigned to the lead
- `assigned_to`: The user assigned to handle the lead
- `created_by`: The user who created the lead
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update

## Role-Based Access Control
The leads module implements role-based access control with the following permissions:

### Admin Users
- Can view all leads
- Can create, update, and delete any lead
- Full access to all lead operations

### Agent Users
- Can only view their own leads (leads where they are the agent)
- Can create new leads (automatically assigned to them)
- Can update and delete their own leads
- Cannot access leads created by other agents

### POC Users
- No access to leads
- Cannot view, create, update, or delete leads

## Authentication
All endpoints require JWT (JSON Web Token) authentication. Here's how to authenticate:

### Getting a Token
```python
import requests

# Login to get the token
login_data = {
    "username": "your_username",
    "password": "your_password"
}

# Replace with your actual domain
login_url = "http://your-domain/api/token/"

# Get the token
response = requests.post(login_url, json=login_data)
tokens = response.json()

# Extract the access token
access_token = tokens['access']
```

### Using the Token
Include the token in the Authorization header of all requests:
```python
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
```

Note: The access token expires after 60 minutes. You'll need to either:
1. Get a new token by logging in again
2. Use the refresh token to get a new access token

## API Endpoints

### 1. List/Create Leads
- **URL**: `/api/leads/`
- **Method**: GET, POST
- **Authentication**: Required (JWT Token)
- **Permissions**: 
  - Admin users can see all leads
  - Agents can only see their assigned leads
  - POC users cannot access leads

#### Query Parameters
- `status`: Filter by lead status
- `agent`: Filter by agent ID
- `assigned_to`: Filter by assigned user ID
- `created_by`: Filter by creator ID
- `search`: Search in name, mobile, email, address, notes
- `ordering`: Sort by any field (prefix with '-' for descending)

#### Example Response
```json
{
    "count": 1,
    "results": [
        {
            "id": 1,
            "name": "John Doe",
            "mobile": "1234567890",
            "email": "john@example.com",
            "address": "123 Main St",
            "status": "new",
            "notes": "Interested in Python course",
            "agent": 1,
            "agent_details": {
                "id": 1,
                "name": "Agent Name",
                "email": "agent@example.com"
            },
            "assigned_to": 2,
            "assigned_to_details": {
                "id": 2,
                "name": "Assigned User",
                "email": "assigned@example.com"
            },
            "created_by": 1,
            "created_by_details": {
                "id": 1,
                "name": "Creator Name",
                "email": "creator@example.com"
            },
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    ]
}
```

### 2. Get/Update/Delete Single Lead
- **URL**: `/api/leads/{id}/`
- **Method**: GET, PUT, PATCH, DELETE
- **Authentication**: Required (JWT Token)
- **Permissions**: Same as List/Create endpoint

## Features
1. Role-based access control
2. Automatic assignment of created_by field
3. Full search and filtering capabilities
4. Status tracking
5. Detailed notes and information
6. Pagination support

## Security Considerations
1. All endpoints require authentication
2. Role-based permissions are enforced
3. Agents can only access their assigned leads
4. Admin users have full access to all leads

## Usage Examples

### Creating a New Lead
```python
import requests

headers = {
    'Authorization': 'Bearer your_jwt_token',
    'Content-Type': 'application/json'
}

data = {
    'name': 'John Doe',
    'mobile': '1234567890',
    'email': 'john@example.com',
    'address': '123 Main St',
    'status': 'new',
    'notes': 'Interested in Python course'
}

response = requests.post('http://your-domain/api/leads/', json=data, headers=headers)
```

### Searching Leads
```python
# Search by status
response = requests.get('http://your-domain/api/leads/?status=new', headers=headers)

# Search by creator
response = requests.get('http://your-domain/api/leads/?created_by=1', headers=headers)

# Search by text
response = requests.get('http://your-domain/api/leads/?search=python', headers=headers)
```

## Error Handling
The API returns appropriate HTTP status codes and error messages:
- 400: Bad Request (invalid data)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (lead doesn't exist)
- 500: Internal Server Error

## Dependencies
- Django
- Django REST Framework
- django-filter
- JWT Authentication 