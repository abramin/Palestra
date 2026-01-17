"""
Unit tests for Email value object.

Justification: Email validation is a pure domain invariant with many edge cases
(format validation, normalization) that benefit from exhaustive unit testing.
Integration tests would add noise without value for these pure validations.
"""
import pytest

from src.domain.membership.email import Email, InvalidEmailError


class TestEmailValidation_RejectsInvalidFormats:
    """Tests that Email rejects various invalid formats."""

    def test_rejects_empty_string(self):
        with pytest.raises(InvalidEmailError):
            Email("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(InvalidEmailError):
            Email("   ")

    def test_rejects_missing_at_symbol(self):
        with pytest.raises(InvalidEmailError):
            Email("userexample.com")

    def test_rejects_missing_domain(self):
        with pytest.raises(InvalidEmailError):
            Email("user@")

    def test_rejects_missing_local_part(self):
        with pytest.raises(InvalidEmailError):
            Email("@example.com")

    def test_rejects_multiple_at_symbols(self):
        with pytest.raises(InvalidEmailError):
            Email("user@@example.com")

    def test_rejects_spaces_in_email(self):
        with pytest.raises(InvalidEmailError):
            Email("user @example.com")

    def test_rejects_missing_tld(self):
        with pytest.raises(InvalidEmailError):
            Email("user@example")


class TestEmailValidation_AcceptsValidFormats:
    """Tests that Email accepts various valid formats."""

    def test_accepts_standard_email(self):
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_accepts_email_with_subdomain(self):
        email = Email("user@mail.example.com")
        assert email.value == "user@mail.example.com"

    def test_accepts_email_with_plus_addressing(self):
        email = Email("user+tag@example.com")
        assert email.value == "user+tag@example.com"

    def test_accepts_email_with_dots_in_local(self):
        email = Email("first.last@example.com")
        assert email.value == "first.last@example.com"


class TestEmailNormalization:
    """Tests that Email normalizes input consistently."""

    def test_lowercases_email(self):
        email = Email("User@EXAMPLE.COM")
        assert email.value == "user@example.com"

    def test_strips_leading_whitespace(self):
        email = Email("  user@example.com")
        assert email.value == "user@example.com"

    def test_strips_trailing_whitespace(self):
        email = Email("user@example.com  ")
        assert email.value == "user@example.com"


class TestEmailEquality:
    """Tests Email value object equality semantics."""

    def test_emails_with_same_value_are_equal(self):
        email1 = Email("user@example.com")
        email2 = Email("user@example.com")
        assert email1 == email2

    def test_emails_with_different_values_are_not_equal(self):
        email1 = Email("user1@example.com")
        email2 = Email("user2@example.com")
        assert email1 != email2

    def test_normalized_emails_are_equal(self):
        email1 = Email("User@Example.com")
        email2 = Email("user@example.com")
        assert email1 == email2
