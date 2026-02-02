from typing import Callable, Optional, List
from fastapi import APIRouter, Depends
from .auth_firebase_token_validation import verify_firebase_token

def create_protected_router(
    *,
    prefix: str = "",
    tags: Optional[List[str]] = None,
    public_paths: Optional[List[str]] = None
) -> APIRouter:
    """
    Creates an APIRouter with authentication enabled by default.

    Args:
        prefix: Router prefix
        tags: OpenAPI tags
        public_paths: List of paths that should be public (no auth required)

    Example:
        router = create_protected_router(
            prefix="/api/v1",
            tags=["users"],
            public_paths=["/health", "/docs"]
        )
    """
    public_paths = public_paths or []
    router = APIRouter(prefix=prefix, tags=tags)

    # Store the original route registration method
    original_add_api_route = router.add_api_route

    def add_api_route_with_auth(
        path: str,
        endpoint: Callable,
        *args,
        dependencies: List = None,
        **kwargs
    ):
        # If path is not in public_paths, add authentication dependency
        if path not in public_paths:
            dependencies = dependencies or []
            # Fix: Check if verify_firebase_token is already in dependencies
            if not any(getattr(dep.dependency, '__name__', None) == 'verify_firebase_token'
                      for dep in dependencies):
                dependencies.append(Depends(verify_firebase_token))

        return original_add_api_route(
            path,
            endpoint,
            *args,
            dependencies=dependencies,
            **kwargs
        )

    # Replace the route registration method with our custom one
    router.add_api_route = add_api_route_with_auth  # type: ignore

    return router
