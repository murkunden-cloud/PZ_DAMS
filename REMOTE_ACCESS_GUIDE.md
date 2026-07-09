# DAMS Remote Access Setup Guide

## Option 1: NGROK (Easiest - Recommended)

### Setup Steps:
1. **Download ngrok:**
   - Go to https://ngrok.com/download
   - Download for Windows
   - Extract `ngrok.exe` to your DAMS folder

2. **Sign up for free account:**
   - Go to https://ngrok.com/signup
   - Create free account
   - Get your authtoken from dashboard

3. **Configure ngrok:**
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. **Start remote access:**
   - Run `setup_remote_access.bat`
   - Or manually:
     ```bash
     # Start DAMS first
     python DC_Manager.py --web
     
     # In another terminal, start ngrok
     ngrok http 5000
     ```

5. **Get your public link:**
   - ngrok will show a forwarding URL like: `https://abc123.ngrok-free.app`
   - **This is the link to share with mobile users**

### Share this link with users:
```
https://[random-id].ngrok-free.app
```

## Option 2: Port Forwarding (Advanced)

### Router Setup:
1. **Find your public IP:** Visit https://whatismyipaddress.com
2. **Access router admin:** Usually `192.168.1.1` or `192.168.0.1`
3. **Port forwarding:**
   - Forward external port 5000 to internal port 5000
   - Forward to your laptop's IP: `192.168.0.198`
4. **Share link:** `http://[YOUR_PUBLIC_IP]:5000`

## Option 3: Cloud Hosting (Best for Production)

### Hosting Options:
- **Free tier:** PythonAnywhere, Render, Railway
- **Paid:** AWS, Google Cloud, Azure

### Benefits:
- Stable public URL
- SSL/HTTPS included
- No laptop dependency
- Better performance

## Security Recommendations

### For Remote Access:
1. **Use strong passwords** for all user accounts
2. **Enable HTTPS** (ngrok provides this automatically)
3. **Limit user permissions** - give view-only access when possible
4. **Monitor access logs** regularly
5. **Use VPN** for sensitive data access

### User Access Levels:
- **Guest users:** View-only access (password: guest1)
- **Circle users:** Limited to their jurisdiction
- **Admin users:** Full access (keep secure)

## Testing Remote Access

1. **Start the service** using your chosen method
2. **Test on your mobile** using the provided link
3. **Share the link** with other users
4. **Monitor usage** through logs

## Troubleshooting

### NGROK Issues:
- **Connection refused:** Make sure DAMS is running first
- **Session expired:** Free ngrok tunnels change URLs, restart to get new link
- **Rate limited:** Upgrade ngrok plan for stable URL

### Port Forwarding Issues:
- **Can't access:** Check firewall settings
- **IP changes:** Use dynamic DNS service (No-IP, DuckDNS)
- **Router blocking:** Contact ISP if needed

## Quick Start (Recommended)

**For immediate sharing:**
1. Download ngrok to DAMS folder
2. Run `setup_remote_access.bat`
3. Copy the ngrok URL shown
4. Share that URL with mobile users

**Example shared link:**
```
https://a1b2c3d4.ngrok-free.app
```

Users can access this from anywhere on their mobile browsers.
