# Markdantic

## 概要

Pydantic の型情報を元に mkdocs 等で使用する Markdown 形式のテキストデータを出力する。
このとき、**mkdocstrings では表現しきれない型情報を、ロスレスに Markdown 化する**ことを目的とする。

## デザインポリシー

本ツールは「見た目よりも型情報の正確さ」を最優先とする。

- 型は完全修飾クラス (FQCN) でレンダリングする
- 組み込み型 (int, str, list, None など) は読みやすさを考慮して短縮形でレンダリングする
- 出力の整形や短縮は行わず、ロスレスな情報提供を優先する
- Markdown レンダラーとの互換性を優先する
- テーブルの破損を防ぐため、半角のパイプ記号を全角に変換する

## 非対応・割り切り

- Markdown の装飾最適化（見栄え調整）は行わない
- 出力結果の整形・短縮は利用者側で後処理することを前提とする
- HTML や PDF の直接生成は対象外とする

## Enum の展開

- 通常の Enum
- 数値ベースの Enum (IntEnum)

"メンバー値=メンバー名" を展開して description の末尾に出力する。

## 使用例

mkdocs / mkdocstrings 等での利用を想定した例：

### コード

`enums.py`

```python
from enum import Enum

class Area(Enum):
    TOKYO = 1
    OSAKA = 2
```

`models.py`

```python
from pathlib import Path
from pydantic import BaseModel, Field
from enums import Area

class SampleModel(BaseModel):
    """テストのモデル"""
    num:   int | None = Field(None, description="Number of Files")
    name:  str        = Field("", description="Name")
    files: list[Path] = Field(default_factory=list, description="list of Path")
    view:  bool       = Field(False, description="View flag")
    area:  Area       = Field(..., description="Area")
```

`main.py`

```python
from markdantic import generator
from models import SampleModel

print(generator(SampleModel))
```

### 出力

以下は `main.py` を実行して生成されるMarkdownの例：

```txt
## `SampleModel`

**Base:** `BaseModel`

テストのモデル

**Parameters:**

|Name|Type|Description|Default|
|---|---|---|---|
|`num`|`int｜None`|Number of Files|`None`|
|`name`|`str`|Name|`''`|
|`files`|`list[pathlib.Path]`|list of Path|`[]`|
|`view`|`bool`|View flag|`False`|
|`area`|`enums.Area`|Area (members: 1=`TOKYO`, 2=`OSAKA`)|_Required_|
```

テーブル部分のレンダリング結果：

|Name|Type|Description|Default|
|---|---|---|---|
|`num`|`int｜None`|Number of Files|`None`|
|`name`|`str`|Name|`''`|
|`files`|`list[pathlib.Path]`|list of Path|`[]`|
|`view`|`bool`|View flag|`False`|
|`area`|`enums.Area`|Area (members: 1=`TOKYO`, 2=`OSAKA`)|_Required_|

## インストール方法

```bash
pip install markdantic
```

uv を使用する場合：

```bash
uv add markdantic
```

※ PyPI で公開予定。
