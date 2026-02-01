import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

import pytest

from graffiti_lookup.__main__ import read_file, write_file


class TestFileOperations:
    def setup_method(self):
        self.temp_dir = TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_data = [
            {
                "service_request": "G12345",
                "address": "123 Main St",
                "created": "2020-01-01",
                "last_updated": "2020-01-02",
                "status": "Done",
            }
        ]
        self.fieldnames = self.test_data[0].keys()

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_write_json_file(self):
        file_path = self.temp_path / "test.json"

        write_file(str(file_path), "json", self.test_data, self.fieldnames)

        assert file_path.exists()
        with open(file_path) as f:
            result = json.load(f)
        assert result == self.test_data

    def test_read_json_file(self):
        file_path = self.temp_path / "test.json"
        with open(file_path, "w") as f:
            json.dump(self.test_data, f)

        result = read_file(str(file_path), "json", self.fieldnames)

        assert result == self.test_data

    def test_read_json_file_not_found_returns_an_empty_list(self):
        file_path = self.temp_path / "nonexistent.json"

        result = read_file(str(file_path), "json", self.fieldnames)

        assert result == []

    def test_write_csv_file(self):
        file_path = self.temp_path / "test.csv"

        write_file(str(file_path), "csv", self.test_data, self.fieldnames)

        assert file_path.exists()
        with open(file_path) as f:
            content = f.read()
        assert "service_request" in content
        assert "G12345" in content

    def test_read_csv_file(self):
        file_path = self.temp_path / "test.csv"
        write_file(str(file_path), "csv", self.test_data, self.fieldnames)

        result = read_file(str(file_path), "csv", self.fieldnames)

        assert len(result) == 1
        assert result[0]["service_request"] == "G12345"
        assert result[0]["address"] == "123 Main St"
        assert result[0]["status"] == "Done"

    def test_read_csv_file_not_found(self):
        file_path = self.temp_path / "nonexistent.csv"

        result = read_file(str(file_path), "csv", self.fieldnames)

        assert result == []

    def test_writing_and_reading_json_file_preserves_data(self):
        file_path = self.temp_path / "roundtrip.json"

        write_file(str(file_path), "json", self.test_data, self.fieldnames)
        result = read_file(str(file_path), "json", self.fieldnames)

        assert result == self.test_data

    def test_writing_and_reading_csv_file_preserves_data(self):
        file_path = self.temp_path / "roundtrip.csv"

        write_file(str(file_path), "csv", self.test_data, self.fieldnames)
        result = read_file(str(file_path), "csv", self.fieldnames)

        assert result == self.test_data

    def test_write_multiple_records_json(self):
        file_path = self.temp_path / "multiple.json"
        multiple_data = [
            {
                "service_request": "G11111",
                "address": "111 First St",
                "created": "2020-01-01",
                "last_updated": "2020-01-02",
                "status": "Done",
            },
            {
                "service_request": "G22222",
                "address": "222 Second St",
                "created": "2020-02-01",
                "last_updated": "2020-02-02",
                "status": "Open",
            },
        ]

        write_file(str(file_path), "json", multiple_data, self.fieldnames)
        result = read_file(str(file_path), "json", self.fieldnames)

        assert len(result) == 2
        assert result[0]["service_request"] == "G11111"
        assert result[1]["service_request"] == "G22222"

    def test_write_multiple_records_csv(self):
        file_path = self.temp_path / "multiple.csv"
        multiple_data = [
            {
                "service_request": "G11111",
                "address": "111 First St",
                "created": "2020-01-01",
                "last_updated": "2020-01-02",
                "status": "Done",
            },
            {
                "service_request": "G22222",
                "address": "222 Second St",
                "created": "2020-02-01",
                "last_updated": "2020-02-02",
                "status": "Open",
            },
        ]

        write_file(str(file_path), "csv", multiple_data, self.fieldnames)
        result = read_file(str(file_path), "csv", self.fieldnames)

        assert len(result) == 2
        assert result[0]["service_request"] == "G11111"
        assert result[1]["service_request"] == "G22222"

    def test_write_single_record_csv(self):
        """Test writing a single dict (not list) to CSV"""
        file_path = self.temp_path / "single.csv"
        single_record = {
            "service_request": "G55555",
            "address": "555 Single St",
            "created": "2021-01-01",
            "last_updated": "2021-01-02",
            "status": "Pending",
        }

        write_file(str(file_path), "csv", single_record, single_record.keys())

        assert file_path.exists()
        with open(file_path) as f:
            content = f.read()
        assert "service_request" in content
        assert "G55555" in content


