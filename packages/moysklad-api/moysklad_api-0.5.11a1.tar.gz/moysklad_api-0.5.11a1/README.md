<p align="center">
  <a href="https://api.moysklad.ru"><img src="https://www.moysklad.ru/upload/logos/logoMS500.png" alt="MoyskladAPI"></a>
</p>

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/moysklad-api.svg)](https://pypi.org/project/moysklad-api/)
[![Downloads](https://img.shields.io/pypi/dm/moysklad-api.svg)](https://pypi.python.org/pypi/moysklad-api)
[![Status](https://img.shields.io/badge/status-pre--alpha-8B5CF6.svg?logo=git&logoColor=white)]()
[![API Version](https://img.shields.io/badge/Мой_Склад_API-1.2-blue.svg)](https://dev.moysklad.ru/doc/api/remap/1.2/)

</div>

> [!CAUTION]
> Библиотека находится в активной разработке и 100% **не рекомендуется для использования в продакшн среде**.

## Установка

```console
pip install moysklad-api
```

## Пример использования

```Python
import asyncio

from moysklad_api import MoyskladAPI, F

ms_api = MoyskladAPI(token="token")


async def main():
    """
    Получение архивных товаров с пустым описанием
    и заменой ссылки на поставщика объектом.

    `limit=None` — загрузить все элементы без ограничения.
    """
    products = await ms_api.get_products(
        F.archived == True,
        F.description.empty(),
        expand="supplier",
        limit=None
    )
    for product in products.rows:
        print(product.code)


if __name__ == "__main__":
    asyncio.run(main())
```
