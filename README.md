# Ticket Search API

A FastAPI-based service for fetching exchange rates from the National Bank of Kazakhstan.

## Features

- 🔄 Fetch current exchange rates from National Bank of Kazakhstan
- 💱 Query specific currency rates

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or if using uv:
```bash
uv add -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` if needed to customize the National Bank API URL.

### 3. Run the Application

```bash
uv run main.py
```
