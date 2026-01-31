import inspect

from jinja2 import Environment, PackageLoader
from pydantic import BaseModel

from markdantic.functions import default_to_md, enum_to_choices, type_to_fqcn
from markdantic.models import FieldDoc, ModelDoc

# テンプレートエンジンの設定
env = Environment(loader=PackageLoader("markdantic", "templates"), auto_reload=False, autoescape=True)


def generator(m: type[BaseModel]) -> str:
    """Pydanticのモデル定義からMarkdown形式のテキストを生成.

    Args:
        m (type[BaseModel]): Pydanticのモデル

    Returns:
        (str): Markdownテキスト

    """
    # テンプレートエンジンに渡す情報の初期化
    model = ModelDoc(
        name=m.__name__,
        base=m.__bases__[0].__name__,
        doc=inspect.cleandoc(m.__doc__ or ""),
        fields=[],
    )

    for name, field in m.model_fields.items():
        # 型表記を取得する
        type = type_to_fqcn(field.annotation)

        # デフォルト値を取得する
        default = default_to_md(field)

        # 説明にEnumの内容を追加する
        base_dscr = field.description or ""
        if s := enum_to_choices(field.annotation):
            description = f"{base_dscr} {s}"
        else:
            description = base_dscr

        # パラメータの情報をデータクラスに格納してリストに追記する
        model.fields.append(
            FieldDoc(
                name=name,
                type=type.replace("|", "｜"),  #  テーブル破壊防止
                description=description.replace("|", "｜"),  # テーブル破壊帽子
                required=field.is_required(),
                default=default,
            )
        )

    # テンプレートエンジンによるレンダリング
    template = env.get_template("model.md.j2")
    return template.render(model=model)
