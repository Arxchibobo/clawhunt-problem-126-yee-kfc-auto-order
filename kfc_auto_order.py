#!/usr/bin/env python3
"""
KFC Auto-Order Automation Script
Automates daily KFC orders via m.kfc.com.cn H5 site using Playwright.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: playwright not installed. Run: pip install -r requirements.txt && playwright install chromium")
    sys.exit(1)


class KFCAutoOrder:
    def __init__(self, config_path: str = "config.json", demo_mode: bool = False):
        self.config = self._load_config(config_path)
        self.demo_mode = demo_mode
        self.dry_run = self.config.get("dry_run", False) or demo_mode
        self.log_messages = []

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.log(f"ERROR: Config file {config_path} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.log(f"ERROR: Invalid JSON in config file: {e}")
            sys.exit(1)

    def log(self, message: str):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        self.log_messages.append(log_line)

    def _get_order_record_file(self) -> Path:
        """Get path to today's order record file."""
        today = datetime.now().strftime("%Y-%m-%d")
        orders_dir = Path("orders")
        orders_dir.mkdir(exist_ok=True)
        return orders_dir / f"{today}.json"

    def _check_already_ordered_today(self) -> bool:
        """Check if order already placed today (idempotent check)."""
        record_file = self._get_order_record_file()
        if record_file.exists():
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    if record.get("status") == "success":
                        self.log(f"Order already placed today at {record.get('timestamp')}")
                        return True
            except (json.JSONDecodeError, KeyError):
                pass
        return False

    def _mark_order_complete(self, success: bool, details: Dict[str, Any]):
        """Mark order as complete for today."""
        record_file = self._get_order_record_file()
        record = {
            "timestamp": datetime.now().isoformat(),
            "status": "success" if success else "failed",
            "details": details,
            "config": {
                "store_name": self.config.get("store_name"),
                "product_keyword": self.config.get("product_keyword")
            }
        }
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    async def _load_cookies(self, context) -> bool:
        """Load saved cookies into browser context."""
        cookie_file = self.config.get("cookie_file", "cookies.json")
        if not os.path.exists(cookie_file):
            self.log(f"WARNING: Cookie file {cookie_file} not found, will need to login")
            return False

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            self.log(f"Loaded {len(cookies)} cookies from {cookie_file}")
            return True
        except Exception as e:
            self.log(f"ERROR loading cookies: {e}")
            return False

    async def _navigate_to_store(self, page: Page) -> bool:
        """Navigate to the configured store."""
        store_name = self.config.get("store_name")
        store_id = self.config.get("store_id")

        self.log(f"Navigating to store: {store_name}")

        try:
            # Go to KFC home
            await page.goto("https://m.kfc.com.cn", wait_until="networkidle", timeout=30000)
            self.log("Loaded KFC home page")

            # Click store selector
            await page.wait_for_selector("text=/选择餐厅|切换门店/i", timeout=10000)
            await page.click("text=/选择餐厅|切换门店/i")
            self.log("Opened store selector")

            # If store_id is provided, use direct URL
            if store_id:
                await page.goto(f"https://m.kfc.com.cn/shop/{store_id}", timeout=30000)
                self.log(f"Navigated directly to store ID: {store_id}")
            else:
                # Search for store by name
                await page.wait_for_selector("input[placeholder*='搜索']", timeout=10000)
                await page.fill("input[placeholder*='搜索']", store_name)
                await page.press("input[placeholder*='搜索']", "Enter")
                self.log(f"Searched for store: {store_name}")

                # Click first result
                await page.wait_for_selector(".store-item, .shop-item", timeout=10000)
                await page.click(".store-item, .shop-item")
                self.log("Selected store from search results")

            await page.wait_for_timeout(2000)
            return True

        except PlaywrightTimeout as e:
            self.log(f"ERROR: Timeout navigating to store: {e}")
            return False
        except Exception as e:
            self.log(f"ERROR navigating to store: {e}")
            return False

    async def _search_and_add_product(self, page: Page) -> bool:
        """Search for product and add to cart."""
        product_keyword = self.config.get("product_keyword")

        self.log(f"Searching for product: {product_keyword}")

        try:
            # Click search icon
            await page.wait_for_selector("text=/搜索|search/i, .search-icon", timeout=10000)
            await page.click("text=/搜索|search/i, .search-icon")

            # Type product name
            await page.wait_for_selector("input[type='search'], input[placeholder*='搜索']", timeout=10000)
            await page.fill("input[type='search'], input[placeholder*='搜索']", product_keyword)
            await page.press("input[type='search'], input[placeholder*='搜索']", "Enter")
            self.log(f"Searched for: {product_keyword}")

            # Wait for results
            await page.wait_for_selector(".product-item, .goods-item", timeout=10000)
            self.log("Product search results loaded")

            # Click first matching product
            await page.click(".product-item, .goods-item")
            self.log("Selected product")

            # Handle size/spec selection if needed
            product_size = self.config.get("product_size")
            if product_size:
                size_selector = f"text=/{product_size}/i"
                try:
                    await page.wait_for_selector(size_selector, timeout=5000)
                    await page.click(size_selector)
                    self.log(f"Selected size: {product_size}")
                except:
                    self.log(f"Size selector not found or not needed: {product_size}")

            # Click add to cart button
            await page.wait_for_selector("text=/加入购物车|立即购买|确定/i", timeout=10000)
            await page.click("text=/加入购物车|立即购买|确定/i")
            self.log("Added product to cart")

            await page.wait_for_timeout(2000)
            return True

        except PlaywrightTimeout as e:
            self.log(f"ERROR: Timeout searching for product: {e}")
            return False
        except Exception as e:
            self.log(f"ERROR searching for product: {e}")
            return False

    async def _checkout_order(self, page: Page) -> bool:
        """Navigate to cart and checkout."""
        self.log("Proceeding to checkout")

        try:
            # Go to cart
            await page.wait_for_selector("text=/购物车|结算/i, .cart-icon", timeout=10000)
            await page.click("text=/购物车|结算/i, .cart-icon")
            self.log("Opened shopping cart")

            await page.wait_for_timeout(2000)

            # Click checkout/submit button
            if self.dry_run:
                self.log("DRY RUN: Would click checkout button but skipping actual submission")
                # Take screenshot to verify we reached checkout
                screenshot_path = self._get_screenshot_path("dry-run")
                await page.screenshot(path=screenshot_path)
                self.log(f"Saved dry-run screenshot: {screenshot_path}")
                return True
            else:
                await page.wait_for_selector("text=/去结算|提交订单|立即支付/i", timeout=10000)
                await page.click("text=/去结算|提交订单|立即支付/i")
                self.log("Clicked checkout button")

                # Wait for order confirmation
                await page.wait_for_selector("text=/订单提交成功|支付成功/i", timeout=30000)
                self.log("Order submitted successfully!")

                # Take success screenshot
                screenshot_path = self._get_screenshot_path("success")
                await page.screenshot(path=screenshot_path)
                self.log(f"Saved order confirmation screenshot: {screenshot_path}")

                return True

        except PlaywrightTimeout as e:
            self.log(f"ERROR: Timeout during checkout: {e}")
            return False
        except Exception as e:
            self.log(f"ERROR during checkout: {e}")
            return False

    def _get_screenshot_path(self, prefix: str) -> str:
        """Get screenshot path with timestamp."""
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%H%M%S")
        orders_dir = Path("orders")
        orders_dir.mkdir(exist_ok=True)
        return str(orders_dir / f"{today}_{prefix}_{timestamp}.png")

    async def _handle_alert(self, message: str):
        """Handle alert notification."""
        alert_config = self.config.get("alert", {})
        alert_type = alert_config.get("type", "log")

        if alert_type == "log":
            log_file = alert_config.get("log_file", "alert.log")
            timestamp = datetime.now().isoformat()
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
            self.log(f"Alert logged to {log_file}: {message}")

    async def run_real_order(self) -> bool:
        """Run the real order automation with Playwright."""
        self.log("Starting KFC auto-order (real mode)")

        # Check if already ordered today
        if self._check_already_ordered_today():
            self.log("Skipping order - already completed today (idempotent check)")
            return True

        async with async_playwright() as p:
            browser = None
            try:
                # Launch browser
                self.log("Launching browser...")
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 375, "height": 812},
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
                )
                page = await context.new_page()

                # Load cookies
                await self._load_cookies(context)

                # Execute order flow
                if not await self._navigate_to_store(page):
                    raise Exception("Failed to navigate to store")

                if not await self._search_and_add_product(page):
                    raise Exception("Failed to add product to cart")

                if not await self._checkout_order(page):
                    raise Exception("Failed to checkout")

                # Mark success
                self._mark_order_complete(True, {
                    "mode": "dry_run" if self.dry_run else "real",
                    "product": self.config.get("product_keyword"),
                    "store": self.config.get("store_name")
                })

                self.log("Order completed successfully!")
                return True

            except Exception as e:
                self.log(f"ERROR: Order failed: {e}")

                # Take error screenshot
                try:
                    if browser:
                        page = (await browser.contexts)[0].pages[0]
                        screenshot_path = self._get_screenshot_path("error")
                        await page.screenshot(path=screenshot_path)
                        self.log(f"Saved error screenshot: {screenshot_path}")
                except:
                    pass

                # Send alert
                await self._handle_alert(f"Order failed: {e}")

                # Mark failure
                self._mark_order_complete(False, {"error": str(e)})

                return False

            finally:
                if browser:
                    await browser.close()
                    self.log("Browser closed")

    def run_demo_order(self) -> bool:
        """Run a simulated demo order (no browser, fake data)."""
        self.log("Starting KFC auto-order (DEMO mode)")
        self.log("=" * 60)

        # Check if already ordered today
        if self._check_already_ordered_today():
            self.log("Skipping order - already completed today (idempotent check)")
            return True

        # Simulate order flow
        self.log(f"DEMO: Loading configuration from config.json")
        self.log(f"DEMO: Store: {self.config.get('store_name')}")
        self.log(f"DEMO: Product: {self.config.get('product_keyword')} ({self.config.get('product_size')})")
        self.log(f"DEMO: Payment: {self.config.get('payment_method')}")

        self.log("DEMO: Would launch headless Chromium browser")
        self.log("DEMO: Would load cookies from cookies.json")
        self.log("DEMO: Would navigate to https://m.kfc.com.cn")

        self.log(f"DEMO: Would click store selector and search for '{self.config.get('store_name')}'")
        self.log("DEMO: Would select first matching store")

        self.log(f"DEMO: Would search for product '{self.config.get('product_keyword')}'")
        self.log("DEMO: Would click first matching product")

        product_size = self.config.get('product_size')
        if product_size:
            self.log(f"DEMO: Would select size '{product_size}'")

        self.log("DEMO: Would click '加入购物车' (Add to Cart)")
        self.log("DEMO: Would navigate to shopping cart")
        self.log("DEMO: Would click '去结算' (Checkout)")

        if self.dry_run:
            self.log("DEMO: DRY RUN mode - would NOT submit order")
            self.log("DEMO: Would save screenshot to orders/YYYY-MM-DD_dry-run_HHMMSS.png")
        else:
            self.log("DEMO: Would click '提交订单' (Submit Order)")
            self.log("DEMO: Would wait for order confirmation")
            self.log("DEMO: Would save screenshot to orders/YYYY-MM-DD_success_HHMMSS.png")

        # Create demo order record
        self._mark_order_complete(True, {
            "mode": "demo",
            "product": self.config.get("product_keyword"),
            "store": self.config.get("store_name")
        })

        self.log("=" * 60)
        self.log("DEMO: Order simulation completed successfully!")
        self.log(f"DEMO: Order record saved to {self._get_order_record_file()}")

        return True

    def run(self) -> bool:
        """Main entry point."""
        try:
            if self.demo_mode:
                return self.run_demo_order()
            else:
                return asyncio.run(self.run_real_order())
        except KeyboardInterrupt:
            self.log("Interrupted by user")
            return False
        except Exception as e:
            self.log(f"FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(
        description="KFC Auto-Order Automation Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kfc_auto_order.py --demo          # Run demo mode (no browser)
  python kfc_auto_order.py --dry-run       # Test run (no order submission)
  python kfc_auto_order.py                 # Real order (production)
        """
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config file (default: config.json)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode (simulate without browser)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run but don't submit order (test mode)"
    )

    args = parser.parse_args()

    # Create automation instance
    automation = KFCAutoOrder(config_path=args.config, demo_mode=args.demo)

    # Override dry_run from command line
    if args.dry_run:
        automation.dry_run = True

    # Run automation
    success = automation.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
