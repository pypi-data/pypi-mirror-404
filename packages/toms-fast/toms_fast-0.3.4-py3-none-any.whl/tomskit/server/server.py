
import os
import warnings
from contextvars import ContextVar
from typing import Any, Optional

from fastapi import FastAPI
from starlette.types import ASGIApp

from tomskit.server.config import Config


class CurrentApp:
    __app_ctx: ContextVar[Optional["FastApp"]] = ContextVar('tomskit.current_app.context', default=None)

    def set_app(self, app_instance: "FastApp"):
        self.__app_ctx.set(app_instance)

    def _get_app(self) -> "FastApp":
        """Get the current application instance, raising error if not set."""
        if (app := self.__app_ctx.get()) is None:
            raise RuntimeError("No application instance is currently set")
        return app

    @property
    def app(self) -> "FastApp":
        """Get the current application instance."""
        return self._get_app()

    def __call__(self) -> "FastApp":
        """Get the current application instance when called."""
        return self._get_app()

    @property
    def config(self):
        """Get the configuration from the current application instance."""
        return self._get_app().config

    @property
    def root_path(self):
        """Get the root path from the current application instance."""
        return self._get_app().root_path

    def reset_app(self):
        """Reset the current application instance."""
        self.__app_ctx.set(None)
        # Also reset FastApp singleton instance for testing
        FastApp.reset_instance()

current_app = CurrentApp()

