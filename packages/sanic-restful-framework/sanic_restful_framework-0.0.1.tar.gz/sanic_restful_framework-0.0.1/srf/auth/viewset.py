import asyncio
from typing import Dict

from redis.asyncio import Redis
from sanic import Request, Sanic
from sanic.constants import SAFE_HTTP_METHODS
from sanic.response import HTTPResponse, JSONResponse
from sanic_jwt import Initialize
from sanic_jwt.authentication import Authentication
from tortoise.queryset import QuerySet

from srf.auth import models, schema
from srf.config import srfconfig
from srf.permission.permission import IsAuthenticated
from srf.tools.email import EmailValidator, VerifyEmailRequest, send_vertify_code
from srf.tools.utils import generate_code
from srf.views import BaseViewSet, action
from srf.views.http_status import HTTPStatus

from .auth import authenticate, retrieve_user
from .schema import UserSchemaReader, UserSchemaWriter


def setup_auth(app: Sanic, *args, **kwargs):
    url_prefix = kwargs.pop("url_prefix", "/api/auth")
    secret = kwargs.pop("secret", srfconfig.JWT_SECRET)
    path_to_authenticate = kwargs.pop(
        "login_path", getattr(srfconfig, "LOGIN_PATH", "login")
    )  # TODO sanic_jwt did not use the app.config in Configuration class。next srf version will drop sanic_jwt
    return Initialize(
        app,
        authenticate=authenticate,
        retrieve_user=retrieve_user,
        path_to_authenticate=path_to_authenticate,
        secret=secret,
        url_prefix=url_prefix,
        **kwargs,
    )


async def logout(request: Request):
    # TODO token handle
    return HTTPResponse(status=HTTPStatus.HTTP_200_OK)


async def register(request: Request):
    """The logic here has to be optimized"""
    req_data = request.json
    cf_info = VerifyEmailRequest.model_validate(req_data, extra="ignore")

    # fetch code from redis and compare
    email_code_register = f"{request.app.config.FORMATTER.EMAIL_CODE_REDIS}_{req_data.get('email')}"
    redis: Redis = request.app.ctx.redis
    if int(await redis.get(email_code_register)) != cf_info.confirmations:
        return HTTPResponse("The verification code is incorrect or timeout, please retry!", status=HTTPStatus.HTTP_400_BAD_REQUEST)
    # delete register code in reis
    await redis.delete(email_code_register)

    # Validate data and save the user
    sch = UserSchemaWriter.model_validate(req_data, by_alias=True, extra="ignore")
    user_db = await models.User.create(sch.model_dump(exclude_unset=True, exclude_none=True))
    user_db_data = UserSchemaReader.model_validate(user_db).model_dump(by_alias=True)

    # generate token
    aut = Authentication(request.app, request.app.ctx.jwt.config)
    access_token = await aut.generate_access_token(user={"user_id": user_db.id, "username": user_db.name, "role": user_db.role})
    user_db_data['access_token'] = access_token

    return JSONResponse(user_db_data, status=HTTPStatus.HTTP_200_OK)


async def vertify_email(request: Request):
    # TODO Verify whether the mailbox is true
    if await send_email_with_redis_code(request):
        return HTTPResponse('Email has been sent, please check')
    else:
        return HTTPResponse('Email send failed', status=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR)


async def send_email_with_redis_code(request: Request, data: Dict = None):
    req_data: Dict = request.json if not data else data  # TODO with Schema
    # schema.CreateUserEmail.model_validate_json(req_data)
    EmailValidator.model_validate(email=req_data.get('email'))
    code = generate_code(5)
    # Thread(target=send_vertify_code, args=(req_data.get('email'), code)).start()
    asyncio.create_task(send_vertify_code(req_data.get('email'), code))
    # TODO change to async thread

    email_code_register = f"{request.app.config.FORMATTER.EMAIL_CODE_REDIS}_{req_data.get('email')}"  # TODO settings
    redis: Redis = request.app.ctx.redis  # TODO change to default cache like django
    await redis.set(email_code_register, code, ex=600)
    return True


class UserViewSet(BaseViewSet):
    model = models.User
    permission_classes = (IsAuthenticated,)
    search_fields = ["name", "is_active", "id"]  # The is_active field is inconsistent with the database field, resulting in invalidation
    filter_fields = {'id': "id", "name": "name", "is_active": "is_active"}

    @property
    def queryset(self, *args, **kwargs) -> QuerySet:
        return self.model.all()

    def get_schema(self, request: Request, *args, is_safe=False, **kwargs):
        if request.method.lower() in SAFE_HTTP_METHODS or is_safe is True:
            return schema.UserSchemaReader
        else:
            return schema.UserSchemaWriter

    @action(detail=False, url_name="self", url_path="self")
    async def get_self(self, request: Request):
        user_json = self.get_schema(request).model_validate(request.ctx.user).model_dump(mode="json", by_alias=True)
        return JSONResponse(user_json)

    async def perform_create(self, sch_model, *args, **kwargs):
        # TODO vertify email available
        return await sch_model.save()
