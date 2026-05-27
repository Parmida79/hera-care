from fastapi import APIRouter, Depends
from fastapi.security import APIKeyHeader

from .auth import limited_auth_router, restricted_auth_router, \
    public_auth_router
from .chat import chat_router
from .test import test_router

oauth2_scheme = APIKeyHeader(name='Authorization')
restricted_router = APIRouter(prefix='/restricted/hera-care/v1',
                              dependencies=[Depends(oauth2_scheme)])
limited_router = APIRouter(prefix='/limited/hera-care/v1',
                           dependencies=[Depends(oauth2_scheme)])
public_router = APIRouter(prefix='/public/hera-care/v1')


# test
public_router.include_router(
    test_router,
    prefix='/test',
    tags=['test'],
)

# auth
limited_router.include_router(
    limited_auth_router,
    prefix='/',
    tags=['auth'],
)
restricted_router.include_router(
    restricted_auth_router,
    prefix='/',
    tags=['auth'],
)
public_router.include_router(
    public_auth_router,
    prefix='/',
    tags=['auth'],
)

# chat
restricted_router.include_router(
    chat_router,
    prefix='/chat',
    tags=['chat'],
)
