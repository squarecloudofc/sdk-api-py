from importlib.util import find_spec

USING_PYDANTIC = bool(find_spec('pydantic'))
