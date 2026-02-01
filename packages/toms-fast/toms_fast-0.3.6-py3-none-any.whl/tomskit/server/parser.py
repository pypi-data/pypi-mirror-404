from typing import (
    Any, Dict, List, Literal, Mapping, Optional, Type, get_args, get_origin
)

from fastapi import HTTPException, Request, UploadFile
from starlette.datastructures import FormData
from pydantic import (
    BaseModel, ConfigDict, Field, ValidationError, create_model, TypeAdapter
)


class ParserModel(BaseModel):
    """
    Base model that allows extra fields and dictionary‐style access.
    """
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        arbitrary_types_allowed=True # ← 允许任意类作为字段类型
    )

    def __getitem__(self, key: str) -> Any:
        if key == "model_config":
            key = "model_config_field"
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "model_config":
            key = "model_config_field"
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "model_config":
            key = "model_config_field"
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        if key == "model_config":
            key = "model_config_field"
        return hasattr(self, key)
    
    def to_mapping(self) -> Mapping[str, Any]:
        return self.model_dump(by_alias=True)

class RequestParser:
    """
    A Flask-RESTful-like request parser built on FastAPI + Pydantic v2.
    Supports:
      - JSON, query, form, header, cookie, path parameters
      - store/append/count actions
      - required/default/nullable/choices semantics
      - automatic TypeAdapter validation for built-ins, Annotated, custom types
      - UploadFile and List[UploadFile]
    """
    # 类级缓存：parser_id -> 模型类
    _model_cache: Dict[str, Type[ParserModel]] = {}

    # 允许的 action
    ALLOWED_ACTIONS = {"store", "append", "count"}

    # 允许的 location
    ALLOWED_LOCATIONS = {"args", "json", "form", "header", "cookie", "path"}

    def __init__(self, parser_id: Optional[str] = None) -> None:
        self._parser_id = parser_id
        self._arg_defs: List[Dict[str, Any]] = []
        self._model_cls: Optional[Type[ParserModel]] = None

    def add_argument(
        self,
        name: str,
        arg_type: Any,
        required: bool = False,
        default: Any = None,
        choices: Optional[List[Any]] = None,
        nullable: bool = False,
        location: Literal["args", "json", "form", "header", "cookie", "path"] = "json",
        action: Literal["store", "append", "count"] = "store",
        help: Optional[str] = None,
    ) -> None:
        """
        Register a new argument.
        Raises ValueError on invalid configuration.
        """
        if not name or not isinstance(name, str):
            raise ValueError("RequestParser: `name` must be a non-empty string")
        if action not in self.ALLOWED_ACTIONS:
            raise ValueError(f"RequestParser: `action` must be one of {self.ALLOWED_ACTIONS}")
        if location not in self.ALLOWED_LOCATIONS:
            raise ValueError(f"RequestParser: `location` must be one of {self.ALLOWED_LOCATIONS}")
        if choices is not None and not isinstance(choices, list):
            raise ValueError("RequestParser: `choices` must be a list if provided")
        if required and default is not None:
            raise ValueError("RequestParser: `default` must be None when `required=True`")
        if not required and default is None and not nullable:
            raise ValueError("RequestParser: `default=None` with `required=False` requires `nullable=True`")
        if choices and default is not None and default not in choices:
            raise ValueError("RequestParser: `default` must be one of `choices`")

        # Validate that arg_type is supported by Pydantic
        try:
            adapter = TypeAdapter(arg_type)
        except Exception as e:
            raise ValueError(f"RequestParser: Invalid arg_type for '{name}': {e}")

        # Validate default value with the same adapter
        if default is not None:
            try:
                adapter.validate_python(default)
            except ValidationError as e:
                raise ValueError(f"RequestParser: Invalid default for '{name}': {e}")

        # Validate each choice
        for choice in (choices or []):
            try:
                adapter.validate_python(choice)
            except ValidationError as e:
                raise ValueError(f"RequestParser: Invalid choice {choice!r} for '{name}': {e}")

        self._arg_defs.append({
            "name": name,
            "type": arg_type,
            "required": required,
            "default": default,
            "choices": choices or [],
            "nullable": nullable,
            "location": location,
            "action": action,
            "help": help,
        })

    def _build_model(self) -> Type[ParserModel]:
        """
        Dynamically create a Pydantic model class based on registered arguments.
        """

        if self._parser_id is not None:
            cached = RequestParser._model_cache.get(self._parser_id)
            if cached is not None:
                return cached

        fields: Dict[str, Any] = {}

        for d in self._arg_defs:
            name = d["name"]
            base_type = d["type"]
            action = d["action"]
            
            # Determine annotation and default
            ann: Any = None
            if action == "append":
                if get_origin(base_type) is list:
                    item_type = get_args(base_type)[0]
                else:
                    item_type = base_type
                ann = List[item_type]  # type: ignore
                default = d["default"] if d["default"] is not None else []
            elif action == "count":
                ann = int
                default = 0
            else:  # store
                ann = base_type
                default = ... if d["required"] and d["default"] is None else d["default"]

            # nullable → Optional
            if d["nullable"]:
                ann = Optional[ann]  # type: ignore

            # choices → Literal
            if d["choices"]:
                # ann = Literal[tuple(d["choices"])]  # type: ignore
                ann = Literal.__getitem__(tuple[Any, ...](d["choices"]))

            internal_name = name
            field_kwargs = {}
            if name == "model_config":
                internal_name = "model_config_field"
                field_kwargs["alias"] = "model_config"

            metadata: Dict[str, Any] = {}
            if d["help"]:
                metadata["description"] = d["help"]

            pydantic_field_kwargs = {**metadata, **field_kwargs}

            fields[internal_name] = (ann, Field(default, **pydantic_field_kwargs))

        try:
            cached_model = create_model("ParsedModel", __base__=ParserModel, **fields)
        except Exception as e:
            raise RuntimeError(f"RequestParser: Failed to create parser model: {e}")
        if self._parser_id is not None:
            RequestParser._model_cache[self._parser_id] = cached_model
        return cached_model  # type: ignore

    async def parse_args(self, request: Request) -> ParserModel:
        """
        Extract raw values from Request by location, merge per action,
        then validate & coerce via the generated Pydantic model.
        Raises HTTPException(422) on validation errors.
        """
        if self._model_cls is None:
            self._model_cls = self._build_model()

        # 1) 根据 Content-Type 决定是否解析 form
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("multipart/form-data") or \
           content_type.startswith("application/x-www-form-urlencoded"):
            try:
                form = await request.form()
            except Exception:
                form = FormData()
        else:
            form = FormData()

        # 2) JSON 解析（仅在不是表单或 multipart 时才尝试）
        try:
            json_body = await request.json()
            json_body = json_body if isinstance(json_body, dict) else {}
        except Exception:
            json_body = {}

        # 3) 其余数据源
        query = dict(request.query_params)
        headers = dict(request.headers)
        cookies = request.cookies
        path_params = request.path_params

        raw: Dict[str, Any] = {}

        # 2) extract & merge
        for d in self._arg_defs:
            key = d["name"]
            loc = d["location"]
            action = d["action"]
            value: Any = None
            value = [] if action == "append" else 0 if action == "count" else None
            present = False

            if loc == "args" and key in query:
                present = True
                value = self._merge(value, query[key], action)

            elif loc == "json" and key in json_body:
                present = True
                value = self._merge(value, json_body[key], action)

            elif loc == "form":
                # 多文件
                if get_origin(d["type"]) is list and get_args(d["type"])[0] is UploadFile:
                    fl = form.getlist(key)  # type: ignore[attr-defined]
                    if fl:
                        present = True
                        for f in fl:
                            value = self._merge(value, f, action)
                # 单文件
                elif d["type"] is UploadFile:
                    fl = form.getlist(key)  # type: ignore[attr-defined]
                    if fl:
                        present = True
                        # 如果想严格单文件，可检查 len(fl)>1
                        value = self._merge(value, fl[0], action)
                # 普通表单字段
                elif key in form:
                    present = True
                    value = self._merge(value, form[key], action)

            elif loc == "header" and key in headers:
                present = True
                value = self._merge(value, headers[key], action)

            elif loc == "cookie" and key in cookies:
                present = True
                value = self._merge(value, cookies[key], action)

            elif loc == "path" and key in path_params:
                present = True
                value = self._merge(value, path_params[key], action)

            # 仅当请求里确实提供过这个字段时，才把它塞进 raw
            if present:
                raw[key] = value

        # 3. 交给 Pydantic 去补默认 & 验证
        try:
            # Pydantic v2 用 model_validate
            return self._model_cls.model_validate(raw)  # type: ignore
        except ValidationError as e:
            # 格式化错误，使运维快速定位字段与原因
            error_messages = []
            for err in e.errors():
                loc = ".".join(str(x) for x in err.get("loc", []))
                msg = err.get("msg", "")
                err_type = err.get("type", "")
                inp = err.get("input", None)
                error_messages.append(
                    f"RequestParser: Field '{loc}': {msg} (type={err_type}, input={inp!r})"
                )
            # 最终把格式化后的信息放到 detail 里
            raise HTTPException(status_code=422, detail={"errors": error_messages})

    @staticmethod
    def _merge(prev: Any, new: Any, action: str) -> Any:
        """Merge raw values according to action."""
        if action == "store":
            return new
        if action == "append":
            lst = prev if isinstance(prev, list) else []
            lst.append(new)
            return lst
        # count
        return (prev or 0) + 1
