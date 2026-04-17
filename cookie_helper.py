#!/usr/bin/env python3
"""
KFC Cookie Helper
Opens KFC site in browser for manual login, then exports cookies to cookies.json
"""

import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install -r requirements.txt && playwright install chromium")
    sys.exit(1)


async def export_cookies():
    """Open KFC site, let user login, then export cookies."""
    print("=" * 70)
    print("KFC Cookie Exporter")
    print("=" * 70)
    print()
    print("This tool will:")
    print("  1. Open KFC H5 site (m.kfc.com.cn) in a browser")
    print("  2. Let YOU log in manually with your phone/password")
    print("  3. Export your session cookies to cookies.json")
    print()
    print("Instructions:")
    print("  - A browser window will open")
    print("  - Log in to your KFC account")
    print("  - After successful login, press ENTER in this terminal")
    print("  - Cookies will be saved to cookies.json")
    print()
    print("=" * 70)
    input("Press ENTER to open browser...")

    async with async_playwright() as p:
        print("\nLaunching browser...")

        # Launch in headed mode so user can interact
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )

        context = await browser.new_context(
            viewport={"width": 375, "height": 812},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        )

        page = await context.new_page()

        # Navigate to KFC
        print("Opening m.kfc.com.cn...")
        await page.goto("https://m.kfc.com.cn", wait_until="networkidle")

        print()
        print("=" * 70)
        print("BROWSER OPENED")
        print("=" * 70)
        print()
        print("Please complete these steps in the browser:")
        print("  1. Click login/sign in button (登录)")
        print("  2. Enter your phone number")
        print("  3. Enter your password or SMS code")
        print("  4. Complete login")
        print("  5. Verify you see your account info")
        print()
        print("After you're successfully logged in, come back here and press ENTER")
        print("=" * 70)

        # Wait for user to complete login
        input("\nPress ENTER after you've logged in...")

        # Get cookies from the browser context
        cookies = await context.cookies()

        # Save cookies to file
        cookie_file = Path("cookies.json")
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"\n✓ Success! Saved {len(cookies)} cookies to {cookie_file}")
        print()
        print("Cookie details:")
        for cookie in cookies:
            print(f"  - {cookie['name']} (domain: {cookie['domain']})")

        print()
        print("=" * 70)
        print("You can now use kfc_auto_order.py with these cookies!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Edit config.json with your preferences")
        print("  2. Test with: python kfc_auto_order.py --dry-run")
        print("  3. Run for real: python kfc_auto_order.py")
        print()

        # Close browser
        await browser.close()
        print("Browser closed. Goodbye!")


def main():
    try:
        asyncio.run(export_cookies())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
