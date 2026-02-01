from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from fastapi import APIRouter

from tomskit.server.server import FastModule


@dataclass
class ResourceInfo:
    """Resource registration information"""
    resource_cls: type
    path: str
    tags: list[str]


class ResourceRegistry:
    """
    Global resource registry, organized by module name.
    
    Used to store all Resources registered via the @register_resource decorator,
    supporting deferred registration, where resources are registered to their
    corresponding FastModule instances at application startup.
    """
    _modules: dict[str, list[ResourceInfo]] = {}
    
    @classmethod
    def register(
        cls,
        resource_cls: type,
        module_name: str,
        path: str,
        tags: list[str] | None = None,
    ):
        """
        Register a Resource to the specified module.
        
        Args:
            resource_cls: Resource class
            module_name: Module name, must match FastModule.name
            path: Default path for the resource
            tags: Default tags list for the resource
        """
        if module_name not in cls._modules:
            cls._modules[module_name] = []
        cls._modules[module_name].append(
            ResourceInfo(
                resource_cls=resource_cls,
                path=path,
                tags=tags or []
            )
        )
    
    @classmethod
    def get_module_resources(cls, module_name: str) -> list[ResourceInfo]:
        """
        Get all Resources for the specified module.
        
        Args:
            module_name: Module name
        
        Returns:
            List of ResourceInfo for the module
        """
        return cls._modules.get(module_name, [])
    
    @classmethod
    def clear_module(cls, module_name: str):
        """
        Clear registrations for the specified module (mainly for testing).
        
        Args:
            module_name: Module name
        """
        if module_name in cls._modules:
            del cls._modules[module_name]
    
    @classmethod
    def clear_all(cls):
        """Clear all registrations (mainly for testing)"""
        cls._modules.clear()


def register_resource(
    module: str,
    path: str,
    tags: list[str] | None = None,
):
    """
    Decorator: Register a Resource to the specified module.
    
    Resources marked with this decorator will be automatically registered
    when FastModule.auto_register_resources() is called.
    
    Args:
        module: Module name, must match FastModule.name
        path: Default path for the resource
        tags: Default tags list for the resource
    
    Example:
        @register_resource(module="files", path="/files", tags=["File Management"])
        class FileResource(Resource):
            @api_doc(summary="Upload file", response_model=FileResponse)
            async def post(self, request: Request):
                ...
    """
    def decorator(cls):
        ResourceRegistry.register(cls, module, path, tags=tags)
        return cls
    return decorator


def _normalize_responses(responses: dict[int | str, str | dict[str, Any]]) -> dict[int | str, dict[str, Any]]:
    """
    Normalize response format, supporting simplified string format.
    
    Converts simplified format:
        {200: "Success", 400: "Bad Request"}
    to FastAPI expected format:
        {200: {"description": "Success"}, 400: {"description": "Bad Request"}}
    """
    normalized: dict[int | str, dict[str, Any]] = {}
    for status_code, value in responses.items():
        if isinstance(value, str):
            normalized[status_code] = {"description": value}
        elif isinstance(value, dict):
            normalized[status_code] = value
        else:
            normalized[status_code] = {"description": str(value)}
    return normalized


