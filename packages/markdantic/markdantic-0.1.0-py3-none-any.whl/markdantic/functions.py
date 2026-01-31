from enum import Enum
from typing import Any, get_args, get_origin

from pydantic import fields
from pydantic_core import PydanticUndefined


def type_to_fqcn(annotation: object) -> str:
    """型を参照してFQCN文字列を返す.

    Args:
        annotation (object): 型

    Returns:
        (str): FQCN文字列

    """
    origin = get_origin(annotation)

    # --- 単体（クラス/Enum/builtins/None/Any等）---
    if origin is None:
        # NoneType -> None
        if annotation is type(None):
            return "None"

        # typing.Any -> Any
        if annotation is Any:
            return "Any"

        # 普通のクラス、Enum、builtins
        mod = getattr(annotation, "__module__", None)
        qn = getattr(annotation, "__qualname__", None)

        if isinstance(mod, str):
            # Python 3.13以降対応
            for suffix in (".__init__", "._local", "._internal", "._impl", "._types"):
                if mod.endswith(suffix):
                    mod = mod[: -len(suffix)]
                    break

        if isinstance(mod, str) and isinstance(qn, str):
            if mod == "builtins":
                return qn  # int, str, list など
            return f"{mod}.{qn}"

        # それ以外は文字列化で逃げる
        return str(annotation)

    args = get_args(annotation)

    # --- コンテナ ---
    if origin in (list,):
        return f"list[{type_to_fqcn(args[0])}]"

    if origin in (dict,):
        return f"dict[{type_to_fqcn(args[0])}, {type_to_fqcn(args[1])}]"

    if origin in (set,):
        return f"set[{type_to_fqcn(args[0])}]"

    if origin in (tuple,):
        if len(args) == 2 and args[1] is Ellipsis:
            return f"tuple[{type_to_fqcn(args[0])}, ...]"
        return "tuple[" + ", ".join(type_to_fqcn(a) for a in args) + "]"

    # --- Union / Optional / その他 ---
    return r"|".join(type_to_fqcn(a) for a in args)


def default_to_md(field: fields.FieldInfo) -> str:
    """オプションフィールドのデフォルト表記を返す

    Args:
        field (fields.FieldInfo): フィールド情報

    Returns:
        (str): デフォルト表記

    """
    if field.is_required():
        return ""
    if field.default_factory is list:
        return "[]"
    if field.default_factory is dict:
        return "{}"
    if field.default_factory is not None:
        df = field.default_factory
        name = getattr(df, "__name__", df.__class__.__name__)
        return f"{name}()"
    if field.default is not PydanticUndefined:
        return repr(field.default)
    return ""


def enum_to_choices(annotation: Any | None) -> str | None:
    """Enum型だったらメンバー名を展開する

    Args:
        annotation (Any | None): 型

    Returns:
        (str | None): 展開した文字列(Enum以外はNone)

    """
    # 合成型（list/dict/Union/etc）は弾く
    if get_origin(annotation) is not None:
        return None

    # 直接Enumだけ展開する
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        parts = []
        for m in annotation:
            parts.append(f"{m.value}=`{m.name}`")
        return "(members: " + ", ".join(parts) + ")"

    return None
