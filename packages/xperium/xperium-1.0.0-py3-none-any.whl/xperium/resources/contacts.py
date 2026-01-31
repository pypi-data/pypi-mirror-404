"""Contacts resource."""
from typing import Any, Dict, List, Optional

from .base import BaseResource
from ..models import Contact


class ContactsResource(BaseResource):
    """
    Resource for managing contacts.
    """

    def identify(
        self,
        external_id: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        first_name: str = "",
        last_name: str = "",
        email_addresses: Optional[List[str]] = None,
        phone_numbers: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> tuple[Contact, bool]:
        """
        Identify or create a contact by external_id, email, or phone.

        This is the primary method for SDK user identification. It tries to find
        a contact by external_id first, falls back to email/phone, and creates a new
        contact if not found.

        Note: When creating a new contact, at least one of email/email_addresses or
        phone/phone_numbers is required. All name fields are optional.

        Args:
            external_id: External identifier from your system
            email: Primary email address (will be added to email_addresses)
            phone: Primary phone number (will be added to phone_numbers)
            first_name: First name (optional, used when creating new contact)
            last_name: Last name (optional, used when creating new contact)
            email_addresses: List of email addresses (optional)
            phone_numbers: List of phone numbers (optional)
            tags: List of tags to associate with contact (optional, merges with existing)
            **kwargs: Additional contact fields (title, department, etc.)

        Returns:
            Tuple of (Contact, created) where created is True if contact was created

        Raises:
            ValidationError: If creating a new contact without email or phone

        Examples:
            # Identify by email
            >>> contact, created = client.contacts.identify(
            ...     email="user@example.com",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )

            # Identify by external_id with phone
            >>> contact, created = client.contacts.identify(
            ...     external_id="user_123",
            ...     phone="+1234567890",
            ...     first_name="Jane"
            ... )

            # Identify with tags
            >>> contact, created = client.contacts.identify(
            ...     email="user@example.com",
            ...     tags=["premium", "vip", "early-adopter"]
            ... )

            # Identify with multiple contact methods
            >>> contact, created = client.contacts.identify(
            ...     external_id="user_123",
            ...     email_addresses=["user@example.com", "alt@example.com"],
            ...     phone_numbers=["+1234567890"],
            ...     tags=["customer"]
            ... )
        """
        # Build email_addresses list
        emails = email_addresses or []
        if email and email not in emails:
            emails.insert(0, email)

        # Build phone_numbers list
        phones = phone_numbers or []
        if phone and phone not in phones:
            phones.insert(0, phone)

        data = {
            "external_id": external_id,
            "first_name": first_name,
            "last_name": last_name,
            **kwargs,
        }

        # Add email/phone arrays if provided
        if emails:
            data["email_addresses"] = emails
        if phones:
            data["phone_numbers"] = phones

        # Add tags if provided
        if tags is not None:
            data["tags"] = tags

        # Remove None values and empty strings (but keep empty lists/dicts)
        data = {k: v for k, v in data.items() if not (v is None or v == "")}

        response = self.http.post("/api/v1/contacts/identify/", data=data)

        contact = Contact.from_dict(response["contact"])
        created = response.get("created", False)

        return contact, created

    def lookup(
        self, external_id: Optional[str] = None, email: Optional[str] = None
    ) -> Optional[Contact]:
        """
        Lookup a contact by external_id or email without creating.

        Args:
            external_id: External identifier
            email: Email address

        Returns:
            Contact if found, None otherwise

        Example:
            >>> contact = client.contacts.lookup(external_id="user_123")
        """
        params = {}
        if external_id:
            params["external_id"] = external_id
        if email:
            params["email"] = email

        try:
            response = self.http.get("/api/v1/contacts/lookup/", params=params)
            return Contact.from_dict(response)
        except Exception:
            # ResourceNotFoundError or other errors
            return None

    def create(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        first_name: str = "",
        last_name: str = "",
        email_addresses: Optional[List[str]] = None,
        phone_numbers: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> Contact:
        """
        Create a new contact.

        Note: At least one of email, phone, email_addresses, or phone_numbers is required.
        All name fields (first_name, last_name) are now optional.

        Args:
            email: Primary email address (optional, will be added to email_addresses)
            phone: Primary phone number (optional, will be added to phone_numbers)
            first_name: First name (optional)
            last_name: Last name (optional)
            email_addresses: List of email addresses (optional)
            phone_numbers: List of phone numbers (optional)
            tags: List of tags to associate with contact (optional)
            **kwargs: Additional contact fields

        Returns:
            Created contact

        Raises:
            ValidationError: If neither email/email_addresses nor phone/phone_numbers is provided

        Examples:
            # Create with email only
            >>> contact = client.contacts.create(
            ...     email="user@example.com"
            ... )

            # Create with phone only
            >>> contact = client.contacts.create(
            ...     phone="+1234567890",
            ...     first_name="John"
            ... )

            # Create with tags
            >>> contact = client.contacts.create(
            ...     email="user@example.com",
            ...     tags=["vip", "premium"]
            ... )

            # Create with both email and phone
            >>> contact = client.contacts.create(
            ...     email="user@example.com",
            ...     phone="+1234567890",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )

            # Create with multiple emails/phones
            >>> contact = client.contacts.create(
            ...     email_addresses=["user@example.com", "user2@example.com"],
            ...     phone_numbers=["+1234567890"],
            ...     first_name="John",
            ...     tags=["early-adopter"]
            ... )
        """
        # Build email_addresses list
        emails = email_addresses or []
        if email and email not in emails:
            emails.insert(0, email)  # Primary email goes first

        # Build phone_numbers list
        phones = phone_numbers or []
        if phone and phone not in phones:
            phones.insert(0, phone)  # Primary phone goes first

        # Validate at least one contact method
        if not emails and not phones:
            from ..exceptions import ValidationError
            raise ValidationError(
                "At least one contact method is required: provide either email/email_addresses or phone/phone_numbers"
            )

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email_addresses": emails,
            "phone_numbers": phones,
            **kwargs,
        }

        # Add tags if provided
        if tags is not None:
            data["tags"] = tags

        # Remove empty strings (but keep empty lists/dicts)
        data = {k: v for k, v in data.items() if v != ""}

        response = self.http.post("/api/v1/contacts/", data=data)
        return Contact.from_dict(response)

    def get(self, contact_id: str) -> Contact:
        """
        Get a contact by ID.

        Args:
            contact_id: Contact UUID

        Returns:
            Contact

        Example:
            >>> contact = client.contacts.get("contact-uuid")
        """
        response = self.http.get(f"/api/v1/contacts/{contact_id}/")
        return Contact.from_dict(response)

    def update(
        self,
        contact_id: Optional[str] = None,
        external_id: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Contact:
        """
        Update a contact by ID or identifier.

        You can update a contact using either:
        1. contact_id (internal UUID)
        2. external_id, email, or phone (any identifier)

        Args:
            contact_id: Contact UUID (optional if using identifiers)
            external_id: External identifier (optional if using contact_id)
            email: Email address (optional if using contact_id)
            phone: Phone number (optional if using contact_id)
            tags: List of tags to add to contact (optional, merges with existing)
            **kwargs: Fields to update (first_name, last_name, title, etc.)

        Returns:
            Updated contact

        Raises:
            ValueError: If neither contact_id nor any identifier is provided

        Examples:
            # Update by contact_id (legacy method)
            >>> contact = client.contacts.update(
            ...     contact_id="contact-uuid",
            ...     first_name="Jane",
            ...     title="Senior Engineer"
            ... )

            # Update by external_id
            >>> contact = client.contacts.update(
            ...     external_id="user_123",
            ...     first_name="Jane",
            ...     last_name="Doe"
            ... )

            # Update by email
            >>> contact = client.contacts.update(
            ...     email="user@example.com",
            ...     first_name="Jane",
            ...     title="Senior Engineer"
            ... )

            # Update with tags
            >>> contact = client.contacts.update(
            ...     email="user@example.com",
            ...     tags=["premium", "active"]
            ... )

            # Update by phone
            >>> contact = client.contacts.update(
            ...     phone="+1234567890",
            ...     first_name="Jane",
            ...     tags=["mobile-user"]
            ... )
        """
        # Check if using contact_id (legacy method)
        if contact_id:
            update_data = {**kwargs}
            if tags:
                update_data["tags"] = tags
            response = self.http.patch(f"/api/v1/contacts/{contact_id}/", data=update_data)
            return Contact.from_dict(response)

        # Using identifier method
        if not any([external_id, email, phone]):
            raise ValueError(
                "Must provide either contact_id or at least one identifier "
                "(external_id, email, or phone)"
            )

        # Build data with identifiers and update fields
        data = {**kwargs}
        if external_id:
            data["external_id"] = external_id
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if tags:
            data["tags"] = tags

        response = self.http.patch("/api/v1/contacts/update-by-identifier/", data=data)
        return Contact.from_dict(response)

    def delete(self, contact_id: str) -> None:
        """
        Delete a contact.

        Args:
            contact_id: Contact UUID

        Example:
            >>> client.contacts.delete("contact-uuid")
        """
        self.http.delete(f"/api/v1/contacts/{contact_id}/")

    def list(self, **filters) -> List[Contact]:
        """
        List contacts with optional filters.

        Args:
            **filters: Filter parameters (status, company, etc.)

        Returns:
            List of contacts

        Example:
            >>> contacts = client.contacts.list(status="CUSTOMER")
        """
        response = self.http.get("/api/v1/contacts/", params=filters)
        results = response.get("results", [])
        return [Contact.from_dict(item) for item in results]

    def mark_contacted(self, contact_id: str) -> Contact:
        """
        Mark contact as contacted (updates last_contacted timestamp).

        Args:
            contact_id: Contact UUID

        Returns:
            Updated contact

        Example:
            >>> contact = client.contacts.mark_contacted("contact-uuid")
        """
        response = self.http.patch(f"/api/v1/contacts/{contact_id}/mark_contacted/")
        return Contact.from_dict(response)

    def update_status(self, contact_id: str, status: str) -> Contact:
        """
        Update contact status.

        Args:
            contact_id: Contact UUID
            status: New status (LEAD, PROSPECT, CUSTOMER, etc.)

        Returns:
            Updated contact

        Example:
            >>> contact = client.contacts.update_status("contact-uuid", "CUSTOMER")
        """
        response = self.http.patch(
            f"/api/v1/contacts/{contact_id}/update_status/", data={"status": status}
        )
        return Contact.from_dict(response)
