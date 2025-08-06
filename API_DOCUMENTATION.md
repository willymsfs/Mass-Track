# Mass Tracking System - API Documentation

## Overview

The Mass Tracking System API provides a comprehensive RESTful interface for managing mass celebrations, bulk intentions, and user authentication. This documentation covers all available endpoints, request/response formats, and authentication requirements.

## Base URL

```
Development: http://localhost:5000/api
Production: https://your-domain.com/api
```

## Authentication

The API uses JWT (JSON Web Token) based authentication. Include the token in the Authorization header for protected endpoints.

### Authentication Header
```
Authorization: Bearer <your-jwt-token>
```

### Token Expiration
- Access tokens expire after 1 hour
- Refresh tokens expire after 30 days
- Use the refresh endpoint to obtain new tokens

## API Endpoints

### Authentication Endpoints

#### POST /auth/login
Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "demo_priest",
    "email": "priest@example.com",
    "full_name": "Father Demo",
    "role": "priest"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing username or password
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /auth/logout
Logout user and invalidate tokens.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

#### POST /auth/change-password
Change user password.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

### User Management Endpoints

#### GET /users/profile
Get current user profile.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "demo_priest",
  "email": "priest@example.com",
  "full_name": "Father Demo",
  "role": "priest",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-15T10:30:00Z",
  "preferences": {
    "notifications_enabled": true,
    "email_reminders": true,
    "reminder_days": 3
  }
}
```

#### PUT /users/profile
Update user profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "full_name": "Father Updated Name",
  "preferences": {
    "notifications_enabled": false,
    "email_reminders": true,
    "reminder_days": 1
  }
}
```

