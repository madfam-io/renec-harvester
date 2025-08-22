#!/usr/bin/env python3
"""
Generate secure API keys for RENEC Harvester.
"""

import secrets
import string
import argparse
import sys


def generate_api_key(length: int = 32, prefix: str = "renec_") -> str:
    """
    Generate a secure API key.
    
    Args:
        length: Length of the random part (default: 32)
        prefix: Prefix for the key (default: "renec_")
        
    Returns:
        Secure API key string
    """
    # Use URL-safe characters
    alphabet = string.ascii_letters + string.digits + "-_"
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{random_part}"


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a secure secret key for sessions/JWT.
    
    Args:
        length: Length in bytes (default: 32)
        
    Returns:
        Base64 encoded secret key
    """
    return secrets.token_urlsafe(length)


def main():
    parser = argparse.ArgumentParser(description="Generate secure keys for RENEC Harvester")
    parser.add_argument(
        "--type", 
        choices=["api", "secret", "both"], 
        default="both",
        help="Type of key to generate"
    )
    parser.add_argument(
        "--count", 
        type=int, 
        default=1,
        help="Number of keys to generate"
    )
    parser.add_argument(
        "--length", 
        type=int, 
        default=32,
        help="Length of the key"
    )
    parser.add_argument(
        "--prefix", 
        default="renec_",
        help="Prefix for API keys"
    )
    
    args = parser.parse_args()
    
    print("RENEC Harvester Key Generator")
    print("=" * 50)
    print()
    
    for i in range(args.count):
        if args.count > 1:
            print(f"Key Set {i + 1}:")
            
        if args.type in ["api", "both"]:
            api_key = generate_api_key(args.length, args.prefix)
            print(f"API Key: {api_key}")
            
        if args.type in ["secret", "both"]:
            secret_key = generate_secret_key(args.length)
            print(f"Secret Key: {secret_key}")
            
        if args.count > 1:
            print()
    
    print()
    print("⚠️  Security Notes:")
    print("- Store these keys securely")
    print("- Never commit keys to version control")
    print("- Use environment variables for production")
    print("- Rotate keys regularly")
    print()
    print("Add to your .env file:")
    print(f"RENEC_API_KEY={generate_api_key(args.length, args.prefix)}")
    print(f"SECRET_KEY={generate_secret_key(args.length)}")


if __name__ == "__main__":
    main()