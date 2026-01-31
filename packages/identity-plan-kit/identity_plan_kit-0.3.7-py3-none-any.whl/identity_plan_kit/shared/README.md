# Error Response Documentation

This document describes all error responses returned by the API. All errors follow a consistent format.

## Response Format

All error responses use the following structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "context": { }  // Optional additional details
  }
}
```

---

## Authentication Errors (401 Unauthorized)

### TOKEN_EXPIRED
Session has expired and user needs to re-authenticate.

```json
{
  "success": false,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Your session has expired. Please log in again."
  }
}
```

### TOKEN_INVALID
The provided authentication token is malformed or invalid.

```json
{
  "success": false,
  "error": {
    "code": "TOKEN_INVALID",
    "message": "Invalid authentication token."
  }
}
```

### UNAUTHORIZED
Request requires authentication but none was provided.

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required."
  }
}
```

### USER_NOT_FOUND
The authenticated user no longer exists in the system.

```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found."
  }
}
```

### AUTHENTICATION_FAILED
General authentication failure (invalid credentials).

```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Authentication Failed."
  }
}
```

---

## Refresh Token Errors (401 Unauthorized)

### REFRESH_TOKEN_MISSING
Refresh token was not provided in the request.

```json
{
  "success": false,
  "error": {
    "code": "REFRESH_TOKEN_MISSING",
    "message": "Refresh token not provided. Please log in again."
  }
}
```

### REFRESH_TOKEN_INVALID
The provided refresh token is invalid or has been revoked.

```json
{
  "success": false,
  "error": {
    "code": "REFRESH_TOKEN_INVALID",
    "message": "Invalid refresh token. Please log in again."
  }
}
```

### REFRESH_TOKEN_EXPIRED
The refresh token has expired.

```json
{
  "success": false,
  "error": {
    "code": "REFRESH_TOKEN_EXPIRED",
    "message": "Refresh token has expired. Please log in again."
  }
}
```

---

## OAuth Errors (400/401)

### OAUTH_ERROR
General OAuth authentication failure. Returned for:
- Invalid authorization code format
- OAuth authentication failed
- Generic `OAuth error: X` messages from provider

```json
{
  "success": false,
  "error": {
    "code": "OAUTH_ERROR",
    "message": "OAuth authentication failed. Please try again."
  }
}
```

### OAUTH_STATE_INVALID
The OAuth state parameter doesn't match (possible CSRF attack).

```json
{
  "success": false,
  "error": {
    "code": "OAUTH_STATE_INVALID",
    "message": "Invalid OAuth state. Please try again."
  }
}
```

### OAUTH_PROVIDER_ERROR
Error from the OAuth provider (Google, etc.).

```json
{
  "success": false,
  "error": {
    "code": "OAUTH_PROVIDER_ERROR",
    "message": "OAuth provider error. Please try again."
  }
}
```

---

## Authorization Errors (403 Forbidden)

### USER_INACTIVE
The user account has been deactivated.

```json
{
  "success": false,
  "error": {
    "code": "USER_INACTIVE",
    "message": "Your account has been deactivated."
  }
}
```

### PERMISSION_DENIED
User lacks the required permission for the action.

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You do not have permission to perform this action.",
    "context": {
      "permission": "admin.write"
    }
  }
}
```

### FEATURE_NOT_AVAILABLE
The requested feature is not available in the user's plan.

```json
{
  "success": false,
  "error": {
    "code": "FEATURE_NOT_AVAILABLE",
    "message": "This feature requires an upgraded plan.",
    "context": {
      "feature": "premium_export",
      "plan": "free"
    }
  }
}
```

### PLAN_AUTHORIZATION_ERROR
User is not authorized to perform plan-related operations.

```json
{
  "success": false,
  "error": {
    "code": "PLAN_AUTHORIZATION_ERROR",
    "message": "Not authorized to assign plan",
    "context": {
      "operation": "assign_plan",
      "target_user_id": "user-123"
    }
  }
}
```

---

## Plan/Subscription Errors

### PLAN_EXPIRED (402 Payment Required)
The user's subscription plan has expired.

```json
{
  "success": false,
  "error": {
    "code": "PLAN_EXPIRED",
    "message": "Your subscription plan has expired. Please renew to continue."
  }
}
```

### USER_PLAN_NOT_FOUND (403/404)
No active subscription plan found for the user.

```json
{
  "success": false,
  "error": {
    "code": "USER_PLAN_NOT_FOUND",
    "message": "No active subscription plan found."
  }
}
```

### PLAN_NOT_FOUND (404 Not Found)
The requested plan does not exist.

```json
{
  "success": false,
  "error": {
    "code": "PLAN_NOT_FOUND",
    "message": "Plan 'enterprise' not found"
  }
}
```

### QUOTA_EXCEEDED (429 Too Many Requests)
User has exceeded their usage quota for a feature.

```json
{
  "success": false,
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "Monthly quota exceeded for ai_generation",
    "context": {
      "feature": "ai_generation",
      "limit": 100,
      "used": 150,
      "period": "monthly"
    }
  }
}
```

---

## Resource Errors (404 Not Found)

### NOT_FOUND
The requested resource does not exist.

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource '/api/v1/users/123' was not found.",
    "context": {
      "path": "/api/v1/users/123",
      "method": "GET"
    }
  }
}
```

