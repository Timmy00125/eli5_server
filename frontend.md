# API Endpoints Reference for Frontend & Postman

This document lists all available API endpoints, their methods, expected request/response formats, and usage notes. Use this as a reference for frontend integration and Postman testing.

---

## Authentication Endpoints (`/api/auth`)

### Register User

- **POST** `/api/auth/register`
- **Request Body:**
  ```json
  {
    "email": "string",
    "username": "string",
    "password": "string"
  }
  ```
- **Response:**
  ```json
  {
    "access_token": "string",
    "user": {
      "id": int,
      "email": "string",
      "username": "string",
      ...
    }
  }
  ```
- **Notes:** Returns JWT token and user info on success.

### Login User

- **POST** `/api/auth/login`
- **Request Body:**
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response:**
  ```json
  {
    "access_token": "string",
    "user": {
      "id": int,
      "email": "string",
      "username": "string",
      ...
    }
  }
  ```
- **Notes:** Returns JWT token and user info on success.

### Get Current User

- **GET** `/api/auth/me`
- **Headers:**
  - `Authorization: Bearer <access_token>`
- **Response:**
  ```json
  {
    "id": int,
    "email": "string",
    "username": "string",
    ...
  }
  ```

---

## History Endpoints (`/api/history`)

### Get User History

- **GET** `/api/history?limit=50&offset=0`
- **Headers:**
  - `Authorization: Bearer <access_token>`
- **Response:**
  ```json
  {
    "entries": [
      {
        "id": int,
        "concept": "string",
        "explanation": "string",
        "created_at": "datetime"
      },
      ...
    ],
    "total": int
  }
  ```

### Save History Entry

- **POST** `/api/history`
- **Headers:**
  - `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "concept": "string",
    "explanation": "string"
  }
  ```
- **Response:**
  ```json
  {
    "id": int,
    "concept": "string",
    "explanation": "string",
    "created_at": "datetime"
  }
  ```

### Delete History Entry

- **DELETE** `/api/history/{entry_id}`
- **Headers:**
  - `Authorization: Bearer <access_token>`
- **Response:**
  ```json
  {
    "message": "History entry deleted successfully"
  }
  ```

---

## Concept Explanation Endpoints

### Get Random Concept Explanation

- **GET** `/api/explain`
- **Response:**
  ```json
  {
    "concept": "string",
    "explanation": "string"
  }
  ```

### Fallback Explanation

- **GET** `/api/fallback-explain`
- **Response:**
  ```json
  {
    "concept": "string",
    "explanation": "string"
  }
  ```

---

## Health Check Endpoint

### Health Check

- **GET** `/health`
- **Response:**
  ```json
  {
    "status": "healthy",
    "database": "connected|disconnected: reason",
    "message": "ELI5 Server is running successfully!"
  }
  ```

---

## General Notes

- All endpoints (except `/api/explain`, `/api/fallback-explain`, `/health`, and `/api/auth/register`/`login`) require a valid JWT token in the `Authorization` header.
- Date/time fields are in ISO 8601 format.
- Use this document to configure Postman collections and guide frontend API integration.
