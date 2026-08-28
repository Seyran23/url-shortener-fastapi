from user_agents import parse


def parse_user_agent(user_agent: str | None) -> tuple[str | None, str | None, str | None]:
    if user_agent is None:
        return None, None, None

    ua = parse(user_agent)

    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "pc"
    else:
        device_type = "other"

    return ua.browser.family, ua.os.family, device_type