class TestMainFunction:
    def setup_method(self):
        self.temp_dir = TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.single_result = {
            "service_request": "G12345",
            "address": "123 Main St",
            "created": "2020-01-01",
            "last_updated": "2020-01-02",
            "status": "Done",
        }
        self.multiple_results = [
            {
                "service_request": "G11111",
                "address": "111 First St",
                "created": "2020-01-01",
                "last_updated": "2020-01-02",
                "status": "Done",
            },
            {
                "service_request": "G22222",
                "address": "222 Second St",
                "created": "2020-02-01",
                "last_updated": "2020-02-02",
                "status": "Open",
            },
        ]

    def teardown_method(self):
        self.temp_dir.cleanup()

    @patch("graffiti_lookup.__main__.sys.stdout")
    @patch(
        "graffiti_lookup.__main__.GraffitiLookup.get_status_by_id",
        new_callable=AsyncMock,
    )
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_single_id_stdout(self, mock_args, mock_get_status, mock_stdout):
        """Test main function outputs single result to stdout"""
        from graffiti_lookup.__main__ import main

        mock_args.id = "G12345"
        mock_args.ids = None
        mock_args.file_path = None
        mock_args.merge_file = False
        mock_args.file_type = None

        mock_get_status.return_value = self.single_result

        await main()

        mock_stdout.write.assert_called_once()
        call_args = mock_stdout.write.call_args[0][0]
        assert json.loads(call_args) == self.single_result

    @patch(
        "graffiti_lookup.__main__.GraffitiLookup.get_statuses_by_id",
        new_callable=AsyncMock,
    )
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_multiple_ids_to_file(self, mock_args, mock_get_statuses):
        from graffiti_lookup.__main__ import main

        file_path = self.temp_path / "results.json"

        mock_args.id = None
        mock_args.ids = "G11111,G22222"
        mock_args.file_path = str(file_path)
        mock_args.file_type = "json"
        mock_args.merge_file = False

        mock_get_statuses.return_value = self.multiple_results

        await main()

        assert file_path.exists()
        with open(file_path) as f:
            result = json.load(f)
        assert len(result) == 2
        assert result[0]["service_request"] == "G11111"
        assert result[1]["service_request"] == "G22222"

    @patch(
        "graffiti_lookup.__main__.GraffitiLookup.get_status_by_id",
        new_callable=AsyncMock,
    )
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_single_id_to_json_file(self, mock_args, mock_get_status):
        from graffiti_lookup.__main__ import main

        file_path = self.temp_path / "result.json"

        mock_args.id = "G12345"
        mock_args.ids = None
        mock_args.file_path = str(file_path)
        mock_args.file_type = "json"
        mock_args.merge_file = False

        mock_get_status.return_value = self.single_result

        await main()

        assert file_path.exists()
        with open(file_path) as f:
            result = json.load(f)
        assert result == self.single_result

    @patch(
        "graffiti_lookup.__main__.GraffitiLookup.get_status_by_id",
        new_callable=AsyncMock,
    )
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_single_id_to_csv_file(self, mock_args, mock_get_status):
        from graffiti_lookup.__main__ import main

        file_path = self.temp_path / "result.csv"

        mock_args.id = "G12345"
        mock_args.ids = None
        mock_args.file_path = str(file_path)
        mock_args.file_type = "csv"
        mock_args.merge_file = False

        mock_get_status.return_value = self.single_result

        await main()

        assert file_path.exists()
        with open(file_path) as f:
            content = f.read()
        assert "service_request" in content
        assert "G12345" in content

    @patch(
        "graffiti_lookup.__main__.GraffitiLookup.get_statuses_by_id",
        new_callable=AsyncMock,
    )
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_merge_file(self, mock_args, mock_get_statuses):
        from graffiti_lookup.__main__ import main

        file_path = self.temp_path / "merged.json"

        # Create existing file with one record
        existing_data = [
            {
                "service_request": "G99999",
                "address": "999 Existing St",
                "created": "2019-01-01",
                "last_updated": "2019-01-02",
                "status": "Completed",
            }
        ]
        with open(file_path, "w") as f:
            json.dump(existing_data, f)

        mock_args.id = None
        mock_args.ids = "G11111,G22222"
        mock_args.file_path = str(file_path)
        mock_args.file_type = "json"
        mock_args.merge_file = True

        mock_get_statuses.return_value = self.multiple_results

        await main()

        with open(file_path) as f:
            result = json.load(f)

        # Should have all 3 records
        assert len(result) == 3
        service_ids = {r["service_request"] for r in result}
        assert service_ids == {"G11111", "G22222", "G99999"}

    @patch(
        "graffiti_lookup.__main__.GraffitiLookup.get_statuses_by_id",
        new_callable=AsyncMock,
    )
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_merge_file_with_duplicate(self, mock_args, mock_get_statuses):
        from graffiti_lookup.__main__ import main

        file_path = self.temp_path / "merged_dup.json"

        # Create existing file with overlapping record
        existing_data = [
            {
                "service_request": "G11111",
                "address": "111 OLD ADDRESS",
                "created": "2020-01-01",
                "last_updated": "2020-01-02",
                "status": "Old Status",
            }
        ]
        with open(file_path, "w") as f:
            json.dump(existing_data, f)

        mock_args.id = None
        mock_args.ids = "G11111,G22222"
        mock_args.file_path = str(file_path)
        mock_args.file_type = "json"
        mock_args.merge_file = True

        mock_get_statuses.return_value = self.multiple_results

        await main()

        with open(file_path) as f:
            result = json.load(f)

        # Should have 2 records with updated G11111
        assert len(result) == 2
        g11111_record = next(r for r in result if r["service_request"] == "G11111")
        assert g11111_record["address"] == "111 First St"

    @patch("graffiti_lookup.__main__.sys.stdout")
    @patch(
        "graffiti_lookup.__main__.GraffitiLookup.get_status_by_id",
        new_callable=AsyncMock,
    )
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_no_result(self, mock_args, mock_get_status, mock_stdout):
        from graffiti_lookup.__main__ import main

        mock_args.id = "G99999"
        mock_args.ids = None
        mock_args.file_path = None
        mock_args.merge_file = False
        mock_args.file_type = None

        mock_get_status.return_value = {}

        await main()

        mock_stdout.write.assert_called_once()
        call_args = mock_stdout.write.call_args[0][0]
        assert json.loads(call_args) == {}

    @patch("graffiti_lookup.__main__.sys.stdout")
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_no_id_or_ids(self, mock_args, mock_stdout):
        """Test main when neither id nor ids provided"""
        from graffiti_lookup.__main__ import main

        mock_args.id = None
        mock_args.ids = None
        mock_args.file_path = None
        mock_args.merge_file = False
        mock_args.file_type = None

        await main()

        # Should output None as JSON
        mock_stdout.write.assert_called_once()
        call_args = mock_stdout.write.call_args[0][0]
        assert json.loads(call_args) is None

    @patch(
        "graffiti_lookup.__main__.GraffitiLookup.get_status_by_id",
        new_callable=AsyncMock,
    )
    @patch("graffiti_lookup.__main__.args")
    @pytest.mark.asyncio
    async def test_main_single_id_file_type_inferred(self, mock_args, mock_get_status):
        """Test main infers file type from file path extension"""
        from graffiti_lookup.__main__ import main

        file_path = self.temp_path / "inferred.csv"

        mock_args.id = "G12345"
        mock_args.ids = None
        mock_args.file_path = str(file_path)
        mock_args.file_type = None  # Should infer from .csv
        mock_args.merge_file = False

        mock_get_status.return_value = self.single_result

        await main()

        assert file_path.exists()
        with open(file_path) as f:
            content = f.read()
        assert "service_request" in content
        assert "G12345" in content
