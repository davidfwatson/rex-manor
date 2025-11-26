# Rex Manor Webhook Deployment

This directory contains the webhook endpoint for automated deployments of the Rex Manor Hugo site.

## Setup Instructions

### 1. Install Python Dependencies

```bash
cd /home/david/webserver/rex-manor/webhook
pip3 install -r requirements.txt
```

### 2. Generate a Webhook Secret

```bash
openssl rand -hex 32
```

Save this secret - you'll need it for both the systemd service and GitHub Actions.

### 3. Update the Systemd Service

Edit `rex-manor-webhook.service` and replace `change-me-in-production` with your generated secret:

```ini
Environment="WEBHOOK_SECRET=your-secret-here"
```

### 4. Install and Start the Service

```bash
sudo cp /home/david/webserver/rex-manor/webhook/rex-manor-webhook.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rex-manor-webhook
sudo systemctl start rex-manor-webhook
sudo systemctl status rex-manor-webhook
```

### 5. Configure Nginx

Add a location block to your nginx configuration to proxy webhook requests. See the nginx configuration section below.

### 6. Set up GitHub Actions

The webhook secret needs to be added as a GitHub repository secret named `WEBHOOK_SECRET`.

## Nginx Configuration

Add this location block to your nginx server configuration:

```nginx
location /webhook/deploy {
    proxy_pass http://127.0.0.1:5000/deploy;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

After adding, test and reload nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Testing

Test the webhook locally:

```bash
curl -X POST http://localhost:5000/health
curl -X POST http://localhost:5000/deploy
```

Test through nginx:

```bash
curl -X POST https://your-domain.com/webhook/deploy
```

## Monitoring

View webhook logs:

```bash
tail -f /home/david/webserver/rex-manor/webhook/deploy.log
```

Check service status:

```bash
sudo systemctl status rex-manor-webhook
```

## Troubleshooting

If the webhook isn't working:

1. Check the service is running: `sudo systemctl status rex-manor-webhook`
2. Check the logs: `tail -f /home/david/webserver/rex-manor/webhook/deploy.log`
3. Verify nginx configuration: `sudo nginx -t`
4. Test the endpoint directly: `curl -X POST http://localhost:5000/deploy`
5. Ensure the webhook secret matches in both the service and GitHub Actions
