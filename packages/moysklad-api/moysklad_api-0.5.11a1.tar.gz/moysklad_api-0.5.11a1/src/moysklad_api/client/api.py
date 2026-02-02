from datetime import date, datetime

from ..client.base import PRODUCTION
from ..client.session import BaseSession, Headers, Method
from ..enums import GroupBy, QuantityMode, StockMode, StockType
from ..filters.base import BaseFilter
from ..methods import (
    GetAssortment,
    GetAudit,
    GetBonusTransaction,
    GetBonusTransactions,
    GetCounterparty,
    GetCurrentStock,
    GetEvents,
    GetProduct,
    GetProducts,
    GetProfit,
    GetPurchaseOrder,
    GetPurchaseOrders,
    GetStock,
    GetToken,
    GetVariant,
    GetVariants,
    GetWebhook,
    GetWebhooks,
    MSMethod,
    T,
    UpdateProduct,
    UpdateProducts,
    UpdateVariant,
    UpdateVariants,
)
from ..methods.base import R
from ..methods.get_counterparties import GetCounterparties
from ..methods.get_demand import GetDemand
from ..methods.get_demands import GetDemands
from ..types import (
    Assortment,
    Audit,
    BonusTransaction,
    Counterparty,
    CurrentStock,
    Demand,
    Event,
    MetaArray,
    Product,
    Profit,
    PurchaseOrder,
    Stock,
    Token,
    Variant,
    Webhook,
)
from ..utils.token import validate_token


