def _format_link_lines(top_links: list[dict]) -> str:
    if not top_links:
        return "No clicks recorded yet."

    return "\n".join(
        f"{i}. {row['original_url']}\n   • {row['count']} clicks"
        for i, row in enumerate(top_links, start=1)
    )


def format_stats(summary: dict, top_links: list[dict]) -> str:
    return (
        "📊 Your Stats\n\n"
        f"Total clicks: {summary['total_clicks']}\n"
        f"Unique visitors: {summary['unique_visitors']}\n\n"
        "🔗 Top Links\n"
        f"{_format_link_lines(top_links)}"
    )


def format_period(title: str, count: int, top_links: list[dict]) -> str:
    return (
        f"📅 {title}\n\n"
        f"{count} clicks\n\n"
        "🔗 Top Links\n"
        f"{_format_link_lines(top_links)}"
    )


def format_top(top_links: list[dict]) -> str:
    return f"🏆 Top Links\n\n{_format_link_lines(top_links)}"


def _format_breakdown_lines(rows: list[dict], key: str, unknown_label: str) -> str:
    if not rows:
        return "No clicks recorded yet."

    return "\n".join(
        f"{i}. {row[key] or unknown_label} — {row['count']} clicks"
        for i, row in enumerate(rows, start=1)
    )


def format_breakdown(
    countries: list[dict],
    devices: list[dict],
    browsers: list[dict],
    referrers: list[dict],
) -> str:
    return (
        "📈 Breakdown\n\n"
        "🌍 Top Countries\n"
        f"{_format_breakdown_lines(countries, 'country', 'Unknown')}\n\n"
        "📱 Top Devices\n"
        f"{_format_breakdown_lines(devices, 'device_type', 'Unknown')}\n\n"
        "🌐 Top Browsers\n"
        f"{_format_breakdown_lines(browsers, 'browser', 'Unknown')}\n\n"
        "🔗 Top Referrers\n"
        f"{_format_breakdown_lines(referrers, 'referer', 'Direct')}"
    )


def format_error() -> str:
    return (
        "⚠️ Something went wrong\n\n"
        "I couldn't generate your report right now.\n\n"
        "The error has been logged and I'll try again on the next scheduled report."
    )


def format_unknown_command() -> str:
    return (
        "❓ Unknown command\n\n"
        "Available commands:\n\n"
        "/link — Link your account\n"
        "/stats — Overall statistics\n"
        "/today — Today's report\n"
        "/week — Weekly statistics\n"
        "/top — Top links\n"
        "/breakdown — Countries, devices, browsers, referrers\n"
        "/help — Show this message"
    )


def format_help() -> str:
    return (
        "🤖 Analytics Bot\n\n"
        "Available commands:\n\n"
        "/link <code>\nLink this chat to your account\n\n"
        "/stats\nOverall statistics\n\n"
        "/today\nToday's report\n\n"
        "/week\nThis week's statistics\n\n"
        "/top\nTop links by activity\n\n"
        "/breakdown\nCountries, devices, browsers, referrers\n\n"
        "/help\nShow available commands"
    )


def format_not_linked() -> str:
    return (
        "🔒 This chat isn't linked to an account yet\n\n"
        "Generate a code from your dashboard, then send:\n"
        "/link <code>"
    )


def format_link_usage() -> str:
    return "Usage: /link <code>\n\nGenerate a code from your dashboard first."


def format_link_success() -> str:
    return "✅ This chat is now linked to your account."


def format_link_invalid_code() -> str:
    return "⚠️ That code is invalid or has expired. Generate a new one and try again."


def format_link_already_linked() -> str:
    return "⚠️ This Telegram account is already linked to a different account."
