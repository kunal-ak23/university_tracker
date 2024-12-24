# API Documentation

## Table of Contents
- [Authentication](#authentication)
- [Users](#users)
- [OEMs](#oems)
- [Programs](#programs)
- [Universities](#universities)
- [Streams](#streams)
- [Contracts](#contracts)
- [Batches](#batches)
- [Billing](#billing)
- [Payments](#payments)
- [Tax Rates](#tax-rates)

## Base URL
All endpoints are relative to: `http://your-domain.com/api/v1/`

## Authentication

All endpoints except authentication endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

### Login
```http
POST /auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "your_password"
}
```

Response:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "role": "university_poc",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

### Register
```http
POST /auth/register/
Content-Type: application/json

{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "secure_password",
    "password2": "secure_password",
    "role": "university_poc",
    "phone_number": "+1234567890",
    "address": "123 Main St",
    "date_of_birth": "1990-01-01"
}
```

Response:
```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "university_poc"
}
```

### Refresh Token
```http
POST /auth/refresh/
Content-Type: application/json

{
    "refresh": "your_refresh_token"
}
```

Response:
```json
{
    "access": "new_access_token"
}
```

## Users

### List Users
```http
GET /users/
```

Query Parameters:
- `role`: Filter by role (university_poc, provider_poc, superuser)
- `roles`: Filter by multiple roles (comma-separated)
- `page`: Page number
- `page_size`: Number of items per page

Response:
```json
{
    "count": 100,
    "next": "http://api/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "johndoe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "full_name": "John Doe",
            "role": "university_poc",
            "phone_number": "+1234567890",
            "profile_picture": "http://...",
            "address": "123 Main St",
            "date_of_birth": "1990-01-01",
            "is_active": true,
            "is_staff": false,
            "is_superuser": false,
            "last_login": "2024-01-01T12:00:00Z",
            "date_joined": "2023-01-01T12:00:00Z",
            "oem_pocs": [],
            "university_pocs": [1, 2]
        }
    ]
}
```

### Get User Profile
```http
GET /auth/me/
```

Response: Same as user object above

### Update User Profile
```http
PATCH /auth/me/
Content-Type: application/json

{
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
}
```

Response: Updated user object

## OEMs

### List OEMs
```http
GET /oems/
```

Query Parameters:
- `search`: Search in name, website, contact_email, contact_phone, address
- `ordering`: Order by name, created_at, updated_at
- `page`: Page number
- `page_size`: Number of items per page

Response:
```json
{
    "count": 50,
    "next": "http://api/oems/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Tech Corp",
            "website": "https://techcorp.com",
            "contact_email": "contact@techcorp.com",
            "contact_phone": "+1234567890",
            "address": "456 Tech St",
            "poc": 1
        }
    ]
}
```

### Create OEM
```http
POST /oems/
Content-Type: application/json

{
    "name": "Tech Corp",
    "website": "https://techcorp.com",
    "contact_email": "contact@techcorp.com",
    "contact_phone": "+1234567890",
    "address": "456 Tech St",
    "poc": 1
}
```

Response: Created OEM object

### Get OEM
```http
GET /oems/{id}/
```

Response: Single OEM object

### Update OEM
```http
PUT /oems/{id}/
Content-Type: application/json

{
    "name": "Tech Corp Updated",
    "website": "https://techcorp.com",
    "contact_email": "new@techcorp.com",
    "contact_phone": "+1234567890",
    "address": "456 Tech St",
    "poc": 1
}
```

Response: Updated OEM object

## Programs

### List Programs
```http
GET /programs/
```

Query Parameters:
- `oem`: Filter by OEM ID
- `provider`: Filter by provider ID (same as OEM)
- `search`: Search in name, program_code, description, prerequisites
- `ordering`: Order by name, program_code, created_at
- `page`: Page number
- `page_size`: Number of items per page

Response:
```json
{
    "count": 30,
    "next": "http://api/programs/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Advanced Computing",
            "program_code": "AC101",
            "provider": {
                "id": 1,
                "name": "Tech Corp"
            },
            "duration": 12,
            "duration_unit": "Months",
            "description": "Advanced computing program",
            "prerequisites": "Basic programming knowledge"
        }
    ]
}
```

### Create Program
```http
POST /programs/
Content-Type: application/json

{
    "name": "Advanced Computing",
    "program_code": "AC101",
    "provider_id": 1,
    "duration": 12,
    "duration_unit": "Months",
    "description": "Advanced computing program",
    "prerequisites": "Basic programming knowledge"
}
```

Response: Created Program object

## Universities

### List Universities
```http
GET /universities/
```

Query Parameters:
- `search`: Search in name, website, contact_email, contact_phone, address
- `ordering`: Order by name, established_year, created_at
- `page`: Page number
- `page_size`: Number of items per page

Response:
```json
{
    "count": 20,
    "next": "http://api/universities/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Tech University",
            "website": "https://techuniv.edu",
            "established_year": 1990,
            "accreditation": "National Board",
            "contact_email": "contact@techuniv.edu",
            "contact_phone": "+1234567890",
            "address": "789 Univ Ave",
            "poc": 1
        }
    ]
}
```

### Create University
```http
POST /universities/
Content-Type: application/json

{
    "name": "Tech University",
    "website": "https://techuniv.edu",
    "established_year": 1990,
    "accreditation": "National Board",
    "contact_email": "contact@techuniv.edu",
    "contact_phone": "+1234567890",
    "address": "789 Univ Ave",
    "poc": 1
}
```

Response: Created University object

## Streams

### List Streams
```http
GET /streams/
```

Query Parameters:
- `university`: Filter by university ID
- `search`: Search in name, description
- `ordering`: Order by name, created_at
- `page`: Page number
- `page_size`: Number of items per page

Response:
```json
{
    "count": 15,
    "next": "http://api/streams/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Computer Science",
            "duration": 4,
            "duration_unit": "Years",
            "university": 1,
            "description": "Computer Science program"
        }
    ]
}
```

### Create Stream
```http
POST /streams/
Content-Type: application/json

{
    "name": "Computer Science",
    "duration": 4,
    "duration_unit": "Years",
    "university": 1,
    "description": "Computer Science program"
}
```

Response: Created Stream object

## Contracts

### List Contracts
```http
GET /contracts/
```

Query Parameters:
- `oem`: Filter by OEM ID
- `university`: Filter by university ID
- `status`: Filter by status
- `search`: Search in name, status, notes
- `ordering`: Order by name, status, start_date, end_date
- `page`: Page number
- `page_size`: Number of items per page

Response:
```json
{
    "count": 25,
    "next": "http://api/contracts/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Tech Partnership 2024",
            "cost_per_student": "1000.00",
            "oem_transfer_price": "800.00",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "status": "active",
            "notes": "Annual contract",
            "tax_rate": 1,
            "contract_programs": [],
            "contract_files": [],
            "streams": [],
            "oem": {
                "id": 1,
                "name": "Tech Corp"
            },
            "university": {
                "id": 1,
                "name": "Tech University"
            },
            "programs": []
        }
    ]
}
```

### Create Contract
```http
POST /contracts/
Content-Type: multipart/form-data

{
    "name": "Tech Partnership 2024",
    "university": 1,
    "oem": 1,
    "cost_per_student": "1000.00",
    "oem_transfer_price": "800.00",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "tax_rate": 1,
    "status": "active",
    "notes": "Annual contract",
    "programs_ids[]": [1, 2],
    "streams_ids[]": [1, 2],
    "files[]": [file1, file2]
}
```

Response: Created Contract object

## Batches

### List Batches
```http
GET /batches/
```

Query Parameters:
- `stream`: Filter by stream ID
- `contract`: Filter by contract ID
- `status`: Filter by status
- `search`: Search in name, notes
- `ordering`: Order by name, start_year, end_year
- `page`: Page number
- `page_size`: Number of items per page

Response:
```json
{
    "count": 40,
    "next": "http://api/batches/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "CS Batch 2024",
            "contract": 1,
            "stream": 1,
            "number_of_students": 50,
            "start_year": 2024,
            "end_year": 2028,
            "start_date": "2024-01-01",
            "end_date": "2028-12-31",
            "cost_per_student_override": null,
            "tax_rate_override": null,
            "oem_transfer_price_override": null,
            "effective_cost_per_student": "1000.00",
            "effective_tax_rate": "18.00",
            "effective_oem_transfer_price": "800.00",
            "status": "active",
            "notes": "First batch of 2024"
        }
    ]
}
```

### Create Batch
```http
POST /batches/
Content-Type: application/json

{
    "name": "CS Batch 2024",
    "contract": 1,
    "stream": 1,
    "number_of_students": 50,
    "start_year": 2024,
    "end_year": 2028,
    "start_date": "2024-01-01",
    "end_date": "2028-12-31",
    "status": "active",
    "notes": "First batch of 2024"
}
```

Response: Created Batch object

## Billing

### List Billings
```http
GET /billings/
```

Response:
```json
{
    "count": 35,
    "next": "http://api/billings/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "January 2024 Billing",
            "batches": [1, 2],
            "batch_snapshots": [],
            "notes": "Monthly billing",
            "total_amount": "50000.00",
            "total_payments": "25000.00",
            "balance_due": "25000.00",
            "total_oem_transfer_amount": "40000.00",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### Create Billing
```http
POST /billings/
Content-Type: application/json

{
    "name": "January 2024 Billing",
    "batches": [1, 2],
    "notes": "Monthly billing"
}
```

Response: Created Billing object

## Payments

### List Payments
```http
GET /payments/
```

Response:
```json
{
    "count": 100,
    "next": "http://api/payments/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "invoice": 1,
            "amount": "25000.00",
            "payment_date": "2024-01-15",
            "payment_method": "bank_transfer",
            "status": "completed",
            "transaction_reference": "TXN123456",
            "notes": "First installment",
            "documents": [],
            "created_at": "2024-01-15T00:00:00Z",
            "updated_at": "2024-01-15T00:00:00Z"
        }
    ]
}
```

### Create Payment
```http
POST /payments/
Content-Type: multipart/form-data

{
    "invoice": 1,
    "amount": "25000.00",
    "payment_date": "2024-01-15",
    "payment_method": "bank_transfer",
    "transaction_reference": "TXN123456",
    "notes": "First installment",
    "documents[]": [file1, file2]
}
```

Response: Created Payment object

## Tax Rates

### List Tax Rates
```http
GET /tax-rates/
```

Response:
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Standard GST",
            "rate": "18.00",
            "description": "Standard GST rate"
        }
    ]
}
```

### Create Tax Rate
```http
POST /tax-rates/
Content-Type: application/json

{
    "name": "Standard GST",
    "rate": "18.00",
    "description": "Standard GST rate"
}
```

Response: Created Tax Rate object

## Common Response Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Pagination

All list endpoints support pagination with the following query parameters:
- `page`: Page number (default: 1)
- `page_size`: Number of items per page (default: 20, max: 100)

## Filtering and Searching

Most list endpoints support:
- Filtering through specific query parameters
- Searching through the `search` query parameter
- Ordering through the `ordering` query parameter (prefix with `-` for descending order)

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

Token lifetime:
- Access Token: 60 minutes
- Refresh Token: 1 day 