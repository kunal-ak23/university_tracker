# University Events Feature

## Overview

The University Events feature allows universities to create and manage upcoming events with an approval workflow and integration capabilities for Outlook Calendar and Notion.

## Features

### 1. Event Management
- **Create Events**: Universities can create events with detailed information
- **Event Details**: Title, description, start/end datetime, location, optional batch association
- **Status Tracking**: Draft → Pending Approval → Approved/Rejected → Upcoming → Ongoing → Completed

### 2. Approval Workflow
- **Draft Status**: Events start as drafts and can be edited
- **Submit for Approval**: Events can be submitted for approval by university POCs
- **Approval/Rejection**: Only university POCs and superusers can approve/reject events
- **Rejection Reasons**: Events can be rejected with specific reasons

### 3. Integration Capabilities
- **Outlook Calendar**: Automatic creation of calendar events when approved
- **Notion Pages**: Automatic creation of Notion pages when approved
- **Integration Tracking**: Status tracking for both integrations
- **Error Handling**: Failed integrations are logged and tracked

### 4. Invitee Management
- **Automatic Invitees**: System automatically identifies relevant POCs
- **Custom Invitees**: Additional invitees can be added as comma-separated emails
- **Simple Management**: Easy add/remove of email addresses
- **Role-based Access**: Different users see different events based on their roles

## Models

### UniversityEvent
```python
class UniversityEvent(BaseModel):
    university = models.ForeignKey(University, ...)
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=500)
    batch = models.ForeignKey(Batch, null=True, blank=True)
    status = models.CharField(choices=EVENT_STATUS_CHOICES, default='draft')
    
    # Approval fields
    submitted_for_approval_at = models.DateTimeField(null=True)
    approved_by = models.ForeignKey(CustomUser, null=True)
    approved_at = models.DateTimeField(null=True)
    rejection_reason = models.TextField(null=True)
    
    # Integration fields
    outlook_calendar_id = models.CharField(max_length=255, null=True)
    outlook_calendar_url = models.URLField(null=True)
    notion_page_id = models.CharField(max_length=255, null=True)
    notion_page_url = models.URLField(null=True)
    integration_status = models.CharField(choices=INTEGRATION_STATUS_CHOICES, default='pending')
    integration_notes = models.TextField(null=True)
```

### Invitees Field
The `invitees` field stores comma-separated email addresses:
```python
invitees = models.TextField(blank=True, null=True, help_text="Comma separated email addresses")
```

Example: `"john@example.com, jane@example.com, admin@university.edu"`

## API Endpoints

### University Events
- `GET /api/university-events/` - List all events (filtered by user role)
- `POST /api/university-events/` - Create new event
- `GET /api/university-events/{id}/` - Get event details
- `PUT /api/university-events/{id}/` - Update event
- `DELETE /api/university-events/{id}/` - Delete event

### Event Actions
- `POST /api/university-events/{id}/submit_for_approval/` - Submit for approval
- `POST /api/university-events/{id}/approve/` - Approve/reject event
- `POST /api/university-events/{id}/update_status/` - Update status based on time
- `GET /api/university-events/{id}/invitees/` - Get event invitees
- `POST /api/university-events/{id}/manage_invitees/` - Add/remove invitees
- `GET /api/university-events/{id}/integration_status/` - Get integration status

## Usage Examples

### Creating an Event
```python
# Create a new event
event_data = {
    "university": 1,
    "title": "Annual Tech Conference",
    "description": "Join us for our annual technology conference",
    "start_datetime": "2024-06-15T09:00:00Z",
    "end_datetime": "2024-06-15T17:00:00Z",
    "location": "Main Auditorium, Building A",
    "batch": 1,  # Optional
    "notes": "Please bring your laptops"
}

response = requests.post('/api/university-events/', json=event_data)
```

### Submitting for Approval
```python
# Submit event for approval
response = requests.post(f'/api/university-events/{event_id}/submit_for_approval/')
```

### Approving an Event
```python
# Approve an event
approval_data = {
    "action": "approve"
}
response = requests.post(f'/api/university-events/{event_id}/approve/', json=approval_data)

# Reject an event
rejection_data = {
    "action": "reject",
    "reason": "Insufficient budget allocation"
}
response = requests.post(f'/api/university-events/{event_id}/approve/', json=rejection_data)
```

### Managing Invitees
```python
# Add invitee
invitee_data = {
    "email": "john.doe@example.com",
    "action": "add"
}
response = requests.post(f'/api/university-events/{event_id}/manage_invitees/', json=invitee_data)

# Remove invitee
invitee_data = {
    "email": "john.doe@example.com",
    "action": "remove"
}
response = requests.post(f'/api/university-events/{event_id}/manage_invitees/', json=invitee_data)
```

## Integration Setup

### Outlook Calendar Integration
To enable Outlook Calendar integration, add the following settings to your Django settings:

```python
# Outlook Calendar Integration Settings
OUTLOOK_TENANT_ID = 'your-tenant-id'
OUTLOOK_CLIENT_ID = 'your-client-id'
OUTLOOK_CLIENT_SECRET = 'your-client-secret'
```

### Notion Integration
To enable Notion integration, add the following settings:

```python
# Notion Integration Settings
NOTION_API_KEY = 'your-notion-api-key'
NOTION_EVENTS_DATABASE_ID = 'your-database-id'
```

## Permissions

### Role-based Access
- **University POC**: Can create, edit, and manage events for their university
- **Provider POC**: Can view events related to their OEM contracts
- **Superuser**: Full access to all events
- **Agent**: Limited access based on their associations

### Event Permissions
- **Draft**: Only creator can edit
- **Pending Approval**: Only university POCs and superusers can approve/reject
- **Approved**: Status automatically updates based on time
- **Completed**: Read-only

## Admin Interface

The Django admin interface provides:
- Complete event management
- Bulk approval/rejection actions
- Integration status monitoring
- Invitee management
- Status updates

## Migration

To apply the database changes:

```bash
python manage.py makemigrations core
python manage.py migrate
```

## Future Enhancements

1. **Email Notifications**: Automatic email notifications for event updates
2. **Calendar Sync**: Two-way sync with Outlook calendar
3. **Recurring Events**: Support for recurring event patterns
4. **Event Templates**: Predefined event templates
5. **Advanced Reporting**: Event analytics and reporting
6. **Mobile App**: Mobile-friendly event management
7. **Video Conferencing**: Integration with video platforms
8. **Attendance Tracking**: Track actual attendance vs. RSVPs

## Troubleshooting

### Common Issues

1. **Integration Failures**: Check API credentials and network connectivity
2. **Permission Errors**: Verify user roles and permissions
3. **Date Validation**: Ensure end datetime is after start datetime
4. **Batch Validation**: Ensure batch belongs to the selected university

### Logs
Integration failures and errors are logged in Django's logging system. Check the logs for detailed error messages. 