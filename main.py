import asyncio
import logging
import sys
from pyrogram import idle

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("MAIN")

# Pyrogram ke extra logs band karo
for noisy in ['pyrogram', 'pyrogram.session', 'pyrogram.connection']:
    logging.getLogger(noisy).setLevel(logging.WARNING)

# ==================== BOT REGISTRY ====================
# Yahan apne bots add/remove karo - Easy management
# Format: ("display_name", "module_name", enabled True/False)

BOT_REGISTRY = [
    ("MixSSGen Bot", "mixssgen", True),
    ("OSINT Bot", "os", True),
    ("CSC Bot", "csc", True),
 #   ("Music Bot", "music", True),
    ("Stats bot", "chatfight", True),
    ("Cloner Bot", "cloner", True),
    ("mass Bot", "bot", True)
]

# ==================== BOT LOADER ====================
loaded_bots = {}  # Store loaded bot modules

def load_bot_module(module_name: str):
    """Dynamically import bot module from Romeo folder"""
    try:
        module = __import__(f"Romeo.{module_name}", fromlist=[module_name])
        return module
    except ImportError as e:
        logger.error(f"❌ Failed to import Romeo.{module_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error loading {module_name}: {e}")
        return None

async def start_single_bot(display_name: str, module_name: str) -> bool:
    """Start a single bot and return success status"""
    logger.info(f"🔄 Starting {display_name}...")
    
    try:
        # Load module
        module = load_bot_module(module_name)
        if not module:
            logger.error(f"❌ {display_name}: Module not found")
            return False
        
        # Check if start_bot function exists
        if not hasattr(module, 'start_bot'):
            logger.error(f"❌ {display_name}: No start_bot() function")
            return False
        
        # Start the bot
        result = await module.start_bot()
        
        # Store reference for later cleanup
        loaded_bots[module_name] = module
        
        logger.info(f"✅ {display_name} started successfully! (@{result})")
        return True
        
    except Exception as e:
        logger.exception(f"❌ {display_name} failed to start: {e}")
        return False

async def stop_all_bots():
    """Stop all running bots gracefully"""
    logger.info("🛑 Stopping all bots...")
    
    for module_name, module in loaded_bots.items():
        try:
            if hasattr(module, 'stop_bot'):
                await module.stop_bot()
                logger.info(f"✅ {module_name} stopped")
        except Exception as e:
            logger.warning(f"⚠️ Error stopping {module_name}: {e}")

# ==================== MAIN FUNCTION ====================
async def main():
    print("=" * 50)
    print("🚀 MULTI-BOT SYSTEM INITIALIZING")
    print("=" * 50)
    
    # Get enabled bots only
    enabled_bots = [(name, mod) for name, mod, enabled in BOT_REGISTRY if enabled]
    
    if not enabled_bots:
        logger.error("❌ No bots enabled in BOT_REGISTRY!")
        return
    
    print(f"\n📋 Bots to start: {len(enabled_bots)}")
    for name, _ in enabled_bots:
        print(f"   • {name}")
    print()
    
    # Start all enabled bots
    started_count = 0
    failed_count = 0
    
    for display_name, module_name in enabled_bots:
        success = await start_single_bot(display_name, module_name)
        if success:
            started_count += 1
        else:
            failed_count += 1
        
        # Small delay between bot starts
        await asyncio.sleep(1)
    
    # Summary
    print()
    print("=" * 50)
    if started_count > 0:
        print(f"🎉 SYSTEM ACTIVE | ✅ {started_count} Running | ❌ {failed_count} Failed")
    else:
        print("❌ NO BOTS STARTED - CHECK LOGS ABOVE")
        return
    print("=" * 50)
    print()
    
    # Keep bots running forever
    try:
        await idle()
    except KeyboardInterrupt:
        pass
    finally:
        await stop_all_bots()

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    try:
        # Python 3.10+ 
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutdown signal received")
    except Exception as e:
        logger.exception(f"❌ FATAL ERROR: {e}")
        sys.exit(1)
