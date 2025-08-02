import os
import subprocess
import asyncio
import json
import logging
from server_monitor import ServerMonitor
from config import *

logger = logging.getLogger(__name__)

class EnhancedMinecraftBot:
    def __init__(self):
        self.bot_process = None
        self.is_connected = False
        self.server_monitor = None
        self.telegram_app = None
        
        self.stats = {
            'connect_time': None,
            'total_movements': 0,
            'deaths': 0,
            'respawns': 0,
            'connection_attempts': 0,
            'server_issues': 0,
            'last_death': None,
            'death_cause': None,
            'killer': None,
            'last_movement': None,
            'last_server_check': None,
            'server_status': 'Unknown',
            'status': 'Disconnected',
            'position': {'x': 0, 'y': 0, 'z': 0},
            'health': 20,
            'effects_active': False
        }
        
        self.create_minecraft_bot_script()
    
    def set_telegram_app(self, app):
        """Set telegram app reference for notifications"""
        self.telegram_app = app
        self.server_monitor = ServerMonitor(app)
    
    def create_minecraft_bot_script(self):
        """Create the Node.js Minecraft bot script"""
        bot_script = """const mineflayer = require('mineflayer');
const fs = require('fs');
const net = require('net');

class EnhancedMinecraftBotManager {
    constructor() {
        this.bot = null;
        this.isConnected = false;
        this.statusFile = 'bot_status.json';
        this.logFile = 'bot_log.txt';
        this.commandFile = 'bot_commands.txt';
        this.respawnTimer = null;
        this.effectTimer = null;
        this.connectionRetries = 0;
        this.maxRetries = 3;
        this.retryDelay = 30000;
        
        this.stats = {
            position: {x: 0, y: 0, z: 0},
            health: 20,
            deaths: 0,
            respawns: 0,
            connectionAttempts: 0,
            serverIssues: 0,
            lastDeath: null,
            deathCause: null,
            killer: null,
            isAlive: true,
            effectsActive: false,
            serverStatus: 'Unknown',
            lastServerCheck: null,
            status: 'Disconnected'
        };
        
        this.movements = ['forward', 'back', 'left', 'right', 'jump', 'look_around', 'sneak'];
        this.initializeFiles();
        this.startCommandListener();
    }
    
    initializeFiles() {
        this.updateStatus();
        fs.writeFileSync(this.commandFile, '');
    }
    
    updateStatus() {
        fs.writeFileSync(this.statusFile, JSON.stringify(this.stats, null, 2));
    }
    
    log(message) {
        const timestamp = new Date().toISOString();
        const logEntry = `[${timestamp}] ${message}\\n`;
        fs.appendFileSync(this.logFile, logEntry);
        console.log(message);
    }
    
    async connect() {
        try {
            if (this.isConnected) {
                this.log('Already connected to server');
                return;
            }
            
            this.stats.connectionAttempts++;
            this.connectionRetries++;
            this.log(`🔍 Connecting... (Attempt ${this.connectionRetries}/${this.maxRetries})`);
            
            this.bot = mineflayer.createBot({
                host: process.env.MC_HOST || 'atmkbfjgx5.aternos.me',
                port: parseInt(process.env.MC_PORT) || 49252,
                username: process.env.MC_USERNAME || 'AFKBot_24x7',
                version: false,
                timeout: 30000
            });
            
            this.setupEventHandlers();
            
        } catch (error) {
            this.log(`❌ Connection error: ${error.message}`);
            this.stats.status = 'Connection Failed';
            this.stats.serverIssues++;
            this.updateStatus();
        }
    }
    
    setupEventHandlers() {
        this.bot.on('login', () => {
            this.log('✅ Successfully logged into Minecraft server!');
            this.isConnected = true;
            this.connectionRetries = 0;
            this.stats.isAlive = true;
            this.stats.status = 'Connected & Active';
            this.stats.serverStatus = 'Online';
            this.updateStatus();
            
            setTimeout(() => {
                this.startMovementSystem();
                this.startEffectSystem();
            }, 3000);
        });
        
        this.bot.on('spawn', () => {
            this.log('🎮 Bot spawned in world');
            this.stats.isAlive = true;
            this.updatePosition();
            this.giveImmmortalityEffects();
        });
        
        this.bot.on('respawn', () => {
            this.log('🔄 Bot respawned');
            this.stats.respawns++;
            this.stats.isAlive = true;
            this.updateStatus();
            
            setTimeout(() => {
                this.giveImmmortalityEffects();
            }, 2000);
        });
        
        this.bot.on('death', () => {
            this.handleDeath();
        });
        
        this.bot.on('health', () => {
            this.stats.health = this.bot.health;
            this.updateStatus();
            
            if (this.bot.health < 15 && this.stats.isAlive) {
                this.log(`⚠️ Health low: ${this.bot.health}. Refreshing effects...`);
                this.giveImmmortalityEffects();
            }
        });
        
        this.bot.on('move', () => {
            this.updatePosition();
        });
        
        this.bot.on('error', (err) => {
            this.log(`❌ Bot error: ${err.message}`);
        });
        
        this.bot.on('end', () => {
            this.log('🔌 Bot disconnected from server');
            this.isConnected = false;
            this.stats.status = 'Disconnected';
            this.updateStatus();
        });
        
        this.bot.on('kicked', (reason) => {
            this.log(`👢 Bot was kicked: ${reason}`);
            this.stats.status = 'Kicked';
            this.updateStatus();
        });
    }
    
    handleDeath() {
        this.log('💀 Bot died!');
        this.stats.deaths++;
        this.stats.isAlive = false;
        this.stats.lastDeath = new Date().toISOString();
        this.stats.status = 'Dead - Respawning';
        this.stats.deathCause = 'Unknown cause';
        this.stats.killer = 'Environment';
        this.updateStatus();
        
        this.respawnTimer = setTimeout(() => {
            this.autoRespawn();
        }, 3000);
    }
    
    autoRespawn() {
        if (this.bot && !this.stats.isAlive) {
            this.log('🔄 Auto-respawning...');
            this.bot.respawn();
        }
    }
    
    giveImmmortalityEffects() {
        if (!this.bot || !this.isConnected) return;
        
        try {
            const effects = [
                '/effect give @s minecraft:resistance 999999 255 true',
                '/effect give @s minecraft:regeneration 999999 255 true',
                '/effect give @s minecraft:absorption 999999 255 true',
                '/effect give @s minecraft:fire_resistance 999999 255 true',
                '/effect give @s minecraft:water_breathing 999999 255 true',
                '/effect give @s minecraft:night_vision 999999 255 true',
                '/effect give @s minecraft:saturation 999999 255 true',
                '/effect give @s minecraft:health_boost 999999 255 true'
            ];
            
            effects.forEach((effect, index) => {
                setTimeout(() => {
                    this.bot.chat(effect);
                }, index * 100);
            });
            
            this.stats.effectsActive = true;
            this.log('✨ Immortality effects applied');
            this.updateStatus();
            
        } catch (error) {
            this.log(`❌ Failed to apply effects: ${error.message}`);
        }
    }
    
    startEffectSystem() {
        this.effectTimer = setInterval(() => {
            if (this.isConnected && this.stats.isAlive) {
                this.giveImmmortalityEffects();
            }
        }, 60000);
    }
    
    startMovementSystem() {
        setInterval(() => {
            if (this.isConnected && this.stats.isAlive) {
                this.performSafeMovement();
            }
        }, 4000);
    }
    
    performSafeMovement() {
        if (!this.bot || !this.isConnected || !this.stats.isAlive) return;
        
        try {
            if (this.isTerrainSafe()) {
                const movement = this.movements[Math.floor(Math.random() * this.movements.length)];
                this.executeMovement(movement);
            } else {
                this.log('⚠️ Unsafe terrain detected, staying in place');
                this.executeMovement('look_around');
            }
        } catch (error) {
            this.log(`Movement error: ${error.message}`);
        }
    }
    
    isTerrainSafe() {
        if (!this.bot.entity || !this.bot.entity.position) return false;
        
        const pos = this.bot.entity.position;
        
        for (let x = -2; x <= 2; x++) {
            for (let z = -2; z <= 2; z++) {
                for (let y = -1; y <= 1; y++) {
                    const checkPos = pos.offset(x, y, z);
                    const block = this.bot.blockAt(checkPos);
                    
                    if (block) {
                        if (block.name.includes('lava') || 
                            block.name.includes('water') ||
                            block.name.includes('fire') ||
                            block.name === 'air' && y < 0) {
                            return false;
                        }
                    }
                }
            }
        }
        
        return true;
    }
    
    executeMovement(action) {
        if (!this.bot) return;
        
        try {
            switch (action) {
                case 'forward':
                    this.bot.setControlState('forward', true);
                    setTimeout(() => this.bot.setControlState('forward', false), 500);
                    break;
                case 'back':
                    this.bot.setControlState('back', true);
                    setTimeout(() => this.bot.setControlState('back', false), 300);
                    break;
                case 'left':
                    this.bot.setControlState('left', true);
                    setTimeout(() => this.bot.setControlState('left', false), 300);
                    break;
                case 'right':
                    this.bot.setControlState('right', true);
                    setTimeout(() => this.bot.setControlState('right', false), 300);
                    break;
                case 'jump':
                    this.bot.setControlState('jump', true);
                    setTimeout(() => this.bot.setControlState('jump', false), 100);
                    break;
                case 'sneak':
                    this.bot.setControlState('sneak', true);
                    setTimeout(() => this.bot.setControlState('sneak', false), 500);
                    break;
                case 'look_around':
                    const yaw = (Math.random() - 0.5) * Math.PI;
                    const pitch = (Math.random() - 0.5) * Math.PI / 3;
                    this.bot.look(yaw, pitch);
                    break;
            }
            
            this.log(`🎮 Performed movement: ${action}`);
            
        } catch (error) {
            this.log(`Movement execution error: ${error.message}`);
        }
    }
    
    updatePosition() {
        if (this.bot && this.bot.entity && this.bot.entity.position) {
            const pos = this.bot.entity.position;
            this.stats.position = {
                x: Math.round(pos.x * 100) / 100,
                y: Math.round(pos.y * 100) / 100,
                z: Math.round(pos.z * 100) / 100
            };
            this.updateStatus();
        }
    }
    
    startCommandListener() {
        setInterval(() => {
            try {
                if (fs.existsSync(this.commandFile)) {
                    const commands = fs.readFileSync(this.commandFile, 'utf8').trim();
                    if (commands) {
                        const commandList = commands.split('\\n').filter(cmd => cmd.trim());
                        commandList.forEach(command => {
                            this.executeCommand(command.trim());
                        });
                        fs.writeFileSync(this.commandFile, '');
                    }
                }
            } catch (error) {
                // Ignore
            }
        }, 1000);
    }
    
    executeCommand(command) {
        switch (command) {
            case 'CONNECT':
                this.connect();
                break;
            case 'DISCONNECT':
                this.disconnect();
                break;
            case 'RESPAWN':
                this.autoRespawn();
                break;
            case 'EFFECTS':
                this.giveImmmortalityEffects();
                break;
            case 'RETRY':
                this.connectionRetries = 0;
                this.connect();
                break;
        }
    }
    
    disconnect() {
        this.log('🔌 Disconnecting from server...');
        this.isConnected = false;
        if (this.bot) {
            this.bot.quit();
            this.bot = null;
        }
        if (this.respawnTimer) clearTimeout(this.respawnTimer);
        if (this.effectTimer) clearInterval(this.effectTimer);
        this.stats.status = 'Disconnected';
        this.updateStatus();
    }
}

const botManager = new EnhancedMinecraftBotManager();

process.on('SIGINT', () => {
    console.log('\\nShutting down bot...');
    botManager.disconnect();
    process.exit(0);
});

process.on('SIGTERM', () => {
    botManager.disconnect();
    process.exit(0);
});"""
        
        with open('minecraft_bot.js', 'w') as f:
            f.write(bot_script)
        logger.info("✅ Enhanced Minecraft bot script created")
    
    def send_command_to_bot(self, command):
        try:
            with open('bot_commands.txt', 'a') as f:
                f.write(f"{command}\n")
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
    
    def get_bot_status(self):
        try:
            with open('bot_status.json', 'r') as f:
                return json.load(f)
        except:
            return self.stats
    
    async def connect_to_server(self):
        try:
            if self.bot_process and self.bot_process.poll() is None:
                return "✅ Bot is already running!"
            
            server_online, server_message = await self.server_monitor.check_server_status()
            
            if not server_online:
                await self.server_monitor.notify_server_issue(server_message)
                return f"❌ **Server Check Failed**\n\n{server_message}\n\n**The server is having some issue or maybe offline, please inform the admin** 📢"
            
            env = os.environ.copy()
            env['MC_HOST'] = MC_SERVER_HOST
            env['MC_PORT'] = str(MC_SERVER_PORT)
            env['MC_USERNAME'] = MC_BOT_USERNAME
            
            self.bot_process = subprocess.Popen(
                ['node', 'minecraft_bot.js'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.send_command_to_bot('CONNECT')
            await asyncio.sleep(5)
            
            return "✅ **Successfully connected to Minecraft server!**\n\n🛡️ Immortality effects will be applied automatically."
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return f"❌ Connection failed: {str(e)}"
    
    async def disconnect_from_server(self):
        try:
            self.send_command_to_bot('DISCONNECT')
            
            if self.bot_process:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=5)
                self.bot_process = None
            
            return "✅ Successfully disconnected from server"
        except Exception as e:
            return f"⚠️ Disconnect error: {str(e)}"
    
    async def retry_connection(self):
        self.send_command_to_bot('RETRY')
        return "🔄 **Connection retry initiated**"
    
    async def force_respawn(self):
        self.send_command_to_bot('RESPAWN')
        return "🔄 Respawn command sent to bot"
    
    async def refresh_effects(self):
        self.send_command_to_bot('EFFECTS')
        return "✨ Effect refresh command sent to bot"
    
    def get_detailed_status(self):
        status = self.get_bot_status()
        
        status_emoji = "🟢" if status.get('status') == 'Connected & Active' else "🔴"
        alive_emoji = "💖" if status.get('isAlive', True) else "💀"
        effects_emoji = "✨" if status.get('effectsActive', False) else "❌"
        
        pos = status.get('position', {})
        
        status_info = f"""
{status_emoji} **Enhanced Bot Status**

🎮 **Connection**: {status.get('status', 'Unknown')}
{alive_emoji} **Bot State**: {'Alive' if status.get('isAlive', True) else 'Dead'}
❤️ **Health**: {status.get('health', 0)}/20
{effects_emoji} **Immortality Effects**: {'Active' if status.get('effectsActive') else 'Inactive'}

📍 **Position**:
X: {pos.get('x', 0)} | Y: {pos.get('y', 0)} | Z: {pos.get('z', 0)}

🌍 **Server**: `{MC_SERVER_HOST}:{MC_SERVER_PORT}`
👤 **Username**: `{MC_BOT_USERNAME}`

📊 **Statistics**:
💀 Deaths: {status.get('deaths', 0)}
🔄 Respawns: {status.get('respawns', 0)}
🔌 Connection Attempts: {status.get('connectionAttempts', 0)}

🛡️ **Safety Features**:
✅ Auto-Respawn System
✅ Terrain Avoidance  
✅ Immortality Effects
✅ Death Monitoring
✅ Real-time Status Updates
        """
        
        return status_info.strip()
      
