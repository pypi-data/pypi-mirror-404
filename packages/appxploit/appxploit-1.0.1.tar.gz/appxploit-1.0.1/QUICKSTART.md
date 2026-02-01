# AppXploit Quick Start Guide

## Installation

```bash
# Install from PyPI (recommended)
pip install appxploit

# Or install from source
git clone https://github.com/letchupkt/appxploit.git
cd appxploit
pip install -e .
```

## Basic Usage

### Analyze an APK
```bash
appxploit target.apk
```

This will:
1. Extract and decompile the APK
2. Analyze for vulnerabilities
3. Generate `target_report.md` in current directory

### Specify Output Location
```bash
appxploit target.apk -o /path/to/report.md
```

### Verbose Mode (Recommended)
```bash
appxploit target.apk -v
```

Shows detailed progress and findings count:
```
[*] Advanced vulnerabilities found: 12
    - Client-side admin check
    - Hardcoded encryption key
    - JavaScript-enabled WebView
```

### Quick Scan
```bash
appxploit target.apk --quick
```

Skips deep analysis for faster results.

### JSON Output
```bash
appxploit target.apk -f json -o report.json
```

## Understanding the Report

### Report Sections

1. **Executive Summary** - High-level overview
2. **Exploit Chains** - Multi-step attack paths
3. **Vulnerabilities** - Individual security issues
4. **API Endpoints** - Discovered endpoints
5. **Secrets** - Hardcoded credentials/keys
6. **App Intelligence** - App classification and risk

### Severity Levels

- **Critical** (Score ≥ 70) - Immediate exploitation, high impact
- **High** (Score ≥ 50) - Exploitable with moderate effort
- **Medium** (Score ≥ 30) - Requires specific conditions
- **Low** (Score ≥ 10) - Limited impact or difficult to exploit
- **Info** (Score < 10) - Informational only

### Exploit Chain Impact Types

- **Account Takeover** - Full user account compromise
- **Data Exfiltration** - Sensitive data theft
- **Privilege Escalation** - Unauthorized access elevation
- **Payment Abuse** - Financial fraud

## Advanced Features

### What AppXploit Detects

#### Authentication & Session Issues
- Client-side authorization checks
- Hardcoded auth bypass flags
- Session token storage issues

#### Access Control (IDOR)
- User IDs in API endpoints
- Admin endpoint references
- Unprotected resources

#### Cryptography
- Weak algorithms (MD5, SHA1, DES)
- ECB mode encryption
- Hardcoded encryption keys
- Base64 as "encryption"

#### WebView Security
- JavaScript-enabled WebViews
- JavaScript interface misuse
- Insecure file access
- HTTP content loading

#### Data Storage
- Sensitive data in SharedPreferences
- Credentials in logs
- World-readable files

#### Component Security
- Exported components abuse
- Mutable PendingIntents
- Unprotected broadcasts

#### Payment & Financial
- Client-side price calculations
- Payment bypass flags

#### OTP & Verification
- Client-side OTP validation
- Hardcoded OTPs/PINs

## Real-World Examples

### Example 1: Banking App Analysis
```bash
appxploit banking_app.apk -v -o banking_report.md
```

**Typical Findings:**
- Client-side OTP validation (Critical)
- Hardcoded API keys (Critical)
- Weak encryption (High)
- Backup enabled (Medium)

**Exploit Chain:**
```
Weak Crypto + Backup → Credential Decryption
CVSS: 7.8 | Impact: Data Exfiltration
```

### Example 2: Social Media App
```bash
appxploit social_app.apk -v
```

**Typical Findings:**
- User IDs in endpoints (High)
- Client-side admin check (Critical)
- Exported activities (Medium)

**Exploit Chain:**
```
Client Auth Bypass + IDOR → Horizontal Privilege Escalation
CVSS: 8.2 | Impact: Privilege Escalation
```

### Example 3: E-commerce App
```bash
appxploit shop_app.apk -v
```

**Typical Findings:**
- Client-side price calculation (Critical)
- Payment bypass flag (Critical)
- Hardcoded merchant keys (Critical)

## Tips for Bug Bounty Hunters

### 1. Always Use Verbose Mode
```bash
appxploit target.apk -v
```
Shows advanced vulnerability counts and helps you understand what was found.

### 2. Focus on Exploit Chains First
Exploit chains are multi-step attacks with higher impact. Start here for maximum bounty potential.

### 3. Verify Findings
AppXploit provides file paths and line numbers. Always verify findings manually before reporting.

### 4. Check Confidence Scores
Higher confidence = lower false positive rate. Focus on findings with:
- Direct code evidence
- Multiple occurrences
- Core functionality involvement

### 5. Understand Business Impact
Use the "business_impact" field in exploit chains to explain non-technical impact to program owners.

## Troubleshooting

### Java Not Found
```bash
# Install Java 8 or higher
sudo apt install openjdk-11-jdk  # Linux
brew install openjdk@11          # macOS
```

### APK Extraction Failed
- Ensure APK is not corrupted
- Check disk space
- Try with `--verbose` for details

### No Vulnerabilities Found
- Some apps are well-secured
- Try different APK versions
- Check if app uses native code (not analyzed)

### Report Not Generated
- Check output path permissions
- Ensure sufficient disk space
- Review verbose output for errors

## Best Practices

### 1. Organize Your Work
```bash
mkdir -p ~/bug-bounty/target-app
cd ~/bug-bounty/target-app
appxploit target.apk -v
```

### 2. Keep AppXploit Updated
```bash
pip install --upgrade appxploit
```

AppXploit checks for updates automatically and notifies you.

### 3. Use Version Control for Reports
```bash
git init
appxploit target_v1.apk -o v1_report.md
git add v1_report.md
git commit -m "Initial analysis"

# Later
appxploit target_v2.apk -o v2_report.md
git diff v1_report.md v2_report.md
```

### 4. Combine with Other Tools
```bash
# Extract APK first
appxploit target.apk -v

# Then use specialized tools
mobsf target.apk           # MobSF for additional checks
frida target.apk           # Dynamic analysis
objection explore          # Runtime manipulation
```

## Recommended Test APKs

Practice on intentionally vulnerable apps:

1. **DIVA** - Damn Insecure and Vulnerable App
2. **InsecureBankv2** - Banking app vulnerabilities
3. **AndroGoat** - OWASP test app
4. **InjuredAndroid** - CTF-style challenges

```bash
# Example
wget https://github.com/payatu/diva-android/releases/download/v1.0/diva-beta.apk
appxploit diva-beta.apk -v
```

## Getting Help

### Command Help
```bash
appxploit --help
```

### Verbose Output
```bash
appxploit target.apk -v
```

### GitHub Issues
Report bugs or request features at: https://github.com/letchupkt/appxploit/issues

## Next Steps

1. ✅ Install AppXploit
2. ✅ Analyze a test APK
3. ✅ Review the generated report
4. ✅ Understand exploit chains
5. ✅ Verify findings manually
6. ✅ Start hunting on real targets!

---

**Happy Hunting! 🎯**

Built with ❤️ by LAKSHMIKANTHAN K (letchupkt)