class MoyskladAPI:
    def __init__(self, token: str, session: BaseSession | None = None, **kwargs):
        """
        Клиент для работы с API МойСклад

        Attributes:

            token: Токен доступа

                Источник: https://api.moysklad.ru/api/remap/1.2/security/token
        """
        validate_token(token)
        if session is None:
            read_timeout = kwargs.get("read_timeout", 60)
            session = BaseSession(
                base=PRODUCTION.url,
                timeout=read_timeout,
            )

        self.__token = token
        self._session_headers = self._create_session_headers(self.__token)
        self._session = session
        self._session.headers = self._session_headers

    @property
    def session(self) -> BaseSession:
        return self._session

    @property
    def base(self) -> str:
        return self._session.base

    @property
    def timeout(self) -> int:
        return self._session.timeout

    @property
    def token(self) -> str:
        return self.__token

    async def close(self):
        await self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import asyncio

        asyncio.run(self.close())

    async def __call__(
        self, method: MSMethod[T], self_method: Method | None = Method.GET
    ) -> T | R:
        return await method.call(self.session, self_method)

    async def get_token(self, username: str, password: str) -> Token:
        call = GetToken(
            username=username,
            password=password,
        )
        return await self(call)

    @staticmethod
    def _create_session_headers(token: str) -> Headers:
        return Headers(token=token)

    async def get_assortment(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
        group_by: GroupBy | None = None,
    ) -> MetaArray[Assortment]:
        """
        Используйте этот метод для получения ассортимента.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/assortment#2-assortiment

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :param group_by: Параметр группировки
        :return: :class:`MetaArray[Assortment]`
        """
        call = GetAssortment(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
            group_by=group_by,
        )
        return await self(call)

    async def get_bonustransaction(
        self,
        bonustransaction_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> BonusTransaction:
        """
        Используйте этот метод для получения бонусной операции по ID.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/bonus-operation#3-poluchit-bonusnye-operacii

        :param bonustransaction_id: Идентификатор бонусной операции
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`BonusTransaction`
        """
        call = GetBonusTransaction(
            bonustransaction_id=bonustransaction_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_bonustransactions(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> MetaArray[BonusTransaction]:
        """
        Используйте этот метод для получения бонусных операций.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/bonus-operation#3-poluchit-bonusnye-operacii

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`MetaArray[BonusTransaction]`
        """
        call = GetBonusTransactions(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_counterparty(
        self,
        counterparty_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> Counterparty:
        """
        Используйте этот метод для получения контрагента по ID.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/counterparty#3-poluchit-kontragenta

        :param counterparty_id: Идентификатор контрагента
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`Counterparty`
        """
        call = GetCounterparty(
            counterparty_id=counterparty_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_counterparties(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> MetaArray[Counterparty]:
        """
        Используйте этот метод для получения списка контрагентов.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/counterparty#3-poluchit-spisok-kontragentov

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`MetaArray[Counterparty]`
        """
        call = GetCounterparties(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_product(
        self,
        product_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> Product:
        """
        Используйте этот метод для получения товара по ID.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/product#3-zaprosy-tovar

        :param product_id: Идентификатор товара
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`Product`
        """
        call = GetProduct(
            product_id=product_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_products(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> MetaArray[Product]:
        """
        Используйте этот метод для получения списка товаров.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/product#3-poluchit-spisok-tovarov

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`MetaArray[Product]`
        """
        call = GetProducts(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def update_product(
        self,
        product_id: str,
        product: Product,
    ) -> Product:
        """
        Используйте этот метод для обновления товара

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/product#3-izmenit-tovar

        :return: :class:`Product`
        """
        call = UpdateProduct(
            product_id=product_id,
            data=product,
        )
        return await self(call, self_method=Method.PUT)

    async def update_products(self, products: list[Product]) -> list[Product]:
        """
        Используйте этот метод для массового обновления товаров

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/product#3-massovoe-sozdanie-i-obnovlenie-tovarov

        :return: :class:`list[Product]`
        """
        call = UpdateProducts(
            data=products,
        )
        return await self(call, self_method=Method.POST)

    async def get_stock(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
        stock_mode: StockMode = StockMode.ALL,
        quantity_mode: QuantityMode = QuantityMode.NON_EMPTY,
    ) -> MetaArray[Stock]:
        """
        Используйте этот метод для получения расширенного отчета об остатках.

        Источники: https://dev.moysklad.ru/doc/api/remap/1.2/#/reports/report-stock#3-kratkij-otchet-ob-ostatkah

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :param stock_mode: Режим фильтрации по остатку для расширенного отчета
        :param quantity_mode: Режим фильтрации по количеству
        :return: :class:`MetaArray[Stock]`
        """
        call = GetStock(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
            stock_mode=stock_mode,
            quantity_mode=quantity_mode,
        )
        return await self(call)

    async def get_current_stock(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
        include_zero_lines: bool = False,
        changed_since: datetime | None = None,
        stock_type: StockType = StockType.STOCK,
    ) -> CurrentStock:
        """
        Используйте этот метод для получения краткого отчета об остатках.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/reports/report-stock#3-kratkij-otchet-ob-ostatkah

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :param include_zero_lines: Включать позиции с нулевым остатком
        :param changed_since: Получить остатки, которые изменились с указанного момента
        :param stock_type: Тип рассчитываемого остатка
        :return: :class:`CurrentStock`
        """
        call = GetCurrentStock(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
            include="zeroLines" if include_zero_lines else None,
            changed_since=changed_since,
            stock_type=stock_type,
        )
        return await self(call)

    async def get_demand(
        self,
        demand_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> Demand:
        """
        Используйте этот метод для получения отгрузки по ID.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/documents/demand#3-poluchit-otgruzku


        :param demand_id: Идентификатор отгрузки
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`Demand`
        """
        call = GetDemand(
            demand_id=demand_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_demands(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> MetaArray[Demand]:
        """
        Используйте этот метод для получения списка отгрузок.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/documents/demand#3-poluchit-spisok-otgruzok

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`MetaArray[Demand]`
        """
        call = GetDemands(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_audit(
        self,
        audit_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> Audit:
        """
        Используйте этот метод для получения аудита (контекста) по ID.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/audit/audit#3-poluchit-konteksty

        :param audit_id: Идентификатор аудита
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`Audit`
        """
        call = GetAudit(
            audit_id=audit_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_audit_events(
        self,
        audit_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> MetaArray[Event]:
        """
        Используйте этот метод для получения событий аудита (контекста).

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/audit/audit#3-poluchit-sobytiya-po-kontekstu

        :param audit_id: Идентификатор аудита
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`MetaArray[Event]`
        """
        call = GetEvents(
            audit_id=audit_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_webhook(
        self,
        webhook_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> Webhook:
        """
        Используйте этот метод для получения вебхука по ID.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/workbook/workbook-webhooks#3-kak-ispolzovat-vebhuki-cherez-json-api

        :param webhook_id: Идентификатор вебхука
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`Webhook`
        """
        call = GetWebhook(
            webhook_id=webhook_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_webhooks(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> Webhook:
        """
        Используйте этот метод для получения списка вебхуков.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/workbook/workbook-webhooks#3-kak-ispolzovat-vebhuki-cherez-json-api

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`Webhook`
        """
        call = GetWebhooks(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_purchaseorder(
        self,
        purchaseorder_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> PurchaseOrder:
        """
        Используйте этот метод для получения заказа поставщику по ID.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/documents/purchaseOrder#3-poluchit-zakaz-postavshiku

        :param purchaseorder_id: Идентификатор заказа поставщику
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`PurchaseOrder`
        """
        call = GetPurchaseOrder(
            purchaseorder_id=purchaseorder_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_purchaseorders(
        self,
        limit: int | None = 1000,
        offset: int | None = None,
        search: str | None = None,
        expand: tuple[str, ...] | str | None = None,
        filters: BaseFilter | tuple[BaseFilter, ...] | None = None,
    ) -> MetaArray[PurchaseOrder]:
        """
        Используйте этот метод для получения заказов поставщику.

         Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/documents/purchaseOrder#3-poluchit-spisok-zakazov-postavshikam

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param search: Контекстный поиск
        :param expand: Замена ссылок объектами
        :return: :class:`MetaArray[PurchaseOrder]`
        """
        call = GetPurchaseOrders(
            limit=limit,
            offset=offset,
            search=search,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_profit_by_variant(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
        moment_from: str | date | datetime | None = None,
        moment_to: str | date | datetime | None = None,
    ) -> MetaArray[Profit]:
        """
        Используйте этот метод для получения отчета прибыльности по модификациям.

        При отсутствии ``moment_from`` и ``moment_to`` отображаются отчеты за последний месяц.
        При отсутствии ``moment_from`` и указании ``moment_to`` отображаются отчеты
        с начала текущего года по ``moment_to``.
        При отсутствии ``moment_to`` и указании ``moment_from`` отображаются отчеты
        с ``moment_from`` по текущий день.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/reports/report-pnl#2-otchet-pribylnost

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :param moment_from: Начало периода
        :param moment_to: Конец периода
        :return: :class:`MetaArray[Profit]`
        """
        call = GetProfit(
            type="variant",
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
            moment_from=moment_from,
            moment_to=moment_to,
        )
        return await self(call)

    async def get_profit_by_product(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
        moment_from: str | date | datetime | None = None,
        moment_to: str | date | datetime | None = None,
    ) -> MetaArray[Profit]:
        """ "
        Используйте этот метод для получения отчета прибыльности по товарам.

        При отсутствии ``moment_from`` и ``moment_to`` отображаются отчеты за последний месяц.
        При отсутствии ``moment_from`` и указании ``moment_to`` отображаются отчеты
        с начала текущего года по ``moment_to``.
        При отсутствии ``moment_to`` и указании ``moment_from`` отображаются отчеты
        с ``moment_from`` по текущий день.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/reports/report-pnl#2-otchet-pribylnost

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :param moment_from: Начало периода
        :param moment_to: Конец периода
        :return: :class:`MetaArray[Profit]`
        """
        call = GetProfit(
            type="product",
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
            moment_from=moment_from,
            moment_to=moment_to,
        )
        return await self(call)

    async def get_variant(
        self,
        variant_id: str,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> Variant:
        """
        Используйте этот метод для получения модификации по ID.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/variant#3-modifikacii

        :param variant_id: Идентификатор модификации
        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`Variant`
        """
        call = GetVariant(
            variant_id=variant_id,
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def get_variants(
        self,
        *filters: BaseFilter,
        limit: int | None = 1000,
        offset: int | None = None,
        expand: tuple[str, ...] | str | None = None,
    ) -> MetaArray[Variant]:
        """
        Используйте этот метод для получения списка модификаций.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/variant#3-poluchit-spisok-modifikacij

        :param filters: Фильтрация выборки
        :param limit: Количество элементов в выданном списке
        :param offset: Отступ в выданном списке
        :param expand: Замена ссылок объектами
        :return: :class:`MetaArray[Variant]`
        """
        call = GetVariants(
            limit=limit,
            offset=offset,
            expand=expand,
            filters=filters,
        )
        return await self(call)

    async def update_variant(
        self,
        variant_id: str,
        variant: Variant,
    ) -> Variant:
        """
        Используйте этот метод для обновления модификации.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/variant#3-izmenit-modifikaciyu

        :return: :class:`Variant`
        """
        call = UpdateVariant(
            variant_id=variant_id,
            data=variant,
        )
        return await self(call, self_method=Method.PUT)

    async def update_variants(self, variants: list[Variant]) -> list[Variant]:
        """
        Используйте этот метод для массового обновления модификаций.

        Источник: https://dev.moysklad.ru/doc/api/remap/1.2/#/dictionaries/variant#3-massovoe-sozdanie-i-obnovlenie-modifikacij

        :return: :class:`list[Variant]`
        """
        call = UpdateVariants(
            data=variants,
        )
        return await self(call, self_method=Method.POST)