### ROLE_NOT_FOUND
The requested role does not exist.

```json
{
  "success": false,
  "error": {
    "code": "ROLE_NOT_FOUND",
    "message": "Role 'super_admin' not found"
  }
}
```

---

## Request Errors (400 Bad Request)

### BAD_REQUEST
The request is malformed or contains invalid parameters.

```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Bad request"
  }
}
```

### VALIDATION_ERROR (422 Unprocessable Entity)
Request validation failed (Pydantic/schema validation).

**Single field error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "'email' must be a valid email address.",
    "context": {
      "errors": [
        {
          "field": "email",
          "message": "'email' must be a valid email address.",
          "type": "email_type"
        }
      ]
    }
  }
}
```

**Multiple field errors:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for: email, password",
    "context": {
      "errors": [
        {
          "field": "email",
          "message": "'email' must be a valid email address.",
          "type": "email_type"
        },
        {
          "field": "password",
          "message": "'password' is too short.",
          "type": "string_too_short"
        }
      ]
    }
  }
}
```

**Missing required fields:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Required fields are missing: email, password",
    "context": {
      "errors": [
        {
          "field": "email",
          "message": "'email' is required.",
          "type": "missing"
        },
        {
          "field": "password",
          "message": "'password' is required.",
          "type": "missing"
        }
      ]
    }
  }
}
```

**Invalid JSON:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid JSON in request body. Please check for syntax errors.",
    "context": {
      "errors": [
        {
          "field": "request body",
          "message": "The request body contains invalid JSON. Please check for syntax errors like missing quotes, commas, or brackets.",
          "type": "json_invalid"
        }
      ]
    }
  }
}
```

---

## Method Errors (405 Method Not Allowed)

### METHOD_NOT_ALLOWED
The HTTP method is not supported for the endpoint.

```json
{
  "success": false,
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "Method 'DELETE' is not allowed for '/api/v1/users'.",
    "context": {
      "path": "/api/v1/users",
      "method": "DELETE"
    }
  }
}
```

---

## Rate Limiting (429 Too Many Requests)

### RATE_LIMIT_EXCEEDED
Too many requests in a given time period.

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded"
  }
}
```

---

## Server Errors (5xx)

### INTERNAL_SERVER_ERROR (500)
An unexpected error occurred on the server.

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later."
  }
}
```

### BAD_GATEWAY (502)
Invalid response from an upstream server.

```json
{
  "success": false,
  "error": {
    "code": "BAD_GATEWAY",
    "message": "Bad Gateway"
  }
}
```

### SERVICE_UNAVAILABLE (503)
The server is temporarily unable to handle requests.

```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Service Unavailable"
  }
}
```

### TIMEOUT (408)
The request timed out.

```json
{
  "success": false,
  "error": {
    "code": "TIMEOUT",
    "message": "Request Timeout"
  }
}
```

---

## Domain Errors

These errors originate from business logic violations.

