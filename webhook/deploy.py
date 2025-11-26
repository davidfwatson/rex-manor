#!/usr/bin/env python3
"""
Webhook endpoint for deploying Rex Manor Hugo site.
Listens for POST requests from GitHub Actions and triggers a deployment.
"""

import os
import sys
import hmac
import hashlib
import subprocess
import logging
from flask import Flask, request, jsonify

# Configuration
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'change-me-in-production')
SITE_PATH = '/home/david/webserver/rex-manor'
LOG_FILE = '/home/david/webserver/rex-manor/webhook/deploy.log'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def verify_signature(payload, signature):
    """Verify the webhook signature."""
    if not signature:
        return False

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f'sha256={expected_signature}', signature)


def run_command(command, cwd=SITE_PATH):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return False, "", "Command timed out"
    except Exception as e:
        logger.error(f"Error running command {command}: {e}")
        return False, "", str(e)


def deploy_site():
    """Deploy the site by pulling changes and rebuilding."""
    logger.info("Starting deployment...")

    # Pull latest changes
    logger.info("Pulling latest changes from git...")
    success, stdout, stderr = run_command('git pull origin main')
    if not success:
        logger.error(f"Git pull failed: {stderr}")
        return False, f"Git pull failed: {stderr}"
    logger.info(f"Git pull output: {stdout}")

    # Build the site
    logger.info("Building Hugo site...")
    success, stdout, stderr = run_command('hugo --minify')
    if not success:
        logger.error(f"Hugo build failed: {stderr}")
        return False, f"Hugo build failed: {stderr}"
    logger.info(f"Hugo build output: {stdout}")

    logger.info("Deployment completed successfully!")
    return True, "Deployment successful"


@app.route('/deploy', methods=['POST'])
def webhook_handler():
    """Handle incoming webhook requests."""
    # Verify signature if provided
    signature = request.headers.get('X-Hub-Signature-256')
    if signature:
        if not verify_signature(request.data, signature):
            logger.warning("Invalid signature received")
            return jsonify({'error': 'Invalid signature'}), 401

    # Log the request
    logger.info(f"Received deployment request from {request.remote_addr}")

    # Deploy the site
    success, message = deploy_site()

    if success:
        return jsonify({'status': 'success', 'message': message}), 200
    else:
        return jsonify({'status': 'error', 'message': message}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    logger.info("Starting webhook server...")
    # Run on localhost only - nginx will proxy to it
    app.run(host='127.0.0.1', port=5000, debug=False)
