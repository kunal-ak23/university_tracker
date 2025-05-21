# Leads Module Documentation

## Overview
The Leads module is designed to manage and track potential students (leads) in the university tracking system. It provides a complete API for creating, reading, updating, and deleting lead information, with support for filtering, searching, and ordering.

## Models

### Lead
```python
class Lead(models.Model):
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True)
    agent = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_leads')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## API Endpoints

### List/Create Leads
- **URL**: `/api/leads/`
- **Method**: GET, POST
- **Authentication**: Required (JWT Token)
- **Permissions**: 
  - Superusers can see all leads
  - Agents can only see their own leads

#### Query Parameters
- `status`: Filter by lead status
- `agent`: Filter by agent ID
- `assigned_to`: Filter by assigned user ID
- `search`: Search in name, mobile, email, address, notes
- `ordering`: Order by name, status, created_at, updated_at

#### Example Request Body (POST)
```json
{
    "name": "John Doe",
    "mobile": "+1234567890",
    "email": "john@example.com",
    "address": "123 Main St",
    "status": "new",
    "notes": "Interested in Data Science program",
    "assigned_to": 1
}
```

### Get/Update/Delete Single Lead
- **URL**: `/api/leads/{id}/`
- **Method**: GET, PUT, PATCH, DELETE
- **Authentication**: Required (JWT Token)
- **Permissions**: Same as List/Create

## Features

### Filtering
- Filter leads by status
- Filter by agent
- Filter by assigned user

### Search
- Search in name
- Search in mobile
- Search in email
- Search in address
- Search in notes

### Ordering
- Order by name
- Order by status
- Order by created_at
- Order by updated_at
- Default ordering: -created_at (newest first)

### Automatic Features
- Automatic assignment of agent on lead creation
- Automatic timestamp management (created_at, updated_at)

## Admin Interface
The leads module is integrated with Django's admin interface with the following features:
- List display: name, mobile, email, status, agent, assigned_to, created_at
- List filters: status, agent, assigned_to, created_at
- Search fields: name, mobile, email, address, notes
- Default ordering: -created_at

## Security
- JWT Authentication required for all endpoints
- Role-based access control:
  - Superusers can access all leads
  - Agents can only access their own leads
- Input validation through serializers
- Proper permission checks on all operations

## Usage Examples

### Creating a New Lead
```python
# Using requests library
import requests

headers = {
    'Authorization': 'Bearer your_jwt_token',
    'Content-Type': 'application/json'
}

data = {
    "name": "John Doe",
    "mobile": "+1234567890",
    "email": "john@example.com",
    "address": "123 Main St",
    "status": "new",
    "notes": "Interested in Data Science program"
}

response = requests.post('http://your-domain/api/leads/', headers=headers, json=data)
```

### Filtering Leads
```python
# Get all leads with status 'new'
response = requests.get('http://your-domain/api/leads/?status=new', headers=headers)

# Search for leads with 'john' in name or email
response = requests.get('http://your-domain/api/leads/?search=john', headers=headers)

# Get leads ordered by creation date
response = requests.get('http://your-domain/api/leads/?ordering=-created_at', headers=headers)
```

## Error Handling
The API returns appropriate HTTP status codes and error messages:
- 400: Bad Request (invalid data)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (lead not found)
- 500: Internal Server Error

## Dependencies
- Django
- Django REST Framework
- django-filter
- JWT Authentication 