### VALIDATION_ERROR (400)
Domain-level validation failure.

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "context": {
      "field": "email",
      "value": "invalid"
    }
  }
}
```

### ENTITY_NOT_FOUND (404)
A domain entity was not found.

```json
{
  "success": false,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "User with id 'user-123' not found",
    "context": {
      "entity_type": "User",
      "entity_id": "user-123"
    }
  }
}
```

### CONFLICT (409)
Operation conflicts with current state (e.g., duplicate resource).

```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "Email already exists",
    "context": {
      "entity_type": "User"
    }
  }
}
```

### AUTHORIZATION_FAILED (403)
Domain-level authorization failure.

```json
{
  "success": false,
  "error": {
    "code": "AUTHORIZATION_FAILED",
    "message": "Not allowed to perform this action",
    "context": {
      "action": "delete",
      "resource_type": "Document"
    }
  }
}
```

### INVALID_STATE (422)
Invalid state transition attempted.

```json
{
  "success": false,
  "error": {
    "code": "INVALID_STATE",
    "message": "Cannot cancel completed order",
    "context": {
      "current_state": "completed",
      "expected_states": ["pending", "processing"]
    }
  }
}
```

---

## Database Errors

### DATABASE_ERROR (500)
General database error.

```json
{
  "success": false,
  "error": {
    "code": "DATABASE_ERROR",
    "message": "A database error occurred"
  }
}
```

### DATABASE_CONNECTION_ERROR (503)
Cannot connect to the database.

```json
{
  "success": false,
  "error": {
    "code": "DATABASE_CONNECTION_ERROR",
    "message": "Database connection failed"
  }
}
```

### DATABASE_TIMEOUT_ERROR (408)
Database operation timed out.

```json
{
  "success": false,
  "error": {
    "code": "DATABASE_TIMEOUT_ERROR",
    "message": "Database operation timed out"
  }
}
```

### DATABASE_CIRCUIT_BREAKER_OPEN (503)
Database circuit breaker is open due to repeated failures.

```json
{
  "success": false,
  "error": {
    "code": "DATABASE_CIRCUIT_BREAKER_OPEN",
    "message": "Database temporarily unavailable"
  }
}
```

---

## Error Code Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TOKEN_EXPIRED` | 401 | Access token has expired |
| `TOKEN_INVALID` | 401 | Access token is invalid |
| `UNAUTHORIZED` | 401 | No authentication provided |
| `USER_NOT_FOUND` | 401/404 | User does not exist |
| `AUTHENTICATION_FAILED` | 401 | Invalid credentials |
| `REFRESH_TOKEN_MISSING` | 401 | No refresh token provided |
| `REFRESH_TOKEN_INVALID` | 401 | Invalid refresh token |
| `REFRESH_TOKEN_EXPIRED` | 401 | Refresh token expired |
| `OAUTH_ERROR` | 400/401 | OAuth authentication failed |
| `OAUTH_STATE_INVALID` | 401 | Invalid OAuth state parameter |
| `OAUTH_PROVIDER_ERROR` | 401 | OAuth provider returned error |
| `USER_INACTIVE` | 403 | User account is deactivated |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `FEATURE_NOT_AVAILABLE` | 403 | Feature not in user's plan |
| `PLAN_AUTHORIZATION_ERROR` | 403 | Not authorized for plan operation |
| `PLAN_EXPIRED` | 402 | Subscription has expired |
| `USER_PLAN_NOT_FOUND` | 403/404 | No active subscription |
| `PLAN_NOT_FOUND` | 404 | Plan does not exist |
| `QUOTA_EXCEEDED` | 429 | Usage quota exceeded |
| `NOT_FOUND` | 404 | Resource not found |
| `ROLE_NOT_FOUND` | 404 | Role does not exist |
| `BAD_REQUEST` | 400 | Malformed request |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method not supported |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `CONFLICT` | 409 | Resource conflict |
| `ENTITY_NOT_FOUND` | 404 | Domain entity not found |
| `AUTHORIZATION_FAILED` | 403 | Domain authorization failed |
| `INVALID_STATE` | 422 | Invalid state transition |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |
| `BAD_GATEWAY` | 502 | Upstream server error |
| `SERVICE_UNAVAILABLE` | 503 | Server temporarily unavailable |
| `TIMEOUT` | 408 | Request timeout |
| `DATABASE_ERROR` | 500 | Database error |
| `DATABASE_CONNECTION_ERROR` | 503 | Database connection failed |
| `DATABASE_TIMEOUT_ERROR` | 408 | Database timeout |
| `DATABASE_CIRCUIT_BREAKER_OPEN` | 503 | Database circuit breaker open |
