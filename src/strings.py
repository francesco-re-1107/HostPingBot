
class Strings():
    # Miscellanous
    WELCOME_MESSAGE = lambda limit: f"Hello!👋\n\nThis bot lets you monitor up to {limit} hosts. Whenever they go 🔴OFFLINE or 🟢ONLINE I'll send you a notification.\nThis is an open source project, you can find it <a href='https://github.com/francesco-re-1107/HostPingBot'>here</a> on GitHub."
    CANCEL = "❌ Cancel"
    CANCELLED = "❌ Cancelled"

    # Creation
    NEW_WATCHDOG = "➕ New watchdog"
    INPUT_NAME = "📝 Enter a name for your watchdog"
    INPUT_ADDRESS = "📝 Enter the address (ip or hostname) of the host you want to monitor"
    INPUT_TYPE = "📝 Choose the type of watchdog"
    TYPE_POLLING = "Polling (ping)"
    TYPE_PUSH = "Push (http)"
    CREATED_PING_WATCHDOG_MESSAGE = lambda name, addr: f"📄 Created polling watchdog {name} ({addr})"
    CREATED_PUSH_WATCHDOG_MESSAGE = lambda name, url: f"📄 Created push watchdog {name}\n\nMake a POST request to\n<code>{url}</code> at least every 2 minutes"
    
    # Deletion
    DELETE_WATCHDOG = "🗑️ Delete a watchdog"
    INPUT_DELETE_WATCHDOG = "📝 Choose the watchdog you want to delete"
    DELETED_WATCHDOG_MESSAGE = lambda name: f"🗑️ Deleted watchdog {name}"
    NO_WATCHDOGS = f"You don't have any watchdogs yet. Use the button {NEW_WATCHDOG} to add one."
    
    # List
    LIST_WATCHDOGS = "📄 My watchdogs"
    LIST_WATCHDOGS_HEADER = "📄 My watchdogs"
    LIST_WATCHDOGS_PING_ITEM = lambda name, addr, status: f"{'🟢' if status else '🔴'} <b>{name}</b> (<code>{addr}</code>)\n\n"
    LIST_WATCHDOGS_PUSH_ITEM = lambda name, url, status, last_update: f"{'🟢' if status else '🔴'} <b>{name}</b>\n🔄 <code>{url}</code>\n🕑 Last update: <i>{last_update}</i>\n\n"

    
    # Notifications
    OFFLINE_MESSAGE = lambda name: f"🔴 {name} is OFFLINE right now"
    ONLINE_MESSAGE = lambda name: f"🟢 {name} is back ONLINE"
    ONLINE_MESSAGE_WITH_TIME = lambda name, down_for: f"🟢 {name} is back ONLINE\n\nIt\'s been down for {down_for}"
    
    # Errors
    ERROR_WATCHDOGS_LIMIT_EXCEEDED = lambda limit: f"❌ You can't add more than {limit} watchdogs"
    ERROR_WATCHDOG_DUPLICATE = lambda name: f"❌ You already have a watchdog named {name}"
    ERROR_INVALID_ADDRESS = lambda addr: f"❌ {addr} is not a valid address"