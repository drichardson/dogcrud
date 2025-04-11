from collections.abc import AsyncGenerator

from dogcrud.core.pagination import CursorDataItemModel, CursorPagination


async def list_metrics(semaphore) -> AsyncGenerator[CursorDataItemModel]:
    # data[i].attributes is only set when filter[configured]=true is set,
    # so do 2 paginations—one with false and one with true—in order to get
    # the attributes.
    for configured in ("false", "true"):
        paginator = CursorPagination(query_params=f"filter[configured]={configured}")
        async for page in paginator.pages("api/v2/metrics", semaphore):
            for item in page.data:
                yield item
