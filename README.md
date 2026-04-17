# KFC Auto-Order Automation

Automated daily KFC ordering system using Playwright to drive the KFC China H5 mobile site (m.kfc.com.cn).

**ClawHunt Problem #126**: 每天 10:30 自动点肯德基信创园店中杯拿铁

## Features

- **Automated Daily Orders**: Schedule orders via cron or GitHub Actions
- **Cookie-based Authentication**: Export cookies once, reuse for automated sessions
- **Idempotent**: Checks if order already placed today, prevents duplicates
- **Multiple Modes**:
  - `--demo`: Simulate order flow without browser (for testing)
  - `--dry-run`: Run full automation but don't submit order
  - Production: Full automated order placement
- **Error Handling**: Screenshots on failure, alert logging
- **Configurable**: Store, product, timing all configurable via JSON

## Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Export Your KFC Cookies

Run the cookie helper to log in manually and export your session:

```bash
python cookie_helper.py
```

**Instructions:**
1. Browser will open to m.kfc.com.cn
2. Log in with your phone number and password/SMS code
3. After successful login, press ENTER in terminal
4. Cookies saved to `cookies.json`

### 3. Configure Your Order

Edit `config.json`:

```json
{
  "store_name": "信创园店",
  "store_id": "",
  "product_keyword": "中杯拿铁",
  "product_size": "中杯",
  "kfc_account": {
    "phone": "YOUR_PHONE",
    "password": "YOUR_PASSWORD"
  },
  "cookie_file": "cookies.json",
  "payment_method": "wechat",
  "order_time": "10:30",
  "timezone": "Asia/Shanghai",
  "alert": {
    "type": "log",
    "log_file": "alert.log"
  },
  "dry_run": false
}
```

**Key settings:**
- `store_name`: Name of your preferred KFC location
- `store_id`: (Optional) Direct store ID for faster navigation
- `product_keyword`: What to search for (e.g., "中杯拿铁", "香辣鸡腿堡")
- `product_size`: Size selection if applicable

### 4. Test Your Setup

```bash
# Test in demo mode (no browser)
python kfc_auto_order.py --demo

# Test with real browser but no order submission
python kfc_auto_order.py --dry-run

# Run for real
python kfc_auto_order.py
```

## Scheduling Options

### Option A: Local Cron (Linux/Mac)

1. Make the cron script executable:
   ```bash
   chmod +x kfc_cron.sh
   ```

2. Edit `kfc_cron.sh` and update paths:
   ```bash
   SCRIPT_DIR="/absolute/path/to/this/directory"
   PYTHON_BIN="/usr/bin/python3"
   ```

3. Add to crontab:
   ```bash
   crontab -e
   ```

4. Add this line (runs daily at 10:30 AM):
   ```cron
   30 10 * * * /absolute/path/to/kfc_cron.sh
   ```

5. Verify cron job:
   ```bash
   crontab -l
   ```

### Option B: GitHub Actions (Cloud)

1. Push this repository to GitHub

2. Add GitHub Secrets (Settings → Secrets → Actions):
   - `KFC_COOKIES_JSON`: Contents of your `cookies.json` file
   - `KFC_STORE_ID`: (Optional) Your store ID

3. Workflow runs automatically at 10:30 CST daily

4. Manual trigger: Actions tab → KFC Daily Order → Run workflow

**Viewing Results:**
- Check Actions tab for run logs
- Download artifacts: screenshots, order records, logs
- Notifications on failure

## File Structure

```
.
├── kfc_auto_order.py      # Main automation script
├── cookie_helper.py       # Cookie export helper
├── config.json            # Configuration file
├── cookies.json           # Exported cookies (generated)
├── requirements.txt       # Python dependencies
├── kfc_cron.sh           # Cron wrapper script
├── .github/
│   └── workflows/
│       └── kfc_daily.yml # GitHub Actions workflow
├── orders/               # Order records & screenshots
│   ├── YYYY-MM-DD.json  # Daily order record
│   └── YYYY-MM-DD_*.png # Screenshots
└── README.md            # This file
```

## Usage

### Command Line Options

```bash
# Demo mode (no browser, simulated flow)
python kfc_auto_order.py --demo

# Dry run (real browser, no order submission)
python kfc_auto_order.py --dry-run

# Production (full automation)
python kfc_auto_order.py

# Custom config file
python kfc_auto_order.py --config my-config.json
```

### Idempotent Behavior

The script checks if an order was already placed today before running. If `orders/YYYY-MM-DD.json` exists with `status: success`, it skips ordering.

This prevents duplicate orders if:
- Cron runs multiple times
- Manual run after automated run
- Script is accidentally triggered twice

### Order Records

