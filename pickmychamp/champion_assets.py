from urllib.error import URLError
from urllib.request import Request, urlopen

from .counter_guides import champion_catalog


MAX_CHAMPION_ASSET_BYTES = 5 * 1024 * 1024
CHAMPION_ASSET_CACHE_CONTROL = (
    "public, max-age=3600, s-maxage=3600, stale-while-revalidate=86400"
)
ASSET_TYPES = {
    "portrait": ("image/png", b"\x89PNG\r\n\x1a\n"),
    "splash": ("image/jpeg", b"\xff\xd8\xff"),
}


def fetch_champion_asset(asset_type: str, champion_id: str) -> tuple[bytes, str]:
    if asset_type not in ASSET_TYPES:
        raise ValueError("Type d'image de champion inconnu.")

    patch, champions = champion_catalog()
    if champion_id not in {champion.get("id") for champion in champions}:
        raise ValueError("Champion inconnu.")

    content_type, signature = ASSET_TYPES[asset_type]
    if asset_type == "portrait":
        url = (
            f"https://ddragon.leagueoflegends.com/cdn/{patch}/img/champion/"
            f"{champion_id}.png"
        )
    else:
        url = (
            "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/"
            f"{champion_id}_0.jpg"
        )

    request = Request(
        url,
        headers={
            "Accept": content_type,
            "User-Agent": "PickMyChamp/1.0",
        },
    )
    try:
        with urlopen(request, timeout=5) as response:
            image = response.read(MAX_CHAMPION_ASSET_BYTES + 1)
            upstream_type = response.headers.get("Content-Type", "")
            upstream_type = upstream_type.split(";", 1)[0].strip().lower()
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Data Dragon champion image is unavailable.") from exc

    if len(image) > MAX_CHAMPION_ASSET_BYTES:
        raise RuntimeError("Data Dragon champion image exceeded the size limit.")
    if upstream_type != content_type or not image.startswith(signature):
        raise RuntimeError("Data Dragon returned an invalid champion image.")
    return image, content_type