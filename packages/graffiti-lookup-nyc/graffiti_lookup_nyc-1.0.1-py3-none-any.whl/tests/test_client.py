from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from graffiti_lookup.client import GraffitiLookup


class TestGraffitiLookup:

    def setup_method(self):
        self.graffiti_lookup = GraffitiLookup()

    def test_sanitize_id(self):
        assert self.graffiti_lookup._sanitize_id("G12345") == "12345"
        assert self.graffiti_lookup._sanitize_id("12345") == "12345"

    def test_convert_to_snake_case(self):
        assert (
            self.graffiti_lookup._convert_to_snake_case("Service Request")
            == "service_request"
        )
        assert (
            self.graffiti_lookup._convert_to_snake_case("Last Updated")
            == "last_updated"
        )

    def test_parse_no_outer_table_returns_empty(self):
        html = "<div><p>No table here</p></div>"
        result = self.graffiti_lookup._parse_record_from_html(html, "G000")
        assert result == {}

    def test_parse_no_data_table_returns_empty(self):
        html = '<div class="txtBox"><p>Missing inner table</p></div>'
        result = self.graffiti_lookup._parse_record_from_html(html, "G001")
        assert result == {}

    def test_sanitize_id_lowercase_g_not_stripped(self):
        assert self.graffiti_lookup._sanitize_id("g123") == "g123"

    def test_parse_rows_with_missing_values(self):
        html = b"""
        <div class=\"txtBox\">
          <table class=\"withBorder\">
            <tr><td>Service Request</td><td></td></tr>
            <tr><td>Address</td><td></td></tr>
          </table>
        </div>
        """
        record = self.graffiti_lookup._parse_record_from_html(html, "G002")
        assert record.get("service_request") == ""
        assert record.get("address") == ""

    def test_parse_record_from_html(self):
        html = """
        <div class="txtBox">
          <table class="withBorder">
            <tr><td>Service Request</td><td>G12345</td></tr>
            <tr><td>Address</td><td>123 MAIN ST, QUEENS</td></tr>
            <tr><td>Created</td><td>01/02/2020</td></tr>
            <tr><td>Last Updated</td><td>01/03/2020</td></tr>
            <tr><td>Status</td><td>Cleaning crew dispatched. Property cleaned.</td></tr>
          </table>
        </div>
        """
        record = self.graffiti_lookup._parse_record_from_html(html, "G12345")

        expected_record = {
            "service_request": "G12345",
            "address": "123 MAIN ST, QUEENS",
            "created": "01/02/2020",
            "last_updated": "01/03/2020",
            "status": "Cleaning crew dispatched. Property cleaned.",
        }

        assert record == expected_record

    @patch.object(GraffitiLookup, "_request", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_get_status_by_id_success(self, mock_request):
        html_response = b"""
        <div class="txtBox">
          <table class="withBorder">
            <tr><td>Service Request</td><td>12345</td></tr>
            <tr><td>Address</td><td>456 OAK AVE, BROOKLYN</td></tr>
            <tr><td>Created</td><td>06/15/2023</td></tr>
            <tr><td>Last Updated</td><td>07/20/2023</td></tr>
            <tr><td>Status</td><td>Completed</td></tr>
          </table>
        </div>
        """

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_response

        mock_request.return_value = mock_response
        result = await self.graffiti_lookup.get_status_by_id("G12345")

        expected_result = {
            "service_request": "12345",
            "address": "456 OAK AVE, BROOKLYN",
            "created": "2023-06-15",
            "last_updated": "2023-07-20",
            "status": "Completed",
        }

        assert result == expected_result
        mock_request.assert_called_once()

    @patch.object(GraffitiLookup, "_request", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_get_status_by_id_not_found(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.content = None

        mock_request.return_value = mock_response
        result = await self.graffiti_lookup.get_status_by_id("G99999")

        assert result == {}

    @patch.object(GraffitiLookup, "_request", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_get_status_by_id_empty_content(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = None

        mock_request.return_value = mock_response
        result = await self.graffiti_lookup.get_status_by_id("G12345")

        assert result == {}

    @patch.object(GraffitiLookup, "_request", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_get_statuses_by_id_multiple(self, mock_request):
        html_response_1 = b"""
        <div class="txtBox">
          <table class="withBorder">
            <tr><td>Service Request</td><td>11111</td></tr>
            <tr><td>Address</td><td>111 FIRST ST, MANHATTAN</td></tr>
            <tr><td>Created</td><td>01/01/2023</td></tr>
            <tr><td>Last Updated</td><td>02/01/2023</td></tr>
            <tr><td>Status</td><td>Completed</td></tr>
          </table>
        </div>
        """

        html_response_2 = b"""
        <div class="txtBox">
          <table class="withBorder">
            <tr><td>Service Request</td><td>22222</td></tr>
            <tr><td>Address</td><td>222 SECOND ST, BROOKLYN</td></tr>
            <tr><td>Created</td><td>03/15/2023</td></tr>
            <tr><td>Last Updated</td><td>04/20/2023</td></tr>
            <tr><td>Status</td><td>Open</td></tr>
          </table>
        </div>
        """

        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.content = html_response_1

        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.content = html_response_2

        mock_request.side_effect = [mock_response_1, mock_response_2]
        result = await self.graffiti_lookup.get_statuses_by_id(["G11111", "G22222"])

        assert len(result) == 2
        assert result[0]["service_request"] == "11111"
        assert result[0]["address"] == "111 FIRST ST, MANHATTAN"
        assert result[1]["service_request"] == "22222"
        assert result[1]["address"] == "222 SECOND ST, BROOKLYN"

    @pytest.mark.asyncio
    async def test_get_statuses_by_id_empty_list(self):
        result = await self.graffiti_lookup.get_statuses_by_id([])

        assert result == []

    @patch.object(GraffitiLookup, "_request", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_get_status_by_id_no_close_connection(self, mock_request):
        html_response = b"""
        <div class="txtBox">
          <table class="withBorder">
            <tr><td>Service Request</td><td>12345</td></tr>
            <tr><td>Address</td><td>789 PINE AVE, BRONX</td></tr>
            <tr><td>Created</td><td>05/10/2023</td></tr>
            <tr><td>Last Updated</td><td>06/15/2023</td></tr>
            <tr><td>Status</td><td>Closed</td></tr>
          </table>
        </div>
        """

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_response

        mock_request.return_value = mock_response
        result = await self.graffiti_lookup.get_status_by_id(
            "G12345", close_connection=False
        )

        expected_result = {
            "service_request": "12345",
            "address": "789 PINE AVE, BRONX",
            "created": "2023-05-10",
            "last_updated": "2023-06-15",
            "status": "Closed",
        }

        assert result == expected_result
