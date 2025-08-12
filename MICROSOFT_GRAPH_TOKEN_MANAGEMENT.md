# Microsoft Graph Token Management System (ROPC Flow)

## Overview

This document describes the comprehensive token management system for Microsoft Graph API integration in the Datagami University Tracker application. The system uses ROPC (Resource Owner Password Credentials) flow for group event creation, which requires delegated permissions.

## Features

- **ROPC Flow**: Uses Resource Owner Password Credentials for delegated permissions
- **Automatic Token Acquisition**: Backend service acquires tokens using ROPC flow
- **Token Storage**: Secure database storage with encryption and access controls
- **Automatic Refresh**: Tokens are automatically refreshed before expiration
- **Error Handling**: Comprehensive error tracking and recovery mechanisms
- **Caching**: In-memory caching for improved performance
- **Admin Interface**: Django admin interface for token management
- **API Endpoints**: REST API endpoints for token operations
- **Management Commands**: Django management commands for token operations

## Architecture

### Components

1. **MicrosoftGraphToken Model** (`core/models.py`)
   - Database model for storing token information
   - Tracks token lifecycle, errors, and usage

2. **MicrosoftGraphTokenService** (`core/graph_token_service.py`)
   - Core service for token management
   - Handles acquisition, refresh, and validation

3. **Admin Interface** (`core/admin.py`)
   - Django admin interface for token management
   - Bulk operations and status monitoring

4. **API Endpoints** (`core/views.py`)
   - REST API for token operations
   - Status checking and management

5. **Management Commands** (`core/management/commands/`)
   - Command-line tools for token operations

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Microsoft Graph Configuration
GRAPH_CLIENT_ID=your_client_id
GRAPH_TENANT=your_tenant_id
GRAPH_GROUP_ID=your_group_id
GRAPH_USERNAME=your_username@yourdomain.com  # For ROPC flow
GRAPH_PASSWORD=your_password  # For ROPC flow
```

### Azure App Registration

1. Go to Azure Portal > Azure Active Directory > App registrations
2. Create a new registration or use existing one
3. Configure the following:
   - **API Permissions**: Add Microsoft Graph permissions
     - `Group.ReadWrite.All` (Delegated permission for group calendar access)
     - `User.Read` (Delegated permission for user access)
     - **Important**: Make sure to grant admin consent for the delegated permissions
   - **Authentication**: Configure for public client (no client secret needed)
4. Note down the Client ID and Tenant ID

### Important: Delegated Permissions for ROPC Flow

For ROPC flow, you need **Delegated Permissions** (not Application Permissions):

1. In your Azure App Registration, go to "API permissions"
2. Click "Add a permission"
3. Select "Microsoft Graph"
4. Choose "Delegated permissions" (not "Application permissions")
5. Search for and add:
   - `Group.ReadWrite.All` (for group calendar access)
   - `User.Read` (for user access)
6. Click "Grant admin consent" to approve the permissions

**Note**: Delegated permissions work at the user level and require user credentials (username/password) for ROPC flow.

## Usage

### Automatic Token Acquisition

The system automatically acquires tokens when needed:

```python
from core.graph_token_service import get_graph_access_token

# Get a valid access token
token = get_graph_access_token(token_type='ropc')
if token:
    # Use the token for API calls
    pass
```

### Manual Token Management

#### Using Management Commands

```bash
# Acquire a new token
python manage.py manage_graph_tokens acquire --token-type ropc

# Refresh existing tokens
python manage.py manage_graph_tokens refresh --token-type ropc

# Clean up expired tokens
python manage.py manage_graph_tokens cleanup

# Check token status
python manage.py manage_graph_tokens status

# Validate active tokens
python manage.py manage_graph_tokens validate
```

#### Using Admin Interface

1. Access Django admin at `/admin/`
2. Navigate to "Microsoft Graph Tokens"
3. Use bulk actions for:
   - Acquire new token
   - Refresh tokens
   - Clean up tokens
   - Validate tokens

#### Using API Endpoints

```bash
# Get token status
GET /api/graph-tokens/status/

# Acquire new token
POST /api/graph-tokens/acquire_token/
{
    "token_type": "ropc",
    "force_refresh": false
}

# Clean up tokens
POST /api/graph-tokens/cleanup_tokens/

# Validate tokens
POST /api/graph-tokens/validate_tokens/
```

### Integration with Event System

The token management system is automatically integrated with the event creation system:

```python
# In your event creation code
from core.services import EventIntegrationService

