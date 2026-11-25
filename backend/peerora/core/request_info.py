"""Who is calling: client IP address and browser (user agent), for audit logs.

Brave sends exactly the same User-Agent as Chrome (on purpose, for privacy),
so the User-Agent alone cannot tell them apart. Two better signals exist:

1. The Sec-CH-UA client-hint header, which browsers send on secure origins
   (HTTPS and localhost), e.g.  "Brave";v="131", "Chromium";v="131", ...
   Chrome lists "Google Chrome" instead, so this never mislabels Chrome.
2. A hint from the frontend (X-Client-Brand: Brave), set only when the page's
   navigator.brave.isBrave() check succeeds - used when no client hint arrives.

When either says Brave and the User-Agent does not already name it, a
"Brave/<version>" product token (or just "Brave" for the frontend hint, which
has no version) is appended to the stored user agent, the same form older
Brave versions used. Nothing else is ever added, so the stored value
stays a normal User-Agent string that the frontend's parser understands.
"""

import re
from dataclasses import dataclass

from fastapi import Request

from peerora.config import trust_proxy_headers

USER_AGENT_MAX_LENGTH = 255
CLIENT_BRAND_HEADER = "X-Client-Brand"
# Brands we add to the user agent, and the token we add for each. Only brands
# that hide themselves in the User-Agent need to be listed (Edge and Opera
# already include "Edg/" and "OPR/").
_KNOWN_HIDDEN_BRANDS = {"Brave": "Brave"}
_BRAND_PATTERN = re.compile(r'"([^"]{1,64})"\s*;\s*v\s*=\s*"([0-9][0-9.]{0,20})"')


@dataclass(frozen=True)
class ClientInfo:
    ip_address: str | None
    user_agent: str | None


def brand_from_client_hints(sec_ch_ua: str | None) -> tuple[str, str] | None:
    """('Brave', '131') if the Sec-CH-UA header lists a known hidden brand."""
    if not sec_ch_ua:
        return None
    for brand, version in _BRAND_PATTERN.findall(sec_ch_ua):
        if brand in _KNOWN_HIDDEN_BRANDS:
            return _KNOWN_HIDDEN_BRANDS[brand], version.split(".")[0]
    return None


def describe_user_agent(user_agent: str | None, sec_ch_ua: str | None, client_brand: str | None) -> str | None:
    """The user agent to store, with a Brave token added when Brave is detected."""
    if not user_agent:
        return None
    brand = brand_from_client_hints(sec_ch_ua)
    if brand is None and client_brand in _KNOWN_HIDDEN_BRANDS:
        brand = (_KNOWN_HIDDEN_BRANDS[client_brand], "")  # frontend hint: no version
    if brand is not None and not re.search(rf"\b{brand[0]}\b", user_agent):
        token = f" {brand[0]}/{brand[1]}" if brand[1] else f" {brand[0]}"
        # Keep the brand token even when the User-Agent is long.
        user_agent = user_agent[: USER_AGENT_MAX_LENGTH - len(token)] + token
    return user_agent[:USER_AGENT_MAX_LENGTH]


def get_client_info(request: Request) -> ClientInfo:
    ip: str | None = None
    if trust_proxy_headers():
        forwarded = request.headers.get("x-forwarded-for", "")
        ip = forwarded.split(",")[0].strip() or None
    if ip is None and request.client is not None:
        ip = request.client.host
    return ClientInfo(
        ip_address=ip[:45] if ip else None,
        user_agent=describe_user_agent(
            request.headers.get("user-agent"),
            request.headers.get("sec-ch-ua"),
            request.headers.get(CLIENT_BRAND_HEADER),
        ),
    )
