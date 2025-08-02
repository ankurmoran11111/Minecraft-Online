
import socket
import logging
import asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import *

logger = logging.getLogger(__name__)

class ServerMonitor:
    def __init__(self, telegram_app=None):
        self.telegram_app = telegram_app
        self.last_server_status = None
        self.connection_attempts = 0
        
    async def check_server_status(self):
        """Check if Minecraft server is online and accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(SERVER_CHECK_TIMEOUT)
            
            result = sock.connect_ex((MC_SERVER_HOST, MC_SERVER_PORT))
            sock.close()
            
            if result == 0:
                logger.info(f"✅ Server {MC_SERVER_HOST}:{MC_SERVER_PORT} is online")
                return True, "Server is online and accessible"
            else:
                logger.warning(f"❌ Server {MC_SERVER_HOST}:{MC_SERVER_PORT} is not responding")
                return False, "Server is not responding to connections"
                
        except socket.gaierror:
            logger.error(f"❌ Could not resolve hostname: {MC_SERVER_HOST}")
            return False, "Could not resolve server hostname (DNS issue)"
        except socket.timeout:
            logger.error(f"❌ Connection to {MC_SERVER_HOST}:{MC_SERVER_PORT} timed out")
            return False, "Connection timed out (server may be offline)"
        except Exception as e:
            logger.error(f"❌ Server check failed: {e}")
            return False, f"Server check failed: {str(e)}"
    
    async def notify_server_issue(self, error_details):
        """Send server issue notification to Telegram"""
        if not self.telegram_app:
            return
            
        try:
            server_issue_msg = f"""
🚨 **SERVER CONNECTIVITY ISSUE**

❌ **Status**: Server has problems or is offline
🌍 **Server**: `{MC_SERVER_HOST}:{MC_SERVER_PORT}`
⚠️ **Issue**: {error_details}
🕒 **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**The server is having some issue or maybe offline, please inform the admin** 📢

🔄 Bot will keep trying to reconnect automatically...
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 RETRY NOW", callback_data='retry_connection')],
                [InlineKeyboardButton("📊 CHECK STATUS", callback_data='status')]
            ])
            
            await self.telegram_app.bot.send_message(
                chat_id=AUTHORIZED_USER_ID,
                text=server_issue_msg,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Failed to send server issue notification: {e}")
          
