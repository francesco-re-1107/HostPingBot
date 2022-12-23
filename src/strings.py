class Strings:
    # Miscellanous
    WELCOME_MESSAGE = (
        lambda limit: f"Hello!👋\n\nThis bot lets you monitor up to {limit} hosts. Whenever they go 🔴OFFLINE or 🟢ONLINE I'll send you a notification.\n\nThe following types of watchdogs are supported:\n\n🔶 <b>Polling (PING)</b>\nA ping is sent to the host every 60 seconds.\n\n🔶 <b>Push (HTTP)</b>\nYour host have to make a POST request to the provided url at least every 2 minutes. If the request is not received within that interval the host will be considered OFFLINE. \n\nThis is an open source project, you can find it <a href='https://github.com/francesco-re-1107/HostPingBot'>here</a> on GitHub."
    )
    CANCEL = "❌ Cancel"
    CANCELLED = "❌ Cancelled"
    STATS = "📊 Stats"

    # Creation
    NEW_WATCHDOG = "➕ New watchdog"
    INPUT_NAME = "📝 Enter a name for your watchdog"
    INPUT_ADDRESS = (
        "📝 Enter the address (ip or hostname) of the host you want to monitor"
    )
    INPUT_TYPE = "📝 Choose the type of watchdog"
    TYPE_POLLING = "Polling (PING)"
    TYPE_PUSH = "Push (HTTP)"
    CREATED_PING_WATCHDOG_MESSAGE = (
        lambda name, addr: f"📄 Created polling watchdog {name} (<code>{addr}</code>)"
    )
    CREATED_PUSH_WATCHDOG_MESSAGE = (
        lambda name, url: f"📄 Created push watchdog {name}\n\nMake a POST request at least every 2 minutes to the following url\n\n<code>{url}</code>"
    )

    # Deletion
    DELETE_WATCHDOG = "🗑️ Delete a watchdog"
    INPUT_DELETE_WATCHDOG = "📝 Choose the watchdog you want to delete"
    DELETED_WATCHDOG_MESSAGE = lambda name: f"🗑️ Deleted watchdog {name}"
    NO_WATCHDOGS = (
        f"You don't have any watchdogs yet. Use the button {NEW_WATCHDOG} to add one."
    )

    # List
    LIST_WATCHDOGS = "📄 My watchdogs"
    LIST_WATCHDOGS_HEADER = "My watchdogs\n\n"
    LIST_WATCHDOGS_PING_HEADER = "🔶 <b>Polling (PING)</b>\n\n"
    LIST_WATCHDOGS_PUSH_HEADER = "🔶 <b>Push (HTTP)</b>\n\n"
    LIST_WATCHDOGS_PING_ITEM = (
        lambda name, addr, status, last_update: f"<b>[{'🟢' if status else '🔴'}] {name}</b>\n\t\t<code>{addr}</code>\n\t\tLast update: <i>{last_update} ago</i>\n\n"
    )
    LIST_WATCHDOGS_PUSH_ITEM = (
        lambda name, url, status, last_update: f"<b>[{'🟢' if status else '🔴'}] {name}</b>\n\t\t<code>{url}</code>\n\t\tLast update: <i>{last_update} ago</i>\n\n"
    )

    # Notifications
    OFFLINE_MESSAGE = lambda name: f"🔴 {name} is OFFLINE right now"
    ONLINE_MESSAGE = lambda name: f"🟢 {name} is back ONLINE"
    ONLINE_MESSAGE_WITH_TIME = (
        lambda name, down_for: f"🟢 {name} is back ONLINE\n\nIt's been down for {down_for}"
    )

    # Errors
    ERROR_WATCHDOGS_LIMIT_EXCEEDED = (
        lambda limit: f"❌ You can't add more than {limit} watchdogs"
    )
    ERROR_WATCHDOG_DUPLICATE = (
        lambda name: f"❌ You already have a watchdog named {name}"
    )
    ERROR_INVALID_ADDRESS = lambda addr: f"❌ {addr} is not a valid address"
    ERROR_DELETING_WATCHDOG = "❌ The watchdog you selected doesn't exist"
