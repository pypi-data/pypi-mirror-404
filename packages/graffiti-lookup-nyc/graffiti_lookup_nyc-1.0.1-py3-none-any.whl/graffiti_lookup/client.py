import asyncio
import logging

from bs4 import BeautifulSoup
import httpx

from graffiti_lookup.models import ServiceRequest

logger = logging.getLogger(__name__)


class GraffitiLookup:
    """NYC Graffiti removal request lookup service"""

    NYC_GRAFFITI_LOOKUP_URL = (
        "https://a002-oomwap.nyc.gov/TagOnline/Shared/CannotRespond?sr="
    )
    ID_FIELD = ServiceRequest.ID_FIELD

    def __init__(self):
        self.client = httpx.AsyncClient()

    @staticmethod
    def _convert_to_snake_case(text=""):
        return "_".join(text.split()).lower()

    @staticmethod
    def _sanitize_id(id=""):
        if id.startswith("G"):
            return id[1:]
        return id

    async def _request(self, method, url, **kwargs):
        return await self.client.request(method, url, **kwargs)

    def _parse_record_from_html(self, html, id):
        parsed_html = BeautifulSoup(html, features="html.parser")
        outer_table = parsed_html.select_one(".txtBox")

        if not outer_table:
            logger.error(
                "Unable to parse graffiti lookup rows from html table", extra={"id": id}
            )
            return {}

        data_table = outer_table.select_one(".withBorder")

        if not data_table:
            logger.error(
                "Unable to parse graffiti lookup rows from html table", extra={"id": id}
            )
            return {}

        rows = data_table.find_all("tr")

        record = {}

        for row in rows:
            columns = row.find_all("td")
            key = None

            for index, column in enumerate(columns):
                text = column.get_text().strip()

                if index == 0 and text:
                    key = self._convert_to_snake_case(text)
                    record[key] = None

                if key and index > 0:
                    record[key] = text

        return record

    async def get_status_by_id(self, id="", close_connection=True):
        sanitized_id = self._sanitize_id(id)
        response = await self._request(
            "GET", f"{self.NYC_GRAFFITI_LOOKUP_URL}{sanitized_id}"
        )

        if close_connection:
            await self.client.aclose()

        if response.status_code == 200 and response.content:
            raw_record = self._parse_record_from_html(response.content, sanitized_id)
            service_request = ServiceRequest(**raw_record)
            return service_request.to_dict()
        return {}

    async def get_statuses_by_id(self, ids=[]):
        tasks = [
            asyncio.create_task(self.get_status_by_id(id, close_connection=False))
            for id in ids
        ]
        responses = await asyncio.gather(*tasks)

        await self.client.aclose()
        return responses
