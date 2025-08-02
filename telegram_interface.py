from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from datetime import datetime
from minecraft_bot import EnhancedMinecraftBot
from config import *

logger = logging.getLogger(__name__)

class EnhancedTelegramInterface:
    def __init__(self):
        self.application = None
        self.mc_bot = EnhancedMinecraftBot()
    
    def create_keyboard(self):
        keyboard = [
            [
                InlineKeyboardButton("🔗 CONNECT", callback_data='connect'),
                InlineKeyboardButton("🔌 DISCONNECT", callback_data='disconnect')
            ],
            [
                InlineKeyboardButton("🔄 RETRY CONNECTION", callback_data='retry_connection'),
                InlineKeyboardButton("✨ REFRESH EFFECTS", callback_data='effects')
            ],
            [
                InlineKeyboardButton("🔄 RESPAWN", callback_data='respawn'),
                InlineKeyboardButton("📊 STATUS", callback_data='status')
            ],
            [
                InlineKeyboardButton("🌐 SERVER CHECK", callback_data='server_check'),
                InlineKeyboardButton("ℹ️ HELP", callback_data='help')
            ],
            [
                InlineKeyboardButton("🆘 EMERGENCY", callback_data='emergency')
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def is_authorized(self, user_id):
        return user_id == AUTHORIZED_USER_ID
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Access Denied!")
            return
        
        welcome_msg = f"""
🤖 **Enhanced Minecraft Bot Controller v2.0**

**FEATURES:**
💀 Death Detection & Auto-Respawn
🛡️ Immortality Effects (requires OP)
🌍 Terrain Avoidance
📊 Real-time Monitoring
🌐 Server Status Detection
📢 Admin Alert System

**Server:** `{MC_SERVER_HOST}:{MC_SERVER_PORT}`
**Bot:** `{MC_BOT_USERNAME}`

**If server has issues, you'll get:**
*"The server is having some issue or maybe offline, please inform the admin"* 📢

Ready to keep your server alive 24/7! 🚀
        """
        
        await update.message.reply_text(
            welcome_msg,
            reply_markup=self.create_keyboard(),
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        
        if not self.is_authorized(query.from_user.id):
            await query.answer("❌ Access Denied!", show_alert=True)
            return
        
        await query.answer()
        action = query.data
        
        if action == 'connect':
            await query.edit_message_text("🔍 Checking server status and connecting...")
            result = await self.mc_bot.connect_to_server()
            await query.edit_message_text(result, reply_markup=self.create_keyboard(), parse_mode='Markdown')
            
        elif action == 'disconnect':
            await query.edit_message_text("🔄 Disconnecting...")
            result = await self.mc_bot.disconnect_from_server()
            await query.edit_message_text(result, reply_markup=self.create_keyboard())
            
        elif action == 'retry_connection':
            await query.edit_message_text("🔄 Retrying server connection...")
            result = await self.mc_bot.retry_connection()
            await query.edit_message_text(result, reply_markup=self.create_keyboard())
            
        elif action == 'respawn':
            result = await self.mc_bot.force_respawn()
            await query.edit_message_text(result, reply_markup=self.create_keyboard())
            
        elif action == 'effects':
            result = await self.mc_bot.refresh_effects()
            await query.edit_message_text(result, reply_markup=self.create_keyboard())
            
        elif action == 'status':
            status = self.mc_bot.get_detailed_status()
            await query.edit_message_text(
                status, 
                reply_markup=self.create_keyboard(),
                parse_mode='Markdown'
            )
            
        elif action == 'server_check':
            await query.edit_message_text("🔍 Performing server connectivity check...")
            server_online, server_message = await self.mc_bot.server_monitor.check_server_status()
            
            if server_online:
                result = f"✅ **Server Status: ONLINE**\n\n🌍 Server: `{MC_SERVER_HOST}:{MC_SERVER_PORT}`\n📡 Response: {server_message}\n🕒 Checked: {datetime.now().strftime('%H:%M:%S')}"
            else:
                result = f"❌ **Server Status: OFFLINE/ISSUES**\n\n🌍 Server: `{MC_SERVER_HOST}:{MC_SERVER_PORT}`\n⚠️ Issue: {server_message}\n🕒 Checked: {datetime.now().strftime('%H:%M:%S')}\n\n**The server is having some issue or maybe offline, please inform the admin** 📢"
            
            await query.edit_message_text(
                result,
                reply_markup=self.create_keyboard(),
                parse_mode='Markdown'
            )
            
        elif action == 'help':
            help_info = """
🆘 **Enhanced Bot Help**

**Control Buttons:**
🔗 **CONNECT** - Connect to server
🔌 **DISCONNECT** - Stop bot safely
🔄 **RETRY CONNECTION** - Force reconnect
✨ **REFRESH EFFECTS** - Reapply immortality
🔄 **RESPAWN** - Force respawn if dead
📊 **STATUS** - Detailed bot information
🌐 **SERVER CHECK** - Manual server test

**Auto Features:**
• Death detection & notifications
• Auto-respawn on death (3s delay)
• Immortality effects (permanent)
• Terrain hazard avoidance
• Smart movement patterns
• Real-time health monitoring
• Server connectivity monitoring

**Requirements:**
• Bot needs OP permissions: `/op AFKBot_24x7`
• Server must be online
• Node.js must be installed
            """
            await query.edit_message_text(
                help_info,
                reply_markup=self.create_keyboard(),
                parse_mode='Markdown'
            )
            
        elif action == 'emergency':
            await query.edit_message_text("🚨 Emergency stop...")
            result = await self.mc_bot.disconnect_from_server()
            await query.edit_message_text(
                f"🚨 **EMERGENCY STOP**\n\n{result}",
                reply_markup=self.create_keyboard(),
                parse_mode='Markdown'
            )
    
    async def run_telegram_bot(self):
        """Start enhanced Telegram bot"""
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Set telegram app reference in mc_bot for notifications
        self.mc_bot.set_telegram_app(self.application)
        
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        logger.info("🚀 Starting Enhanced Telegram Bot with Server Monitoring...")
        await self.application.run_polling()
      
