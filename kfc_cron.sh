#!/bin/bash
#
# KFC Auto-Order Cron Script
#
# Setup Instructions:
# 1. Make this script executable: chmod +x kfc_cron.sh
# 2. Edit paths below to match your installation
# 3. Add to crontab: crontab -e
# 4. Add line: 30 10 * * * /absolute/path/to/kfc_cron.sh
#
# This will run daily at 10:30 AM

# CONFIGURATION - UPDATE THESE PATHS
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="/usr/bin/python3"  # Or: /usr/bin/env python3
LOG_FILE="$SCRIPT_DIR/cron.log"

# Change to script directory
cd "$SCRIPT_DIR" || exit 1

# Log start time
echo "==================================" >> "$LOG_FILE"
echo "KFC Auto-Order Cron Job Started" >> "$LOG_FILE"
echo "Time: $(date)" >> "$LOG_FILE"
echo "==================================" >> "$LOG_FILE"

# Activate virtual environment if exists
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "Activating virtual environment..." >> "$LOG_FILE"
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Run the automation script
echo "Running kfc_auto_order.py..." >> "$LOG_FILE"
$PYTHON_BIN "$SCRIPT_DIR/kfc_auto_order.py" >> "$LOG_FILE" 2>&1

# Log exit status
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Order completed successfully" >> "$LOG_FILE"
else
    echo "✗ Order failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "==================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit $EXIT_CODE