**Response (200 OK):**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "demo_priest",
    "email": "newemail@example.com",
    "full_name": "Father Updated Name",
    "role": "priest"
  }
}
```

### Mass Celebrations Endpoints

#### GET /mass-celebrations
Get list of mass celebrations with filtering and pagination.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20, max: 100)
- `start_date` (string): Filter from date (YYYY-MM-DD)
- `end_date` (string): Filter to date (YYYY-MM-DD)
- `mass_type` (string): Filter by type (personal, bulk, fixed_date, special)
- `sort_by` (string): Sort field (date, type, created_at)
- `sort_order` (string): Sort direction (asc, desc)

**Response (200 OK):**
```json
{
  "celebrations": [
    {
      "id": 1,
      "celebration_date": "2024-01-15",
      "celebration_time": "08:00:00",
      "mass_type": "personal",
      "intention_for": "Family intentions",
      "intention_source": "Personal",
      "location": "St. Mary's Church",
      "notes": "Morning mass",
      "bulk_intention_id": null,
      "created_at": "2024-01-15T08:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

#### POST /mass-celebrations
Create a new mass celebration record.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "celebration_date": "2024-01-15",
  "celebration_time": "08:00:00",
  "mass_type": "personal",
  "intention_for": "Family intentions",
  "intention_source": "Personal",
  "location": "St. Mary's Church",
  "notes": "Morning mass",
  "bulk_intention_id": null
}
```

**Response (201 Created):**
```json
{
  "message": "Mass celebration recorded successfully",
  "celebration": {
    "id": 1,
    "celebration_date": "2024-01-15",
    "celebration_time": "08:00:00",
    "mass_type": "personal",
    "intention_for": "Family intentions",
    "intention_source": "Personal",
    "location": "St. Mary's Church",
    "notes": "Morning mass",
    "bulk_intention_id": null,
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

#### GET /mass-celebrations/{id}
Get specific mass celebration by ID.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "id": 1,
  "celebration_date": "2024-01-15",
  "celebration_time": "08:00:00",
  "mass_type": "personal",
  "intention_for": "Family intentions",
  "intention_source": "Personal",
  "location": "St. Mary's Church",
  "notes": "Morning mass",
  "bulk_intention_id": null,
  "created_at": "2024-01-15T08:30:00Z"
}
```

#### PUT /mass-celebrations/{id}
Update existing mass celebration.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "celebration_time": "09:00:00",
  "location": "St. Joseph's Church",
  "notes": "Updated location"
}
```

**Response (200 OK):**
```json
{
  "message": "Mass celebration updated successfully",
  "celebration": {
    "id": 1,
    "celebration_date": "2024-01-15",
    "celebration_time": "09:00:00",
    "mass_type": "personal",
    "intention_for": "Family intentions",
    "intention_source": "Personal",
    "location": "St. Joseph's Church",
    "notes": "Updated location",
    "bulk_intention_id": null,
    "created_at": "2024-01-15T08:30:00Z"
  }
}
```

#### DELETE /mass-celebrations/{id}
Delete mass celebration record.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "message": "Mass celebration deleted successfully"
}
```

### Bulk Intentions Endpoints

#### GET /bulk-intentions
Get list of bulk intentions.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status` (string): Filter by status (active, paused, completed)
- `page` (integer): Page number
- `per_page` (integer): Items per page

**Response (200 OK):**
```json
{
  "bulk_intentions": [
    {
      "id": 1,
      "total_count": 300,
      "current_count": 275,
      "intention_for": "Deceased members",
      "intention_source": "Province",
      "status": "active",
      "priority": "normal",
      "start_date": "2024-01-01",
      "completion_date": null,
      "created_at": "2024-01-01T00:00:00Z",
      "pause_history": [
        {
          "paused_at": "2024-01-10T10:00:00Z",
          "resumed_at": "2024-01-12T08:00:00Z",
          "reason": "Fixed date mass",
          "count_at_pause": 285
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 5,
    "pages": 1
  }
}
```

#### POST /bulk-intentions
Create new bulk intention.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "total_count": 300,
  "intention_for": "Deceased members",
  "intention_source": "Province",
  "priority": "normal",
  "start_date": "2024-01-01",
  "notes": "Annual memorial masses"
}
```

**Response (201 Created):**
```json
{
  "message": "Bulk intention created successfully",
  "bulk_intention": {
    "id": 1,
    "total_count": 300,
    "current_count": 300,
    "intention_for": "Deceased members",
    "intention_source": "Province",
    "status": "active",
    "priority": "normal",
    "start_date": "2024-01-01",
    "completion_date": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### PUT /bulk-intentions/{id}/pause
Pause bulk intention.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "reason": "Personal mass obligations"
}
```

**Response (200 OK):**
```json
{
  "message": "Bulk intention paused successfully",
  "bulk_intention": {
    "id": 1,
    "status": "paused",
    "current_count": 275,
    "paused_at": "2024-01-15T10:00:00Z"
  }
}
```

#### PUT /bulk-intentions/{id}/resume
Resume paused bulk intention.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "message": "Bulk intention resumed successfully",
  "bulk_intention": {
    "id": 1,
    "status": "active",
    "current_count": 275,
    "resumed_at": "2024-01-16T08:00:00Z"
  }
}
```

#### GET /bulk-intentions/{id}/progress
Get detailed progress for bulk intention.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "bulk_intention": {
    "id": 1,
    "total_count": 300,
    "current_count": 275,
    "completed_count": 25,
    "completion_percentage": 8.33,
    "estimated_completion": "2024-06-15",
    "daily_average": 1.2,
    "status": "active"
  },
  "recent_celebrations": [
    {
      "date": "2024-01-15",
      "count_before": 276,
      "count_after": 275
    }
  ],
  "pause_history": [
    {
      "paused_at": "2024-01-10T10:00:00Z",
      "resumed_at": "2024-01-12T08:00:00Z",
      "reason": "Fixed date mass",
      "duration_hours": 46
    }
  ]
}
```

### Dashboard Endpoints

#### GET /dashboard/summary
Get dashboard summary data.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "current_month": {
    "total_masses": 15,
    "personal_masses": 2,
    "bulk_masses": 10,
    "fixed_date_masses": 2,
    "special_masses": 1
  },
  "monthly_obligations": {
    "personal_masses_required": 3,
    "personal_masses_completed": 2,
    "completion_percentage": 66.67,
    "days_remaining": 16
  },
  "bulk_intentions": {
    "active_count": 2,
    "total_remaining": 450,
    "lowest_count": 25,
    "completion_alerts": 1
  },
  "upcoming_obligations": [
    {
      "type": "fixed_date",
      "date": "2024-01-20",
      "intention_for": "Fr. John Memorial",
      "days_until": 5
    }
  ],
  "recent_activity": [
    {
      "type": "mass_celebration",
      "date": "2024-01-15",
      "description": "Personal mass celebrated",
      "timestamp": "2024-01-15T08:00:00Z"
    }
  ]
}
```

#### GET /dashboard/statistics
Get detailed statistics for charts and graphs.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `period` (string): Time period (month, quarter, year)
- `year` (integer): Specific year for data

**Response (200 OK):**
```json
{
  "monthly_trends": [
    {
      "month": "2024-01",
      "total_masses": 15,
      "personal_masses": 3,
      "bulk_masses": 10,
      "fixed_date_masses": 2
    }
  ],
  "mass_type_distribution": {
    "personal": 20,
    "bulk": 65,
    "fixed_date": 10,
    "special": 5
  },
  "completion_rates": {
    "personal_masses": 100,
    "bulk_intentions": 85,
    "fixed_date_masses": 100
  },
  "bulk_intention_progress": [
    {
      "id": 1,
      "intention_for": "Deceased members",
      "total_count": 300,
      "current_count": 275,
      "progress_percentage": 8.33
    }
  ]
}
```

### Calendar Endpoints

#### GET /calendar/events
Get calendar events for specified date range.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `start_date` (string): Start date (YYYY-MM-DD)
- `end_date` (string): End date (YYYY-MM-DD)
- `view` (string): Calendar view (month, week, day)

**Response (200 OK):**
```json
{
  "events": [
    {
      "id": 1,
      "date": "2024-01-15",
      "time": "08:00:00",
      "type": "personal",
      "title": "Personal Mass",
      "description": "Family intentions",
      "color": "blue",
      "editable": true
    }
  ],
  "summary": {
    "total_events": 15,
    "personal_masses": 3,
    "bulk_masses": 10,
    "fixed_date_masses": 2
  }
}
```

### Notifications Endpoints

#### GET /notifications
Get user notifications.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `unread_only` (boolean): Show only unread notifications
- `page` (integer): Page number
- `per_page` (integer): Items per page

**Response (200 OK):**
```json
{
  "notifications": [
    {
      "id": 1,
      "type": "bulk_intention_low",
      "title": "Bulk Intention Running Low",
      "message": "Your bulk intention 'Deceased members' has only 25 masses remaining.",
      "read": false,
      "created_at": "2024-01-15T10:00:00Z",
      "data": {
        "bulk_intention_id": 1,
        "current_count": 25
      }
    }
  ],
  "unread_count": 3,
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 15
  }
}
```

#### PUT /notifications/{id}/read
Mark notification as read.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "message": "Notification marked as read"
}
```

#### PUT /notifications/read-all
Mark all notifications as read.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "message": "All notifications marked as read",
  "count": 5
}
```

