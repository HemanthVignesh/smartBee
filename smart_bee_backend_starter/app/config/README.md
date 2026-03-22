# Configuration Directory

## Required Files

Place your Gmail OAuth credentials here:

1. **credentials.json** - Download from Google Cloud Console
   - DO NOT commit to git
   - Required for Gmail API access

2. **token.pickle** - Auto-generated after first OAuth flow
   - DO NOT commit to git
   - Contains your authentication token

## Setup Instructions

1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials.json
6. Place it in this directory

## Security

These files are in `.gitignore` and will NOT be committed to version control.