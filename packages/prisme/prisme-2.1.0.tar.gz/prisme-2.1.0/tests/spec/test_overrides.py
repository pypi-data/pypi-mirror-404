"""Tests for override models."""

from prisme.spec.overrides import DeliveryOverrides, FrontendOverrides, MCPOverrides


class TestDeliveryOverrides:
    def test_defaults(self):
        overrides = DeliveryOverrides()
        assert overrides.page_size is None
        assert overrides.max_page_size is None
        assert overrides.rest_tags is None
        assert overrides.subscriptions is None

    def test_with_values(self):
        overrides = DeliveryOverrides(page_size=50, rest_tags=["custom"])
        assert overrides.page_size == 50
        assert overrides.rest_tags == ["custom"]

    def test_forbids_extra(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DeliveryOverrides(unknown_field="bad")


class TestFrontendOverrides:
    def test_defaults(self):
        overrides = FrontendOverrides()
        assert overrides.nav_icon is None
        assert overrides.generate_form is None

    def test_with_values(self):
        overrides = FrontendOverrides(
            nav_icon="users",
            nav_label="Customers",
            table_columns=["name", "email"],
            generate_form=True,
        )
        assert overrides.nav_icon == "users"
        assert overrides.table_columns == ["name", "email"]


class TestMCPOverrides:
    def test_defaults(self):
        overrides = MCPOverrides()
        assert overrides.tool_prefix is None
        assert overrides.tool_descriptions == {}

    def test_with_values(self):
        overrides = MCPOverrides(
            tool_prefix="customer",
            tool_descriptions={"list": "Search customers"},
        )
        assert overrides.tool_prefix == "customer"
