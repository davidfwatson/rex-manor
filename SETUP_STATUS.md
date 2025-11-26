# Rex Manor Website Setup Status
**Date:** 2025-11-25
**Server IP:** 104.237.154.224
**Domain:** rexmanor.org

## ✅ COMPLETED

### 1. Server Resources Checked
- RAM: 1.9GB total, ~740MB available (sufficient)
- CPU: 1 core AMD EPYC
- Disk: 12GB free
- Hugo will be MUCH lighter than Flask apps (no Python processes, just static files)

### 2. Hugo Installed
- Version: v0.152.2 extended (latest)
- Location: `/usr/local/bin/hugo`
- Blowfish theme initialized via git submodule

### 3. Site Built Successfully
- Built to: `/home/david/webserver/rex-manor/public/`
- Pages: 17 pages generated
- Config: `/home/david/webserver/rex-manor/config/_default/hugo.toml`
- BaseURL set to: `https://rexmanor.org/`

### 4. Nginx Configured
- Config file: `/etc/nginx/sites-available/rexmanor.org`
- Enabled: `/etc/nginx/sites-enabled/rexmanor.org` (symlink)
- Currently serving HTTP on port 80
- HTTPS config prepared but commented out (waiting for SSL cert)
- Nginx tested and reloaded successfully

### 5. DNS Updated
- You pointed rexmanor.org → 104.237.154.224
- Waiting for propagation (can take 5-60 minutes)

## ⏳ IN PROGRESS

### Setup Let's Encrypt SSL Certificate
**Waiting for:** DNS propagation to complete

**To check if DNS is ready:**
```bash
dig +short rexmanor.org @8.8.8.8
# Should return: 104.237.154.224
```

**Once DNS resolves, run:**
```bash
sudo certbot --nginx -d rexmanor.org -d www.rexmanor.org
```

This will:
- Obtain SSL certificate from Let's Encrypt
- Automatically update `/etc/nginx/sites-available/rexmanor.org`
- Configure HTTPS redirect
- Set up auto-renewal

## 📋 NEXT STEPS

1. **Wait for DNS propagation** (check with dig command above)

2. **Run certbot** (command above)

3. **Verify site is live:**
   - Visit https://rexmanor.org
   - Check certificate is valid

4. **Future updates to site:**
   ```bash
   cd ~/webserver/rex-manor
   # Make your content changes...
   hugo --cleanDestinationDir
   # Site will update immediately (nginx serves static files)
   ```

## 🔧 IMPORTANT FILES

- Hugo config: `/home/david/webserver/rex-manor/config/_default/hugo.toml`
- Built site: `/home/david/webserver/rex-manor/public/`
- Nginx config: `/etc/nginx/sites-available/rexmanor.org`
- Content: `/home/david/webserver/rex-manor/content/`

## 📝 NOTES

- **No uwsgi needed** for Hugo (unlike podcast.davidfwatson.com and partymail.app)
- **No Python processes** - just static files served by nginx
- **Very lightweight** - minimal RAM usage
- **To rebuild site:** Run `hugo --cleanDestinationDir` in the rex-manor directory
- Certbot is already installed (v1.21.0)

## 🚨 IF SOMETHING BREAKS

**Check nginx status:**
```bash
sudo systemctl status nginx
sudo nginx -t  # Test config
```

**Reload nginx after changes:**
```bash
sudo systemctl reload nginx
```

**Check certbot certificates:**
```bash
sudo certbot certificates
```

**Rebuild Hugo site:**
```bash
cd ~/webserver/rex-manor
hugo --cleanDestinationDir
```

## 📞 Current State Summary
Everything is ready except SSL. The site is serving on HTTP (port 80) at rexmanor.org.
Once DNS propagates, run the certbot command above and you're done!