def api_doc(
    summary: str | None = None,
    description: str | None = None,
    response_description: str | None = None,
    deprecated: bool = False,
    operation_id: str | None = None,
    response_model: Any = None,
    status_code: int | None = None,
    responses: dict[int | str, str | dict[str, Any]] | None = None,
    path: str | None = None,
):
    """
    Decorator for setting API documentation information and path for Resource class methods.
    
    Important rules:
    - The same parameter cannot be used repeatedly in multiple @api_doc decorators
      (except responses which can be merged)
    - response_model: Used to specify the BaseModel/Pydantic model for FastAPI API responses
    - path: Method-level path, if provided will override the default path from registration
    - responses can be merged across multiple decorators
    - Other parameters (summary, description, response_model, operation_id, path, etc.)
      will raise an exception if used repeatedly
    - tags should be set in @register_resource, not in @api_doc
    
    Example:
        from pydantic import BaseModel
        
        class UserResponse(BaseModel):
            id: int
            name: str
        
        @register_resource(module="users", path="/users", tags=["User Management"])
        class UserResource(Resource):
            # Method 1: Using simplified string format
            @api_doc(
                summary="Get user list",
                description="Get all users with pagination",
                response_model=list[UserResponse],
                responses={
                    200: "Success",
                    400: "Bad request",
                    404: "Not found"
                }
            )
            async def get(self, request: Request):
                ...
            
            # Method 2: Using full dictionary format
            @api_doc(
                summary="Create user",
                response_model=UserResponse,
                responses={
                    201: {"description": "User created successfully"},
                    400: {"description": "Invalid input data"},
                    409: {"description": "User already exists", "content": {...}}
                }
            )
            async def post(self, request: Request):
                ...
            
            # Method 3: Setting multiple times, responses will be automatically merged
            @api_doc(responses={200: "Success"})
            @api_doc(responses={404: "Not found"})
            @api_doc(responses={500: "Internal server error"})
            @api_doc(
                path="/users/{user_id}",  # Override default path
                summary="Get user details",
                response_model=UserResponse
            )
            async def get(self, request: Request):
                ...
    """
    def decorator(func: Callable) -> Callable:
        # Check for non-mergeable parameters that cannot be repeated
        non_mergeable_params = {
            'summary': summary,
            'description': description,
            'response_description': response_description,
            'response_model': response_model,
            'status_code': status_code,
            'operation_id': operation_id,
            'path': path,
        }
        
        for param_name, param_value in non_mergeable_params.items():
            if param_value is not None:
                attr_name = f'_api_{param_name}'
                if hasattr(func, attr_name):
                    raise ValueError(
                        f"Parameter '{param_name}' has already been set in a previous @api_doc decorator. "
                        f"It cannot be used repeatedly in multiple decorators. Please merge into a single @api_doc."
                    )
        
        # Set parameters
        if summary is not None:
            setattr(func, '_api_summary', summary)
        if description is not None:
            setattr(func, '_api_description', description)
        if response_description is not None:
            setattr(func, '_api_response_description', response_description)
        if response_model is not None:
            setattr(func, '_api_response_model', response_model)
        if status_code is not None:
            setattr(func, '_api_status_code', status_code)
        if operation_id is not None:
            setattr(func, '_api_operation_id', operation_id)
        if path is not None:
            setattr(func, '_api_path', path)
        
        # Merge responses: merge dictionaries instead of overwriting
        if responses is not None:
            existing_responses = getattr(func, '_api_responses', None)
            if existing_responses:
                merged_responses = dict(existing_responses)
                normalized_new = _normalize_responses(responses)
                merged_responses.update(normalized_new)
                setattr(func, '_api_responses', merged_responses)
            else:
                normalized_responses = _normalize_responses(responses)
                setattr(func, '_api_responses', normalized_responses)
        
        if deprecated:
            setattr(func, '_api_deprecated', True)
        
        # Mark method as decorated by api_doc
        setattr(func, '_api_doc_decorated', True)
        
        return func
    return decorator


class Resource:
    """
    RESTful API resource base class.
    
    A Resource represents a resource entity, containing CRUD operations for that resource.
    All methods share the same path (specified during registration), but can be overridden
    via @api_doc(path=...).
    
    Attributes:
        decorators (List[Callable]): Class-level decorator list, applied to all methods.
        methods (List[str]): List of supported HTTP methods.
    """
    decorators: list[Callable] | None = None
    methods: list[str] = ["get", "post", "put", "delete", "patch"]  # Only standard RESTful methods
    
    def __init__(self, router: ResourceRouter):
        self.router = router
        self.app: FastModule = self.router.router_app
    
    def __init_subclass__(cls):
        """
        Called when a subclass is initialized, ensuring methods are properly decorated.
        """
        # If subclass hasn't set decorators, initialize as empty list
        if not hasattr(cls, 'decorators') or cls.decorators is None:
            cls.decorators = []
        super().__init_subclass__()
        cls._decorate_methods()
    
    @classmethod
    def _decorate_methods(cls):
        """
        Apply decorators to methods in the subclass.
        """
        for method_name in cls.methods:
            method = getattr(cls, method_name, None)
            if method:
                decorated = cls.apply_decorators(method)
                setattr(cls, method_name, decorated)
    
    @classmethod
    def apply_decorators(cls, func: Callable) -> Callable:
        """
        Apply decorators to the specified method.
        
        Args:
            func (Callable): Method to be decorated.
        
        Returns:
            Callable: Decorated method.
        """
        if cls.decorators:
            for decorator in reversed(cls.decorators):
                func = decorator(func)
        return func


