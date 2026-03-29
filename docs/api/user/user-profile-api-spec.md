# User Profile API Specification

## Overview
User Profile API provides endpoints for retrieving user information with role detection (orderer/runner) and activity statistics for the My Page feature.

## Base URL
```
/api/v1/users
```

## Authentication
All endpoints require JWT authentication via Bearer token in the Authorization header.

---

## Endpoints

### 1. Get User Profile with Roles

Retrieves current user's profile information with role flags indicating whether the user has acted as an orderer or runner.

**Endpoint:** `GET /me/profile`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "id": 1,
  "email": "user@example.com",
  "nickname": "홍길동",
  "phoneNumber": "010-1234-5678",
  "status": "active",
  "isAdmin": false,
  "oauthProvider": "kakao",
  "roles": {
    "isOrderer": true,
    "isRunner": true
  },
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

**Role Determination:**
- `isOrderer`: `true` if user has created at least one proposal
- `isRunner`: `true` if user has submitted at least one offer

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token

---

### 2. Get User Activity Statistics

Retrieves comprehensive activity statistics for both orderer and runner roles. Designed for the My Page feature.

**Endpoint:** `GET /me/activity`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "ordererActivity": {
    "totalProposals": 10,
    "activeProposals": 2,
    "completedProposals": 7,
    "cancelledProposals": 1,
    "totalSpent": 50000,
    "recentProposals": [
      {
        "id": 1,
        "ordererId": 1,
        "title": "강남역에서 커피 배달",
        "content": "스타벅스 아메리카노 2잔",
        "deadline": "2026-03-28T15:00:00+09:00",
        "errandFee": 5000,
        "status": "POSTED",
        "paymentStatus": "CONFIRMED",
        "paymentDeadline": "2026-03-28T10:30:00+09:00",
        "depositorName": "홍길동",
        "paymentConfirmedAt": "2026-03-27T12:00:00+09:00",
        "paymentConfirmedBy": 1,
        "createdAt": "2026-03-27T10:30:00+09:00",
        "updatedAt": "2026-03-27T12:00:00+09:00"
      }
    ]
  },
  "runnerActivity": {
    "totalOffers": 20,
    "waitingOffers": 5,
    "acceptedOffers": 12,
    "rejectedOffers": 3,
    "totalEarnings": 100000,
    "acceptanceRate": 0.75,
    "recentOffers": [
      {
        "id": 1,
        "proposalId": 1,
        "runnerId": 1,
        "estimatedTime": 30,
        "message": "I can do this",
        "status": "WAITING",
        "createdAt": "2026-03-27T10:00:00+09:00",
        "updatedAt": "2026-03-27T10:00:00+09:00"
      }
    ]
  }
}
```

**Orderer Activity Fields:**
- `totalProposals`: Total number of proposals created
- `activeProposals`: Proposals in POSTED or OFFERED status
- `completedProposals`: Proposals in MATCHED status
- `cancelledProposals`: Proposals in CANCELLED status
- `totalSpent`: Sum of errand fees for MATCHED proposals
- `recentProposals`: Latest 3 proposals

**Runner Activity Fields:**
- `totalOffers`: Total number of offers submitted
- `waitingOffers`: Offers in WAITING status
- `acceptedOffers`: Offers in ACCEPTED status
- `rejectedOffers`: Offers in REJECTED status
- `totalEarnings`: Sum of errand fees from ACCEPTED offers
- `acceptanceRate`: Ratio of accepted offers to responded offers (accepted + rejected)
- `recentOffers`: Latest 5 offers

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token

---

### 3. Get User's Proposals

Retrieves a paginated list of proposals created by the current user (orderer activity).

**Endpoint:** `GET /me/proposals`

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | ProposalStatus | No | Filter by proposal status |
| page | integer | No | Page number (default: 1, min: 1) |
| limit | integer | No | Items per page (default: 10, min: 1, max: 100) |

**Valid Status Values:**
- `PENDING_PAYMENT`
- `POSTED`
- `OFFERED`
- `MATCHED`
- `CANCELLED`

**Response:** `200 OK`

```json
[
  {
    "id": 1,
    "ordererId": 1,
    "title": "강남역에서 커피 배달",
    "content": "스타벅스 아메리카노 2잔",
    "deadline": "2026-03-28T15:00:00+09:00",
    "errandFee": 5000,
    "status": "POSTED",
    "paymentStatus": "CONFIRMED",
    "paymentDeadline": "2026-03-28T10:30:00+09:00",
    "depositorName": "홍길동",
    "paymentConfirmedAt": "2026-03-27T12:00:00+09:00",
    "paymentConfirmedBy": 1,
    "createdAt": "2026-03-27T10:30:00+09:00",
    "updatedAt": "2026-03-27T12:00:00+09:00"
  }
]
```

**Sorting:** Results are sorted by creation date (newest first)

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token
- `422 Unprocessable Entity`: Invalid query parameters

**Example Requests:**
```bash
# Get all proposals
GET /api/v1/users/me/proposals