class FastApp(FastAPI):
    """
    A custom FastAPI instance that disables default documentation paths.

    This class creates a custom FastAPI instance that disables the default
    documentation paths (/docs, /redoc, /openapi) to enhance security and
    reduce unnecessary exposure in production environments.

    This class also adds configuration support and can initialize the
    current_app context variable for global access to the application instance.
    """

    _instance: Optional["FastApp"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._is_initialized = False
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance. Useful for testing."""
        cls._instance = None
    
    def __init__(self, *args, **kwargs):
        if not self._is_initialized:
            # Only disable docs if not explicitly provided by user
            if 'docs_url' not in kwargs:
                kwargs['docs_url'] = None
            if 'redoc_url' not in kwargs:
                kwargs['redoc_url'] = None
            if 'openapi_url' not in kwargs:
                kwargs['openapi_url'] = None
            super().__init__(*args, **kwargs)
            self.config = Config()
            current_app.set_app(self)
            self._is_initialized = True
        else:
            # Even if already initialized, ensure current_app is set
            # This handles cases where reset_app() was called but instance still exists
            current_app.set_app(self)

    def mount(self, path: str, app: ASGIApp, name: Optional[str] = None):
        """Mount an ASGI application at the specified path."""
        if hasattr(app, "config"):
            app.config = self.config
        super().mount(path, app, name)
        
    def set_environ(self):
        """Set environment variables from configuration."""
        for key, value in self.config.items():
            if isinstance(value, str):
                os.environ[key] = value
            elif isinstance(value, (int, float, bool)):
                os.environ[key] = str(value)
            elif value is None:
                os.environ[key] = ""
    
    def set_app_root_path(self, app_file: str):
        """Set the application root path based on the app file location."""
        self.app_root_path = os.path.dirname(os.path.abspath(app_file))

    def add_exception_handler(self, exc_class_or_status_code, handler):
        """Add an exception handler to the application."""
        super().add_exception_handler(exc_class_or_status_code, handler)

class FastModule(FastAPI):
    """
    FastAPI sub-application module class.

    Used to create independent sub-application modules, where each module
    can have its own routes, middleware, and configuration. Supports
    automatic Resource registration to simplify module management.
    """

    def __init__(self, name: str, *args, **kwargs):
        """
        Initialize FastModule.

        Args:
            name: Module name used to identify the module. Must match the
                module name in @register_resource(module=...).
            *args, **kwargs: Additional arguments passed to FastAPI.
        """
        # Only disable docs if not explicitly provided by user
        if 'docs_url' not in kwargs:
            kwargs['docs_url'] = None
        if 'redoc_url' not in kwargs:
            kwargs['redoc_url'] = None
        if 'openapi_url' not in kwargs:
            kwargs['openapi_url'] = None
        
        super().__init__(*args, **kwargs)

        self.module_name = name
        self._router: Optional[Any] = None  # Store the unique ResourceRouter instance

        # Get configuration from current_app
        try:
            self.config = current_app.config
        except RuntimeError:
            raise RuntimeError(
                "FastApp instance must be created and set as current_app before creating FastModule"
            )
    
    def create_router(self, prefix: str = "", **kwargs):
        """
        Create a ResourceRouter and associate it with this module.

        A FastModule can only have one ResourceRouter. If a router has
        already been created, calling this method again will raise a ValueError.

        Args:
            prefix: Route prefix.
            **kwargs: Additional arguments passed to ResourceRouter.

        Returns:
            ResourceRouter: The created ResourceRouter instance.

        Example:
            router = module.create_router(prefix="/api/v1")
        """
        from tomskit.server.resource import ResourceRouter
        
        if self._router is not None:
            raise ValueError(
                f"FastModule '{self.module_name}' already has a router. "
                "A FastModule can only have one ResourceRouter. "
                "If you need multiple routers, create multiple FastModule instances."
            )
        
        router = ResourceRouter(app=self, prefix=prefix, **kwargs)
        self._router = router
        return router
    
    def auto_register_resources(self):
        """
        Automatically register all Resources marked for this module.

        This method searches ResourceRegistry for all Resources marked with
        the current module name and automatically registers them to this
        module's ResourceRouter.

        If the router does not exist, it will be automatically created
        (using default prefix="").

        Example:
            module = FastModule(name="files")
            module.auto_register_resources()  # Auto-register all Resources marked for "files" module

            # Or create router first, then auto-register
            module = FastModule(name="files")
            router = module.create_router(prefix="/api/v1")
            module.auto_register_resources()  # Register to the created router
        """
        from tomskit.server.resource import ResourceRegistry

        # Get or create router
        if self._router is None:
            self._router = self.create_router()

        # Get all Resources for this module from registry
        resources = ResourceRegistry.get_module_resources(self.module_name)

        if not resources:
            # If no Resources are registered, issue a warning but don't error (allows manual registration)
            warnings.warn(
                f"Module '{self.module_name}' has no Resources registered via @register_resource. "
                f"Ensure Resource classes use @register_resource(module='{self.module_name}', ...) decorator.",
                UserWarning,
            )
            return

        # Register all Resources
        for resource_info in resources:
            self._router.add_resource(
                resource_cls=resource_info.resource_cls,
                path=resource_info.path,
                tags=resource_info.tags if resource_info.tags else None,
            )

        # Include router after all resources are registered
        # This ensures router has routes before being included
        self.include_router(self._router)
    
    def setup_cors(
        self,
        allow_origins: Optional[list[str]] = None,
        allow_credentials: bool = True,
        allow_methods: Optional[list[str]] = None,
        allow_headers: Optional[list[str]] = None,
        expose_headers: Optional[list[str]] = None,
    ):
        """
        Configure CORS middleware.

        Args:
            allow_origins: List of allowed origins for cross-origin requests.
            allow_credentials: Whether to allow credentials in cross-origin requests.
            allow_methods: List of allowed HTTP methods.
            allow_headers: List of allowed request headers.
            expose_headers: List of response headers exposed to clients.

        Example:
            module.setup_cors(
                allow_origins=["http://localhost:3000"],
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE"],
            )
        """
        from fastapi.middleware.cors import CORSMiddleware
        
        self.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins or [],
            allow_credentials=allow_credentials,
            allow_methods=allow_methods or ["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=allow_headers or ["Content-Type", "Authorization"],
            expose_headers=expose_headers or [],
        )
        
    def add_exception_handler(self, exc_class_or_status_code, handler):
        """Add an exception handler to the module."""
        super().add_exception_handler(exc_class_or_status_code, handler)
