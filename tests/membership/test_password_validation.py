"""
Unit tests for Password value object.

Justification: Password validation has multiple strength requirements (length,
complexity rules) and hashing behavior with many edge cases that are easier to
test exhaustively in isolation.
"""

import pytest

from src.domain.membership.password import Password, WeakPasswordError


class TestPasswordValidation_RejectsWeakPasswords:
    """Tests that Password rejects passwords that don't meet strength requirements."""

    def test_rejects_empty_password(self):
        with pytest.raises(WeakPasswordError):
            Password.create("")

    def test_rejects_password_shorter_than_8_characters(self):
        with pytest.raises(WeakPasswordError):
            Password.create("Short1!")

    def test_rejects_password_without_uppercase(self):
        with pytest.raises(WeakPasswordError):
            Password.create("lowercase1!")

    def test_rejects_password_without_lowercase(self):
        with pytest.raises(WeakPasswordError):
            Password.create("UPPERCASE1!")

    def test_rejects_password_without_digit(self):
        with pytest.raises(WeakPasswordError):
            Password.create("NoDigitsHere!")

    def test_rejects_password_without_special_character(self):
        with pytest.raises(WeakPasswordError):
            Password.create("NoSpecial123")


class TestPasswordValidation_AcceptsStrongPasswords:
    """Tests that Password accepts passwords meeting all requirements."""

    def test_accepts_password_meeting_all_requirements(self):
        password = Password.create("StrongPass1!")
        assert password is not None

    def test_accepts_password_with_minimum_length(self):
        password = Password.create("Abcdef1!Ghij")  # Exactly 12 chars
        assert password is not None

    def test_accepts_password_with_various_special_characters(self):
        for special in ["!", "@", "#", "$", "%", "^", "&", "*"]:
            password = Password.create(f"Password1234{special}")
            assert password is not None


class TestPasswordHashing:
    """Tests that Password hashes values securely."""

    def test_does_not_store_plaintext(self):
        plaintext = "StrongPass1!"
        password = Password.create(plaintext)
        assert password.hashed_value != plaintext

    def test_same_plaintext_produces_different_hashes(self):
        """Salt should make each hash unique."""
        password1 = Password.create("StrongPass1!")
        password2 = Password.create("StrongPass1!")
        assert password1.hashed_value != password2.hashed_value

    def test_verify_returns_true_for_correct_password(self):
        password = Password.create("StrongPass1!")
        assert password.verify("StrongPass1!") is True

    def test_verify_returns_false_for_incorrect_password(self):
        password = Password.create("StrongPass1!")
        assert password.verify("WrongPassword1!") is False


class TestPasswordFromHash:
    """Tests reconstituting Password from stored hash."""

    def test_can_create_from_existing_hash(self):
        original = Password.create("StrongPass1!")
        reconstituted = Password.from_hash(original.hashed_value)
        assert reconstituted.verify("StrongPass1!") is True

    def test_from_hash_does_not_validate_strength(self):
        """When loading from DB, we don't re-validate - the hash is trusted."""
        original = Password.create("StrongPass1!")
        reconstituted = Password.from_hash(original.hashed_value)
        # Should not raise, even though we can't check original strength
        assert reconstituted is not None
