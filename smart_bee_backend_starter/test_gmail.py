#!/usr/bin/env python3
"""Test Gmail Connection"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

from app.services.ingestion.gmail_service import GmailService


def main():
    print("=" * 60)
    print("🐝 Smart BEE - Gmail Connection Test")
    print("=" * 60)
    print()
    
    try:
        print("📡 Initializing Gmail service...")
        gmail = GmailService()
        print("✅ Gmail service initialized!")
        print()
        
        print("👤 Fetching profile...")
        profile = gmail.get_profile()
        
        if profile:
            print("✅ Successfully connected to Gmail!")
            print()
            print(f"📧 Email: {profile['email']}")
            print(f"📊 Total Messages: {profile['messages_total']}")
            print(f"💬 Total Threads: {profile['threads_total']}")
            print()
            
            print("📬 Fetching 3 unread emails...")
            emails = gmail.get_unread_emails(max_results=3)
            
            if emails:
                print(f"✅ Found {len(emails)} unread emails!")
                print()
                for i, email in enumerate(emails, 1):
                    print(f"{i}. From: {email['sender'][:50]}")
                    print(f"   Subject: {email['subject'][:60]}")
                    print()
            else:
                print("📭 No unread emails found")
            
            print("=" * 60)
            print("🎉 Gmail Connection Test Complete!")
            print("=" * 60)
            print()
            print("✅ All systems operational")
            print("🚀 Ready to start the server!")
            print()
            return True
        else:
            print("❌ Failed to get Gmail profile")
            return False
    
    except FileNotFoundError as e:
        print()
        print("❌ Gmail Credentials Not Found!")
        print()
        print("Please set up Gmail OAuth:")
        print("  1. Go to Google Cloud Console")
        print("  2. Create OAuth 2.0 credentials")
        print("  3. Download credentials.json")
        print("  4. Place in: app/config/credentials.json")
        print()
        print(f"Error: {e}")
        return False
    
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  • Check credentials.json exists")
        print("  • Verify Gmail API is enabled")
        print("  • Check internet connection")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)