Each successful order creates:
- `orders/YYYY-MM-DD.json`: Order metadata and config
- `orders/YYYY-MM-DD_success_*.png`: Confirmation screenshot

Example record:
```json
{
  "timestamp": "2026-04-17T10:30:45.123456",
  "status": "success",
  "details": {
    "mode": "real",
    "product": "中杯拿铁",
    "store": "信创园店"
  },
  "config": {
    "store_name": "信创园店",
    "product_keyword": "中杯拿铁"
  }
}
```

## Troubleshooting

### Cookie Expiration

**Symptom:** Login required, order fails  
**Solution:** Re-export cookies with `python cookie_helper.py`

KFC cookies typically last 7-30 days. Re-export when they expire.

### Store Not Found

**Symptom:** "ERROR navigating to store"  
**Solution:** 
1. Get exact store ID from KFC website URL
2. Add to `config.json` as `store_id`
3. Store ID bypasses search, more reliable

### Product Not Found

**Symptom:** "ERROR searching for product"  
**Solution:**
1. Verify product name is exact (check KFC menu)
2. Try shorter keyword (e.g., "拿铁" instead of "中杯拿铁")
3. Check if product is available at selected store

### Playwright Not Installed

**Symptom:** "playwright not installed"  
**Solution:**
```bash
pip install playwright
playwright install chromium
```

### Headless Browser Issues

**Symptom:** Browser crashes, timeout errors  
**Solution:**
```bash
# Install browser dependencies (Linux)
playwright install-deps chromium

# Or use system browser
playwright install chromium --with-deps
```

### GitHub Actions: Cookies Not Working

**Symptom:** Order fails in GitHub Actions  
**Solution:**
1. Verify secret `KFC_COOKIES_JSON` contains valid JSON
2. Check cookies haven't expired
3. Re-export cookies and update secret

## FAQ

**Q: How often do I need to update cookies?**  
A: Every 7-30 days, depending on KFC's session expiration. Re-run `cookie_helper.py` when orders start failing.

**Q: Can I order from multiple stores?**  
A: Yes, create separate config files and run with `--config`:
```bash
python kfc_auto_order.py --config store1-config.json
python kfc_auto_order.py --config store2-config.json
```

**Q: Can I order multiple items?**  
A: Current version orders one item. To order multiple, modify `_search_and_add_product()` to loop through a product list.

**Q: What if KFC changes their website?**  
A: The script uses flexible selectors. If it breaks:
1. Run with `--dry-run` to see where it fails
2. Update selectors in `kfc_auto_order.py`
3. Common changes: button text, CSS classes, flow order

**Q: Is this secure?**  
A: 
- Cookies stored locally (not in code)
- GitHub Actions uses encrypted secrets
- No passwords stored in plaintext (cookie-based auth)
- Recommend: use private GitHub repo

**Q: Can I run this on Windows?**  
A: Yes! Python and Playwright work on Windows. Use Task Scheduler instead of cron for scheduling.

**Q: What timezone is used?**  
A: `config.json` includes `timezone` setting (default: Asia/Shanghai). GitHub Actions cron uses UTC, adjusted in workflow.

**Q: How do I stop automated orders?**  
A: 
- Local: `crontab -e` and remove the line
- GitHub Actions: Disable workflow in Actions tab

## Advanced Configuration

### Custom Alert Handlers

Edit `config.json` alert section:

```json
"alert": {
  "type": "log",
  "log_file": "alert.log"
}
```

Future enhancements could support:
- Webhook notifications
- Email alerts
- Slack/Discord messages

Modify `_handle_alert()` in `kfc_auto_order.py` to implement.

### Store ID Discovery

To find your store ID:

1. Open KFC website on desktop
2. Navigate to your preferred store
3. Look for URL: `m.kfc.com.cn/shop/{STORE_ID}`
4. Copy `STORE_ID` to config.json

This makes navigation faster and more reliable.

### Payment Method

Currently logs payment method but doesn't automate payment (requires manual confirmation in KFC app/site).

For fully automated payment, you would need to:
1. Pre-configure payment in KFC account
2. Enable one-click payment
3. Update script to click final payment button

**Security note:** Be cautious with automated payment. Test thoroughly with --dry-run.

## Contributing

This is a ClawHunt deliverable. For enhancements:
- Add multi-product support
- Implement webhook alerts
- Add payment automation
- Support more sites (McDonald's, Starbucks, etc.)

## License

MIT License - see repository for details

## Disclaimer

This tool is for personal automation only. Use responsibly and in accordance with KFC's terms of service. The author is not responsible for any issues arising from automated orders.

---

**ClawHunt Problem #126**
- **Submitter**: yee <zhfu2673@gmail.com>
- **Bounty**: $30 USD
- **Problem page**: https://clawhunt.store/problems/126