### Excel Import Endpoints

#### GET /excel-import/templates
Get available import templates.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "templates": [
    {
      "id": 1,
      "name": "Standard Template",
      "description": "Basic mass celebration import",
      "columns": [
        "Date",
        "Type",
        "For Whom",
        "Source",
        "Notes"
      ],
      "download_url": "/api/excel-import/templates/1/download"
    }
  ]
}
```

#### POST /excel-import/upload
Upload Excel file for import.

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Request Body:**
```
file: <Excel file>
template_id: 1
```

**Response (200 OK):**
```json
{
  "import_id": "uuid-string",
  "status": "validating",
  "message": "File uploaded successfully, validation in progress"
}
```

#### GET /excel-import/status/{import_id}
Get import status and results.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "import_id": "uuid-string",
  "status": "completed",
  "total_rows": 100,
  "valid_rows": 95,
  "invalid_rows": 5,
  "imported_rows": 95,
  "errors": [
    {
      "row": 5,
      "column": "Date",
      "error": "Invalid date format"
    }
  ],
  "summary": {
    "personal_masses": 30,
    "bulk_masses": 50,
    "fixed_date_masses": 10,
    "special_masses": 5
  }
}
```

#### POST /excel-import/confirm/{import_id}
Confirm and execute import after validation.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "message": "Import completed successfully",
  "imported_count": 95,
  "skipped_count": 5
}
```

### Reports Endpoints

#### GET /reports/monthly
Generate monthly report.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `year` (integer): Year
- `month` (integer): Month (1-12)
- `format` (string): Output format (json, pdf)

**Response (200 OK):**
```json
{
  "report": {
    "period": "2024-01",
    "summary": {
      "total_masses": 15,
      "personal_masses": 3,
      "bulk_masses": 10,
      "fixed_date_masses": 2,
      "special_masses": 0
    },
    "obligations": {
      "personal_masses_required": 3,
      "personal_masses_completed": 3,
      "completion_rate": 100
    },
    "bulk_intentions": [
      {
        "intention_for": "Deceased members",
        "masses_celebrated": 10,
        "remaining_count": 275
      }
    ],
    "daily_breakdown": [
      {
        "date": "2024-01-01",
        "masses": 1,
        "types": ["bulk"]
      }
    ]
  }
}
```

#### GET /reports/annual
Generate annual report.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `year` (integer): Year
- `format` (string): Output format (json, pdf)

**Response (200 OK):**
```json
{
  "report": {
    "year": 2024,
    "summary": {
      "total_masses": 180,
      "personal_masses": 36,
      "bulk_masses": 120,
      "fixed_date_masses": 20,
      "special_masses": 4
    },
    "monthly_breakdown": [
      {
        "month": "2024-01",
        "total_masses": 15,
        "personal_completion_rate": 100
      }
    ],
    "bulk_intentions_completed": [
      {
        "intention_for": "Deceased members",
        "total_count": 300,
        "completion_date": "2024-06-15",
        "duration_days": 165
      }
    ]
  }
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "celebration_date",
        "message": "Date is required"
      }
    ]
  }
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED`: Missing or invalid authentication
- `AUTHORIZATION_FAILED`: Insufficient permissions
- `VALIDATION_ERROR`: Request validation failed
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `DUPLICATE_RESOURCE`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_SERVER_ERROR`: Server error

### HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

### Limits
- **Authentication endpoints**: 5 requests per minute
- **General API endpoints**: 100 requests per minute
- **File upload endpoints**: 10 requests per hour

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642694400
```

## Pagination

### Request Parameters
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

### Response Format
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

## Webhooks (Future Feature)

### Available Events
- `mass_celebration.created`
- `bulk_intention.completed`
- `monthly_obligation.completed`
- `bulk_intention.low_count`

### Webhook Payload Format
```json
{
  "event": "mass_celebration.created",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "celebration_id": 1,
    "priest_id": 1,
    "celebration_date": "2024-01-15"
  }
}
```

## SDK and Libraries

### JavaScript/Node.js
```javascript
const MassTrackingAPI = require('mass-tracking-api');

const client = new MassTrackingAPI({
  baseURL: 'https://your-domain.com/api',
  token: 'your-jwt-token'
});

// Record a mass celebration
const celebration = await client.massCelebrations.create({
  celebration_date: '2024-01-15',
  mass_type: 'personal',
  intention_for: 'Family intentions'
});
```

### Python
```python
from mass_tracking_api import MassTrackingClient

client = MassTrackingClient(
    base_url='https://your-domain.com/api',
    token='your-jwt-token'
)

# Get dashboard summary
summary = client.dashboard.get_summary()
```

## Testing

### Test Environment
```
Base URL: https://test.your-domain.com/api
Test User: demo_priest
Test Password: demo123
```

### Postman Collection
Download the Postman collection for easy API testing:
[Mass Tracking API.postman_collection.json](./postman/Mass_Tracking_API.postman_collection.json)

## Support

For API support and questions:
- **Documentation**: This document and inline API docs
- **GitHub Issues**: https://github.com/willymsfs/Mass-Track/issues
- **Email**: api-support@your-domain.com

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial API release
- Authentication endpoints
- Mass celebration management
- Bulk intention tracking
- Dashboard and reporting
- Excel import functionality

---

This API documentation provides comprehensive coverage of all available endpoints and functionality in the Mass Tracking System. For the most up-to-date information, always refer to the inline API documentation available at `/api/docs` when the system is running.

