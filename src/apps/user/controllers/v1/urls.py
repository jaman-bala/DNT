from ninja import Router

from apps.user.controllers.v1.auth import router as auth_router
from apps.user.controllers.v1.user import router as user_router
from config.auth.authentication import UnifiedJWTAuthentication

jwt_auth = UnifiedJWTAuthentication()

router = Router(tags=["Users"])

router.add_router("/auth", auth_router)
router.add_router("/users", user_router, auth=jwt_auth)
