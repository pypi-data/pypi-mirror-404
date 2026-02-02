#!/usr/bin/env python3
"""
Generate MCP API Token

Generates a signed JWT token for MCP authentication.
Uses az_keyvault_client_secret as the signing key.

Usage:
    python generate_mcp_token.py --expiry-date "2025-12-31"
    python generate_mcp_token.py -e "2026-06-30"
"""

import argparse
import os
import sys
from datetime import datetime

import jwt


def generate_token(expiry_date: str) -> str:
    """Generate a signed JWT token with expiry date."""
    
    client_secret = os.environ.get("az_keyvault_client_secret")
    if not client_secret:
        raise ValueError("az_keyvault_client_secret environment variable is not set")
    
    # Parse end date
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        expiry_timestamp = int(expiry.timestamp())
    except ValueError:
        raise ValueError(f"Invalid date format: {expiry_date}. Use YYYY-MM-DD")
    
    # Create payload
    payload = {
        "exp": expiry_timestamp,
        "iat": int(datetime.now().timestamp()),
        "type": "mcp_api_token"
    }
    
    # Sign and return token
    token = jwt.encode(payload, client_secret, algorithm="HS256")
    return token


def main():
    parser = argparse.ArgumentParser(description="Generate MCP API Token")
    parser.add_argument(
        "-e", "--expiry-date",
        required=True,
        help="Token expiry date in YYYY-MM-DD format"
    )
    
    args = parser.parse_args()
    
    try:
        token = generate_token(args.expiry_date)
        print(f"\nMCP Token (expires {args.expiry_date}):\n")
        print(token)
        print("\n")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()