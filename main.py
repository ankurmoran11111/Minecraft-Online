import asyncio
import logging
import subprocess
import sys
from telegram_interface import EnhancedTelegramInterface

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def install_dependencies():
    """Install required Node.js packages"""
    try:
        logger.info("📦 Installing Node.js dependencies...")
        process = await asyncio.create_subprocess_exec(
            'npm', 'install', 'mineflayer', 'minecraft-data',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        logger.info("✅ Dependencies installed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to install dependencies: {e}")

async def main():
    """Main function"""
    logger.info("🤖 Starting Enhanced Minecraft Telegram Bot v2.0...")
    
    # Install dependencies
    await install_dependencies()
    
    # Start enhanced Telegram interface
    telegram_interface = EnhancedTelegramInterface()
    
    try:
        await telegram_interface.run_telegram_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await telegram_interface.mc_bot.disconnect_from_server()

if __name__ == "__main__":
    # Install python-telegram-bot if not installed
    try:
        import telegram
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==20.7"])
    
    asyncio.run(main())
  
