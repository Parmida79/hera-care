from fastapi import APIRouter

test_router = APIRouter()


@test_router.get('/')
async def test():
    return 'If you are seeing this, the config is set correctly!'
