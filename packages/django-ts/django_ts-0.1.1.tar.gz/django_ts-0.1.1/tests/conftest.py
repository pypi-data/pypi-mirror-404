import pytest


@pytest.fixture
def mock_model():
    class MockModel:
        STATUS_ACTIVE = "active"
        STATUS_INACTIVE = "inactive"
        STATUS_PENDING = "pending"
        PRIORITY_HIGH = 1
        PRIORITY_LOW = 2

        STATUS_CHOICES = (
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("pending", "Pending"),
        )

        PRIORITY_CHOICES = (
            (1, "High Priority"),
            (2, "Low Priority"),
        )

        class _meta:
            object_name = "MockModel"

    return MockModel


@pytest.fixture
def mock_model_no_constants():
    class EmptyModel:
        regular_attribute = "not a constant"

        class _meta:
            object_name = "EmptyModel"

    return EmptyModel
