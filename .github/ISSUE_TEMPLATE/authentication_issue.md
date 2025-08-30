---
name: Authentication Issue
about: Report problems with Spotify or YouTube Music authentication
title: '[AUTH] '
labels: authentication, help wanted
assignees: ''
---

**Authentication service**
Which service are you having trouble with?
- [ ] Spotify authentication
- [ ] YouTube Music authentication
- [ ] Both

**Describe the authentication issue**
A clear and concise description of the authentication problem.

**Steps you've already tried**
- [ ] Verified Spotify Client ID and Client Secret
- [ ] Added correct redirect URI in Spotify app settings
- [ ] Ran `ytmusicapi oauth` for YouTube Music
- [ ] Checked that YouTube Data API is enabled
- [ ] Added test user to OAuth consent screen
- [ ] Regenerated oauth.json file
- [ ] Checked file permissions

**Error message**
```
Paste the complete error message here
```

**Configuration details**
- Spotify app settings (Client ID only, never share Client Secret):
  - Client ID: [first 8 characters only, e.g. ab12cd34...]
  - Redirect URI: [e.g. http://localhost:8888/callback]
- YouTube Music setup:
  - Google Cloud project has YouTube Data API enabled: [Yes/No/Unknown]
  - OAuth consent screen configured: [Yes/No/Unknown]
  - Test user added: [Yes/No/Unknown]

**oauth.json file format (remove sensitive values)**
```json
{
  "scope": "https://www.googleapis.com/auth/youtube",
  "token_type": "Bearer",
  "access_token": "[REMOVED]",
  "refresh_token": "[REMOVED]", 
  "expires_at": 1234567890,
  "expires_in": 3599
}
```

**Environment:**
- OS: [e.g. macOS 12, Windows 11, Ubuntu 20.04]
- Python version: [e.g. 3.13]
- Browser used for OAuth: [e.g. Chrome, Firefox, Safari]

**Additional context**
- Is this your first time setting up the authentication?
- Did authentication work before and suddenly stop?
- Any recent changes to your Google or Spotify accounts?