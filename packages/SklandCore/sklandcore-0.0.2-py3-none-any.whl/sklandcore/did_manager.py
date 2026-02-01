from .did import getDid

_account_did_cache: dict[str, str] = {}


async def get_or_create_did(account_key: str) -> str:
    if account_key not in _account_did_cache:
        _account_did_cache[account_key] = await getDid()
    return _account_did_cache[account_key]
