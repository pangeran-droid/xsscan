<div align="center">

# XSS Scanner (Playwright-Based)

A modern **Playwright-based XSS Scanner** designed for **bug bounty hunters**
and **security researchers**.

This tool performs **real browser–based XSS detection** through crawling,
URL parameter injection, and smart form submission.

This Playwright-based XSS scanner is designed for bug bounty hunters and penetration testers
to detect real-world executed cross-site scripting vulnerabilities.

> Focused on **XSS that is actually EXECUTED**, not just reflected strings.

</div>

---

<div align="center">

<img src="asset/example.gif" width="800">

<sub>Example XSS detection result</sub>

</div>

---

## Features

- Real browser execution (Playwright + Chromium)
- URL parameter XSS scanning
- Multi-form XSS scanning
- Smart form submission (auto bypass required / validation fields)
- JavaScript dialog detection (`alert`, `prompt`)
- Recursive crawling (same domain only)
- Auto XSS report generation (`.ndjson`)
- Clean & readable CLI colored output
- Marker-based validation to avoid false positives

---

## How It Works (High Level)

1. Crawl target website (same domain)
2. Detect URL parameters
3. Inject XSS payloads
4. Detect JavaScript dialogs (`alert`, `prompt`)
5. Parse & submit all forms intelligently
6. Fallback to raw form submission if smart submit fails
7. Save **confirmed executed XSS** to report file

> Only **EXECUTED XSS** will be reported.

---

## Requirements

- Python **3.8+**
- Playwright
- Chromium browser (installed via Playwright)

---

## Installation

```bash
git clone https://github.com/pangeran-droid/XSS-Scanner-Pro.git
cd XSS-Scanner-Pro
pip install -r requirements.txt
playwright install chromium
```

---

## Usage

```bash
python3 main.py -u https://target.com
```

### Options

| Flag | Description | Default  |
|:----:|-------------|----------|
| `-u` | Target URL  | required |
| `-d` | Crawl depth | 2        |

---

## Payload Examples

Each scan generates a unique marker using a random numeric value.  
The marker is injected into XSS payloads and verified upon execution.

```text
"><svg/onload=alert({marker})>
"><img src=x onerror=prompt({marker})>
<script>alert({marker})</script>
```

---

## Output Example

```bash
[*] Crawling (0) → https://target.com
[*] Form #1 → /search (GET)
[🔥 XSS] EXECUTED at https://target.com/search?q=...
```

---

## Report File

Confirmed XSS findings will be saved automatically to:

```bash
xss_report.ndjson
```

### Example entry:

```bash
{"url":"https://target.com","marker":"1337123456","message":"1337123456"}
```

---

## ⚠️ Disclaimer

> This tool is created **for educational purposes and authorized security testing only**.  
> ❌ Do **NOT** use this tool against targets without **explicit permission**.  
>
> The author is **not responsible** for any misuse or illegal activities.