# The service will automatically get a valid token
success = EventIntegrationService.create_outlook_event(event)
```

## Token Lifecycle

### 1. Token Acquisition
- System checks for existing valid tokens
- If none found, acquires new token using ROPC flow
- Stores token in database with expiration time

### 2. Token Usage
- Tokens are cached in memory for 5 minutes
- Usage is tracked in database
- Error count is reset on successful use

### 3. Token Refresh
- Tokens are automatically refreshed 5 minutes before expiration
- Failed refresh attempts are tracked
- Tokens with too many errors are deactivated

### 4. Token Cleanup
- Expired tokens are automatically deactivated
- Old inactive tokens are removed after 30 days
- Error tracking helps identify problematic tokens

## Error Handling

### Error Tracking
- Each token tracks consecutive error count
- Error messages are stored for debugging
- Tokens with 3+ consecutive errors are deactivated

### Recovery Mechanisms
- Automatic retry with new token acquisition
- Comprehensive logging for troubleshooting

### Common Issues

1. **Configuration Issues**
   - Missing environment variables
   - Incorrect client credentials
   - Insufficient API permissions

2. **Network Issues**
   - Timeout errors
   - Connection failures
   - Rate limiting

3. **Token Issues**
   - Expired tokens
   - Invalid scopes
   - Revoked permissions

## Security Considerations

### Token Storage
- Tokens are stored in database with proper access controls
- Sensitive fields should be encrypted in production
- Regular cleanup prevents token accumulation

### Access Control
- Only superusers can manage tokens via admin
- API endpoints require proper authentication
- Token operations are logged for audit

### Best Practices
- Use ROPC flow for group event creation (requires delegated permissions)
- Store user credentials securely (consider using app passwords for MFA accounts)
- Implement proper error handling
- Monitor token usage and errors
- Regular cleanup of expired tokens

## Monitoring and Maintenance

### Health Checks
- Regular token validation
- Error rate monitoring
- Performance metrics tracking

### Maintenance Tasks
- Daily token cleanup
- Weekly token validation
- Monthly error analysis

### Logging
- All token operations are logged
- Error details are captured
- Performance metrics are tracked

## Troubleshooting

### Common Problems

1. **"Failed to acquire token"**
   - Check environment variables
   - Verify Azure app registration
   - Check API permissions

2. **"ErrorAccessDenied" or "Access is denied"**
   - **Most Common**: Using Application permissions instead of Delegated permissions
   - Ensure you've granted admin consent for delegated permissions
   - Check that the app has the correct `Group.ReadWrite.All` delegated permission
   - Verify the M365 Group ID is correct and the user has access to it
   - Check if MFA is enabled (may need app password)

3. **"Token validation failed"**
   - Token may be expired
   - Permissions may have changed
   - Network connectivity issues

4. **"Too many errors"**
   - Check Azure app configuration
   - Verify client credentials
   - Review error logs

### Debug Commands

```bash
# Check configuration
python manage.py manage_graph_tokens status

# Force token acquisition
python manage.py manage_graph_tokens acquire --force

# Validate all tokens
python manage.py manage_graph_tokens validate
```

### Log Analysis

Check the Django logs for detailed error information:

```bash
tail -f debug.log | grep -i "graph\|token"
```

## API Reference

### MicrosoftGraphTokenService

#### Methods

- `get_access_token(token_type, force_refresh=False)`: Get valid access token
- `refresh_token(token_obj)`: Refresh specific token
- `handle_token_error(token_obj, error_message)`: Handle token errors
- `cleanup_old_tokens()`: Clean up expired tokens
- `get_token_status()`: Get token statistics
- `validate_token(access_token)`: Validate token

### Management Commands

- `manage_graph_tokens acquire`: Acquire new token
- `manage_graph_tokens refresh`: Refresh existing tokens
- `manage_graph_tokens cleanup`: Clean up expired tokens
- `manage_graph_tokens status`: Show token status
- `manage_graph_tokens validate`: Validate active tokens

### API Endpoints

- `GET /api/graph-tokens/status/`: Get token status
- `POST /api/graph-tokens/acquire_token/`: Acquire new token
- `POST /api/graph-tokens/cleanup_tokens/`: Clean up tokens
- `POST /api/graph-tokens/validate_tokens/`: Validate tokens

## Migration Guide

### Migration Complete

The system now uses ROPC flow for group event creation. The old client credentials flow has been updated to use ROPC flow which requires delegated permissions.

### Database Migration

Run the migration to create the token table:

```bash
python manage.py makemigrations core
python manage.py migrate
```

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review error logs
3. Verify configuration
4. Test with management commands
5. Contact the development team

## Future Enhancements

- Token encryption at rest
- Advanced caching strategies
- Token rotation policies
- Integration with Azure Key Vault
- Enhanced monitoring and alerting 