from fastapi import APIRouter, Depends
from fastapi.security import APIKeyHeader

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