class ResourceRouter(APIRouter):
    """
    RESTful resource router for registering and managing Resources.
    
    Inherits from FastAPI's APIRouter, specifically designed for handling Resource class registration.
    """
    
    def __init__(self, app: FastModule, *args, **kwargs):
        """
        Initialize ResourceRouter.
        
        Args:
            app (FastModule): FastModule instance, must be provided.
            *args, **kwargs: Other parameters passed to APIRouter.
        """
        self.router_app = app
        if self.router_app is None:
            raise ValueError("The 'app' parameter must be provided.")
        
        super().__init__(*args, **kwargs)
        self._default_dependencies = kwargs.get('dependencies', [])
        # Cache route names for efficient duplicate checking
        self._route_names: set[str] = set()
    
    def check_name_duplicate(self, name: str) -> bool:
        """Check if route name already exists"""
        return name in self._route_names
    
    def add_resource(
        self,
        resource_cls: type[Resource],
        path: str,
        tags: list[str] | None = None,
    ):
        """
        Add Resource to the router.
        
        Args:
            resource_cls (Type[Resource]): Resource class, must inherit from Resource.
            path (str): Default path for the resource. All methods use this path by default,
                unless a method specifies a different path via @api_doc(path=...).
            tags (List[str] | None): Default tags list. Applied to all methods,
                unless a method specifies different tags via @api_doc(tags=...).
        """
        resource_instance = resource_cls(router=self)
        
        # Use tags passed during registration (Resource class no longer has tags attribute)
        class_tags = tags or []
        
        # Standard HTTP methods set for efficient validation
        VALID_HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch'}
        
        # Get all methods decorated with @api_doc
        # Check class methods directly instead of using dir() for better performance
        methods_to_register = []
        for attr_name in resource_cls.methods:
            # Validate method name early
            method_name_lower = attr_name.lower()
            if method_name_lower not in VALID_HTTP_METHODS:
                raise ValueError(
                    f"Method name '{attr_name}' is not a standard HTTP method. "
                    f"Only 'get', 'post', 'put', 'delete', 'patch' are supported. "
                    f"Non-standard method names like 'get_detail' are not allowed."
                )
            
            class_method = getattr(resource_cls, attr_name, None)
            if class_method and callable(class_method) and hasattr(class_method, '_api_doc_decorated'):
                # Get the method from instance to ensure it has the correct bound state
                instance_method = getattr(resource_instance, attr_name, None)
                if instance_method:
                    # Store original method name, lowercase method name, class method, and instance method
                    methods_to_register.append((attr_name, method_name_lower, class_method, instance_method))
        
        if not methods_to_register:
            raise ValueError(
                f"Resource {resource_cls.__name__} has no methods decorated with @api_doc. "
                f"Please add @api_doc decorator to at least one method."
            )
        
        # Register each method
        for original_method_name, method_name_lower, class_method, instance_method in methods_to_register:
            # Apply class-level decorators to instance method
            decorated_method = resource_cls.apply_decorators(instance_method)
            
            # Batch get all method-level documentation attributes from class method
            # (attributes are set on the class method by @api_doc decorator)
            method_path = getattr(class_method, '_api_path', None) or path
            method_summary = getattr(class_method, '_api_summary', None)
            method_description = getattr(class_method, '_api_description', None)
            method_response_model = getattr(class_method, '_api_response_model', None)
            method_status_code = getattr(class_method, '_api_status_code', None)
            method_responses = getattr(class_method, '_api_responses', None)
            method_response_description = getattr(class_method, '_api_response_description', None)
            method_deprecated = getattr(class_method, '_api_deprecated', False)
            method_operation_id = getattr(class_method, '_api_operation_id', None)
            
            # Use tags from register_resource only, not from api_doc
            method_tags = class_tags
            
            # Determine HTTP method (already validated and lowercased)
            http_method = method_name_lower.upper()
            
            # Generate route name using class name and original method name
            route_name = f"{resource_cls.__name__}_{original_method_name}"
            if self.check_name_duplicate(route_name):
                raise ValueError(f"Resource route name {route_name} already exists")
            # Add to cache
            self._route_names.add(route_name)
            
            # Build route parameters
            # Note: FastAPI's APIRouter.add_api_route will automatically prepend
            # the router's prefix to the path. So we pass the path without prefix here.
            route_kwargs: dict[str, Any] = {
                "path": method_path,
                "endpoint": decorated_method,
                "methods": [http_method],
                "name": route_name,
                "dependencies": self._default_dependencies,
            }
            
            # Add documentation-related parameters (only if they have values)
            if method_tags:
                route_kwargs["tags"] = method_tags
            if method_summary:
                route_kwargs["summary"] = method_summary
            if method_description:
                route_kwargs["description"] = method_description
            if method_response_model:
                route_kwargs["response_model"] = method_response_model
            if method_status_code:
                route_kwargs["status_code"] = method_status_code
            if method_responses:
                # method_responses is already normalized in api_doc decorator
                route_kwargs["responses"] = method_responses
            if method_response_description:
                route_kwargs["response_description"] = method_response_description
            if method_deprecated:
                route_kwargs["deprecated"] = True
            if method_operation_id:
                route_kwargs["operation_id"] = method_operation_id
            
            self.add_api_route(**route_kwargs)
