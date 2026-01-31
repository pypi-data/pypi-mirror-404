from datetime import datetime

import pytest

from graffiti_lookup.models import ServiceRequest


class TestServiceRequest:

    def test_service_request_creation(self):
        service_request = ServiceRequest(
            service_request="G2589",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )

        assert service_request.service_request == "G2589"
        assert service_request.address == "123 Main St"
        assert service_request.status == "Closed"

    def test_service_request_date_parsing_returns_correct_datetime_format(self):
        service_request = ServiceRequest(
            service_request="G2589",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )

        assert service_request.created == datetime(2024, 1, 15)
        assert service_request.last_updated == datetime(2024, 1, 20)

    def test_service_request_id_field_constant(self):
        assert ServiceRequest.ID_FIELD == "service_request"

    def test_serialize_field_datetime_returns_expected_datetime_string_format(self):
        service_request = ServiceRequest(
            service_request="G2589",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )

        assert service_request.serialize_field("created") == "2024-01-15"
        assert service_request.serialize_field("last_updated") == "2024-01-20"

    def test_serialize_field_string(self):
        service_request = ServiceRequest(
            service_request="G2589",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )

        assert service_request.serialize_field("service_request") == "G2589"
        assert service_request.serialize_field("address") == "123 Main St"
        assert service_request.serialize_field("status") == "Closed"

    def test_to_dict_returns_proper_dictionary_representation_of_the_service_request(
        self,
    ):
        service_request = ServiceRequest(
            service_request="G2589",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )

        result = service_request.to_dict()

        expected_result = {
            "service_request": "G2589",
            "address": "123 Main St",
            "created": "2024-01-15",
            "last_updated": "2024-01-20",
            "status": "Closed",
        }

        assert result == expected_result

    def test_to_dict_contains_all_fields(self):
        service_request = ServiceRequest(
            service_request="G999",
            address="999 Test Lane",
            created="06/15/2023",
            last_updated="07/10/2023",
            status="In Progress",
        )

        result = service_request.to_dict()

        expected_fields = [
            "service_request",
            "address",
            "created",
            "last_updated",
            "status",
        ]

        assert list(result.keys()) == expected_fields

    def test_invalid_date_format_raises_error(self):
        with pytest.raises(ValueError):
            ServiceRequest(
                service_request="G2589",
                address="123 Main St",
                created="2024-01-15",  # Invalid format (should be MM/DD/YYYY)
                last_updated="01/20/2024",
                status="Closed",
            )

    def test_invalid_date_values_raises_error(self):
        with pytest.raises(ValueError):
            ServiceRequest(
                service_request="G2589",
                address="123 Main St",
                created="13/45/2024",  # Invalid month and day
                last_updated="01/20/2024",
                status="Closed",
            )

    def test_service_request_equality(self):
        service_request1 = ServiceRequest(
            service_request="G2589",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )
        service_request2 = ServiceRequest(
            service_request="G2589",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )

        assert service_request1 == service_request2

    def test_service_request_inequality(self):
        service_request1 = ServiceRequest(
            service_request="G2589",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )
        service_request2 = ServiceRequest(
            service_request="G2590",
            address="123 Main St",
            created="01/15/2024",
            last_updated="01/20/2024",
            status="Closed",
        )

        assert service_request1 != service_request2