# Get only matched proposals
GET /api/v1/users/me/proposals?status=MATCHED

# Get second page with 20 items
GET /api/v1/users/me/proposals?page=2&limit=20
```

---

### 4. Get User's Offers

Retrieves a paginated list of offers submitted by the current user (runner activity).

**Endpoint:** `GET /me/offers`

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | OfferStatus | No | Filter by offer status |
| page | integer | No | Page number (default: 1, min: 1) |
| limit | integer | No | Items per page (default: 10, min: 1, max: 100) |

**Valid Status Values:**
- `WAITING`
- `ACCEPTED`
- `REJECTED`

**Response:** `200 OK`

```json
[
  {
    "id": 1,
    "proposalId": 1,
    "runnerId": 1,
    "estimatedTime": 30,
    "message": "I can do this",
    "status": "WAITING",
    "createdAt": "2026-03-27T10:00:00+09:00",
    "updatedAt": "2026-03-27T10:00:00+09:00"
  }
]
```

**Sorting:** Results are sorted by creation date (newest first)

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token
- `422 Unprocessable Entity`: Invalid query parameters

**Example Requests:**
```bash
# Get all offers
GET /api/v1/users/me/offers

# Get only accepted offers
GET /api/v1/users/me/offers?status=ACCEPTED

# Get second page with 20 items
GET /api/v1/users/me/offers?page=2&limit=20
```

---

## Data Models

### UserRoles
```typescript
{
  isOrderer: boolean;  // User has created proposals
  isRunner: boolean;   // User has submitted offers
}
```

### UserProfileResponse
```typescript
{
  id: number;
  email: string;
  nickname: string | null;
  phoneNumber: string | null;
  status: string;
  isAdmin: boolean;
  oauthProvider: string;
  roles: UserRoles;
  createdAt: string;  // ISO 8601 datetime
  updatedAt: string;  // ISO 8601 datetime
}
```

### OrdererActivitySummary
```typescript
{
  totalProposals: number;
  activeProposals: number;
  completedProposals: number;
  cancelledProposals: number;
  totalSpent: number;
  recentProposals: ProposalResponse[];  // Max 3 items
}
```

### RunnerActivitySummary
```typescript
{
  totalOffers: number;
  waitingOffers: number;
  acceptedOffers: number;
  rejectedOffers: number;
  totalEarnings: number;
  acceptanceRate: number;  // 0.0 to 1.0
  recentOffers: OfferResponse[];  // Max 5 items
}
```

### UserActivityResponse
```typescript
{
  ordererActivity: OrdererActivitySummary;
  runnerActivity: RunnerActivitySummary;
}
```

---

## Implementation Notes

1. **Role Detection:**
   - Roles are determined dynamically based on database queries
   - A user can have both roles simultaneously
   - New users have neither role until they create a proposal or submit an offer

2. **Statistics Calculation:**
   - `totalSpent` only counts MATCHED proposals (completed transactions)
   - `totalEarnings` only counts ACCEPTED offers
   - `acceptanceRate` = accepted / (accepted + rejected), returns 0.0 if no responses yet

3. **Pagination:**
   - Default page size is 10 items
   - Maximum page size is 100 items
   - Page numbers are 1-indexed

4. **Performance:**
   - Role detection uses EXISTS-style queries for efficiency
   - Statistics are calculated using aggregate queries
   - Recent items are limited to prevent large response payloads

5. **Security:**
   - All endpoints require JWT authentication
   - Users can only access their own data
   - No admin override capability (intentional isolation)
