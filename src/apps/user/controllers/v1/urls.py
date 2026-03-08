from apps.user.controllers.v1.auth import router as auth_router
from apps.user.controllers.v1.user import router as user_router
from config.auth.authentication import UnifiedJWTAuthentication
from ninja import NinjaAPI

# Create instance of the unified authentication class
jwt_auth = UnifiedJWTAuthentication()

api_v1 = NinjaAPI(
    title="API v1",
    version="1.1",
    description="Modern Django-Ninja API template with best practices (Version 1)",
)

# Add routers
api_v1.add_router("/auth", auth_router)
api_v1.add_router("/users", user_router, auth=jwt_auth)
