"""
Custom Objects resource for managing custom object definitions and records.
"""

from typing import Dict, List, Optional, Any
from .base import BaseResource


class CustomObjectsResource(BaseResource):
    """
    Resource for managing custom object definitions, records, and fields.

    Supports:
    - Custom object definitions (CRUD)
    - Custom object records (CRUD)
    - Custom field definitions (CRUD)
    - Headless CMS (public content API)
    """

    # ===========================================================================
    # Custom Object Definitions
    # ===========================================================================

    def list_definitions(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_content_model: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List all custom object definitions.

        Args:
            search: Search by name or object_key
            is_active: Filter by active status
            is_content_model: Filter by content model status
            limit: Number of results to return
            offset: Number of results to skip

        Returns:
            Paginated list of custom object definitions

        Example:
            objects = client.custom_objects.list_definitions(
                is_content_model=True
            )
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        if search:
            params["search"] = search
        if is_active is not None:
            params["is_active"] = is_active
        if is_content_model is not None:
            params["is_content_model"] = is_content_model

        return self._request("GET", "/custom-objects", params=params)

    def get_definition(self, object_id: str) -> Dict[str, Any]:
        """
        Get a custom object definition by ID.

        Args:
            object_id: The custom object ID

        Returns:
            Custom object definition

        Example:
            obj = client.custom_objects.get_definition("obj_123")
        """
        return self._request("GET", f"/custom-objects/{object_id}")

    def get_schema(self, object_id: str) -> Dict[str, Any]:
        """
        Get a custom object definition with full schema (includes custom fields).

        Args:
            object_id: The custom object ID

        Returns:
            Custom object definition with custom_fields array

        Example:
            schema = client.custom_objects.get_schema("obj_123")
            for field in schema["custom_fields"]:
                print(f"{field['name']}: {field['field_type']}")
        """
        return self._request("GET", f"/custom-objects/{object_id}/schema")

    def create_definition(
        self,
        name: str,
        plural_name: str,
        object_key: str,
        description: Optional[str] = None,
        icon: str = "Package",
        color: str = "#3B82F6",
        primary_field: str = "name",
        enable_activities: bool = True,
        enable_tags: bool = True,
        enable_attachments: bool = True,
        is_content_model: bool = False,
        allow_public_access: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new custom object definition.

        Args:
            name: Singular name (e.g., "Project")
            plural_name: Plural name (e.g., "Projects")
            object_key: Unique key (lowercase, underscores only, e.g., "project")
            description: Optional description
            icon: Phosphor icon name
            color: Hex color code
            primary_field: Field key to use as primary display field
            enable_activities: Enable activity tracking
            enable_tags: Enable tags
            enable_attachments: Enable file attachments
            is_content_model: Enable CMS features (publishing, SEO)
            allow_public_access: Allow public API access (requires is_content_model=True)

        Returns:
            Created custom object definition

        Example:
            # Create a regular CRM object
            project = client.custom_objects.create_definition(
                name="Project",
                plural_name="Projects",
                object_key="project",
                description="Customer projects",
                icon="briefcase",
                color="#10B981"
            )

            # Create a headless CMS content model
            blog = client.custom_objects.create_definition(
                name="Blog Post",
                plural_name="Blog Posts",
                object_key="blog_post",
                is_content_model=True,
                allow_public_access=True
            )
        """
        data = {
            "name": name,
            "plural_name": plural_name,
            "object_key": object_key,
            "icon": icon,
            "color": color,
            "primary_field": primary_field,
            "enable_activities": enable_activities,
            "enable_tags": enable_tags,
            "enable_attachments": enable_attachments,
            "is_content_model": is_content_model,
            "allow_public_access": allow_public_access,
        }
        if description:
            data["description"] = description

        return self._request("POST", "/custom-objects", data=data)

    def update_definition(
        self,
        object_id: str,
        name: Optional[str] = None,
        plural_name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        primary_field: Optional[str] = None,
        enable_activities: Optional[bool] = None,
        enable_tags: Optional[bool] = None,
        enable_attachments: Optional[bool] = None,
        is_content_model: Optional[bool] = None,
        allow_public_access: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update a custom object definition.

        Args:
            object_id: The custom object ID
            **kwargs: Fields to update

        Returns:
            Updated custom object definition

        Example:
            updated = client.custom_objects.update_definition(
                "obj_123",
                color="#3B82F6",
                is_content_model=True
            )
        """
        data = {}
        if name is not None:
            data["name"] = name
        if plural_name is not None:
            data["plural_name"] = plural_name
        if description is not None:
            data["description"] = description
        if icon is not None:
            data["icon"] = icon
        if color is not None:
            data["color"] = color
        if primary_field is not None:
            data["primary_field"] = primary_field
        if enable_activities is not None:
            data["enable_activities"] = enable_activities
        if enable_tags is not None:
            data["enable_tags"] = enable_tags
        if enable_attachments is not None:
            data["enable_attachments"] = enable_attachments
        if is_content_model is not None:
            data["is_content_model"] = is_content_model
        if allow_public_access is not None:
            data["allow_public_access"] = allow_public_access
        if is_active is not None:
            data["is_active"] = is_active

        return self._request("PATCH", f"/custom-objects/{object_id}", data=data)

    def delete_definition(self, object_id: str) -> None:
        """
        Delete a custom object definition.

        Args:
            object_id: The custom object ID

        Example:
            client.custom_objects.delete_definition("obj_123")
        """
        self._request("DELETE", f"/custom-objects/{object_id}")

    # ===========================================================================
    # Custom Object Records
    # ===========================================================================

    def list_records(
        self,
        object_key: str,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        owner: Optional[str] = None,
        status: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
        ordering: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List all records for a specific custom object.

        Args:
            object_key: The custom object key (e.g., "project")
            search: Search by name
            tags: Filter by tags
            owner: Filter by owner ID
            status: Filter by status (DRAFT, PUBLISHED, ARCHIVED)
            is_public: Filter by public status
            limit: Number of results to return
            offset: Number of results to skip
            ordering: Field to order by (e.g., "-created_at")

        Returns:
            Paginated list of custom object records

        Example:
            records = client.custom_objects.list_records(
                "project",
                search="website",
                tags=["priority"],
                limit=10
            )
        """
        params = {
            "object_key": object_key,
            "limit": limit,
            "offset": offset,
        }
        if search:
            params["search"] = search
        if tags:
            params["tags"] = tags
        if owner:
            params["owner"] = owner
        if status:
            params["status"] = status
        if is_public is not None:
            params["is_public"] = is_public
        if ordering:
            params["ordering"] = ordering

        return self._request("GET", "/custom-object-records/by_object_type", params=params)

    def get_record(self, record_id: str) -> Dict[str, Any]:
        """
        Get a single custom object record by ID.

        Args:
            record_id: The record ID

        Returns:
            Custom object record

        Example:
            record = client.custom_objects.get_record("rec_123")
            print(record["field_values"]["name"])
        """
        return self._request("GET", f"/custom-object-records/{record_id}")

    def create_record(
        self,
        object_definition: str,
        field_values: Dict[str, Any],
        tags: Optional[List[str]] = None,
        owner: Optional[str] = None,
        # CMS fields
        is_public: bool = False,
        status: str = "DRAFT",
        publish_at: Optional[str] = None,
        unpublish_at: Optional[str] = None,
        meta_title: Optional[str] = None,
        meta_description: Optional[str] = None,
        meta_keywords: Optional[List[str]] = None,
        og_image: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new custom object record.

        Args:
            object_definition: The custom object ID
            field_values: Dict of field values (field_key: value)
            tags: Optional tags
            owner: Optional owner ID
            is_public: Make public (for content models)
            status: Status (DRAFT, PUBLISHED, ARCHIVED)
            publish_at: Schedule publish date (ISO format)
            unpublish_at: Schedule unpublish date (ISO format)
            meta_title: SEO meta title
            meta_description: SEO meta description
            meta_keywords: SEO keywords list
            og_image: Open Graph image URL
            slug: URL slug

        Returns:
            Created custom object record

        Example:
            # Create a regular CRM record
            project = client.custom_objects.create_record(
                object_definition="obj_123",
                field_values={
                    "name": "Website Redesign",
                    "budget": 50000,
                    "deadline": "2024-12-31",
                    "status": "In Progress"
                },
                tags=["web", "design", "priority"]
            )

            # Create a CMS content record
            blog_post = client.custom_objects.create_record(
                object_definition="obj_456",
                field_values={
                    "title": "Getting Started",
                    "content": "<h1>Welcome</h1><p>...</p>"
                },
                is_public=True,
                status="PUBLISHED",
                meta_title="Getting Started - Blog",
                meta_description="Learn how to get started",
                slug="getting-started"
            )
        """
        data = {
            "object_definition": object_definition,
            "field_values": field_values,
        }
        if tags:
            data["tags"] = tags
        if owner:
            data["owner"] = owner
        if is_public:
            data["is_public"] = is_public
        if status:
            data["status"] = status
        if publish_at:
            data["publish_at"] = publish_at
        if unpublish_at:
            data["unpublish_at"] = unpublish_at
        if meta_title:
            data["meta_title"] = meta_title
        if meta_description:
            data["meta_description"] = meta_description
        if meta_keywords:
            data["meta_keywords"] = meta_keywords
        if og_image:
            data["og_image"] = og_image
        if slug:
            data["slug"] = slug

        return self._request("POST", "/custom-object-records", data=data)

    def update_record(
        self,
        record_id: str,
        field_values: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        owner: Optional[str] = None,
        is_public: Optional[bool] = None,
        status: Optional[str] = None,
        publish_at: Optional[str] = None,
        unpublish_at: Optional[str] = None,
        meta_title: Optional[str] = None,
        meta_description: Optional[str] = None,
        meta_keywords: Optional[List[str]] = None,
        og_image: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a custom object record.

        Args:
            record_id: The record ID
            **kwargs: Fields to update

        Returns:
            Updated custom object record

        Example:
            updated = client.custom_objects.update_record(
                "rec_123",
                field_values={"status": "Completed"},
                tags=["completed", "web"]
            )
        """
        data = {}
        if field_values is not None:
            data["field_values"] = field_values
        if tags is not None:
            data["tags"] = tags
        if owner is not None:
            data["owner"] = owner
        if is_public is not None:
            data["is_public"] = is_public
        if status is not None:
            data["status"] = status
        if publish_at is not None:
            data["publish_at"] = publish_at
        if unpublish_at is not None:
            data["unpublish_at"] = unpublish_at
        if meta_title is not None:
            data["meta_title"] = meta_title
        if meta_description is not None:
            data["meta_description"] = meta_description
        if meta_keywords is not None:
            data["meta_keywords"] = meta_keywords
        if og_image is not None:
            data["og_image"] = og_image
        if slug is not None:
            data["slug"] = slug

        return self._request("PATCH", f"/custom-object-records/{record_id}", data=data)

    def delete_record(self, record_id: str) -> None:
        """
        Delete a custom object record.

        Args:
            record_id: The record ID

        Example:
            client.custom_objects.delete_record("rec_123")
        """
        self._request("DELETE", f"/custom-object-records/{record_id}")

    def move_stage(self, record_id: str, field_id: str, stage: str) -> Dict[str, Any]:
        """
        Move a record to a different pipeline stage.

        Args:
            record_id: The record ID
            field_id: The pipeline field ID
            stage: The stage name

        Returns:
            Updated custom object record

        Example:
            client.custom_objects.move_stage(
                "rec_123",
                field_id="field_456",
                stage="In Progress"
            )
        """
        data = {"field_id": field_id, "stage": stage}
        return self._request("PATCH", f"/custom-object-records/{record_id}/move-stage", data=data)

    # ===========================================================================
    # Custom Field Definitions
    # ===========================================================================

    def list_fields(self, custom_object_id: str) -> List[Dict[str, Any]]:
        """
        List all custom field definitions for a custom object.

        Args:
            custom_object_id: The custom object ID

        Returns:
            List of custom field definitions

        Example:
            fields = client.custom_objects.list_fields("obj_123")
            for field in fields:
                print(f"{field['name']}: {field['field_type']}")
        """
        response = self._request(
            "GET",
            "/custom-fields",
            params={
                "entity_type": "CUSTOM_OBJECT",
                "related_custom_object": custom_object_id,
            },
        )
        return response.get("results", [])

    def create_field(
        self,
        name: str,
        field_key: str,
        field_type: str,
        custom_object_id: str,
        is_required: bool = False,
        is_indexed: bool = False,
        default_value: Optional[Any] = None,
        options: Optional[List[str]] = None,
        pipeline_stages: Optional[List[Dict[str, Any]]] = None,
        placeholder: Optional[str] = None,
        help_text: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new custom field definition.

        Args:
            name: Field display name
            field_key: Unique field key (lowercase, underscores)
            field_type: Field type (TEXT, NUMBER, DATE, DROPDOWN, PIPELINE, etc.)
            custom_object_id: The custom object ID
            is_required: Is field required
            is_indexed: Index field for faster queries
            default_value: Default value
            options: Options for DROPDOWN/MULTI_SELECT
            pipeline_stages: Stages for PIPELINE type
            placeholder: Placeholder text
            help_text: Help text
            **kwargs: Additional field properties

        Returns:
            Created custom field definition

        Example:
            # Text field
            field = client.custom_objects.create_field(
                name="Project Name",
                field_key="name",
                field_type="TEXT",
                custom_object_id="obj_123",
                is_required=True
            )

            # Pipeline field
            pipeline = client.custom_objects.create_field(
                name="Project Stage",
                field_key="stage",
                field_type="PIPELINE",
                custom_object_id="obj_123",
                pipeline_stages=[
                    {"name": "Discovery", "color": "#3B82F6", "position": 0, "is_default": True},
                    {"name": "In Progress", "color": "#F59E0B", "position": 1},
                    {"name": "Done", "color": "#10B981", "position": 2}
                ]
            )
        """
        data = {
            "name": name,
            "field_key": field_key,
            "field_type": field_type,
            "entity_type": "CUSTOM_OBJECT",
            "related_custom_object": custom_object_id,
            "is_required": is_required,
            "is_indexed": is_indexed,
            **kwargs,
        }
        if default_value is not None:
            data["default_value"] = default_value
        if options:
            data["options"] = options
        if pipeline_stages:
            data["pipeline_stages"] = pipeline_stages
        if placeholder:
            data["placeholder"] = placeholder
        if help_text:
            data["help_text"] = help_text

        return self._request("POST", "/custom-fields", data=data)

    def update_field(self, field_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update a custom field definition.

        Args:
            field_id: The field ID
            **kwargs: Fields to update

        Returns:
            Updated custom field definition

        Example:
            updated = client.custom_objects.update_field(
                "field_123",
                name="Updated Name",
                is_required=True
            )
        """
        return self._request("PATCH", f"/custom-fields/{field_id}", data=kwargs)

    def delete_field(self, field_id: str) -> None:
        """
        Delete a custom field definition.

        Args:
            field_id: The field ID

        Example:
            client.custom_objects.delete_field("field_123")
        """
        self._request("DELETE", f"/custom-fields/{field_id}")

    # ===========================================================================
    # Headless CMS (Public Content API)
    # ===========================================================================

    def get_public_content(
        self,
        object_key: str,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        ordering: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get published public content (unauthenticated).

        Note: This endpoint does not require authentication.

        Args:
            object_key: The custom object key
            search: Search by name, slug, meta_title, meta_description
            limit: Number of results to return
            offset: Number of results to skip
            ordering: Field to order by

        Returns:
            Paginated list of published records

        Example:
            posts = client.custom_objects.get_public_content(
                "blog_post",
                search="api",
                limit=10
            )
        """
        params = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        if ordering:
            params["ordering"] = ordering

        return self._request("GET", f"/public/custom-objects/{object_key}", params=params)

    def get_public_content_by_slug(self, object_key: str, slug: str) -> Dict[str, Any]:
        """
        Get a single published record by slug (unauthenticated).

        Note: This endpoint does not require authentication.

        Args:
            object_key: The custom object key
            slug: The record slug

        Returns:
            Published record

        Example:
            post = client.custom_objects.get_public_content_by_slug(
                "blog_post",
                "getting-started-with-api"
            )
        """
        return self._request("GET", f"/public/custom-objects/{object_key}/slug/{slug}")

    def get_public_schema(self, object_key: str) -> Dict[str, Any]:
        """
        Get the schema for a public content model (unauthenticated).

        Note: This endpoint does not require authentication.

        Args:
            object_key: The custom object key

        Returns:
            Custom object definition with field schema

        Example:
            schema = client.custom_objects.get_public_schema("blog_post")
            for field in schema.get("custom_fields", []):
                print(f"{field['name']}: {field['field_type']}")
        """
        return self._request("GET", f"/public/custom-objects/{object_key}/schema")

    # ==================== Media Files ====================

    def upload_media(
        self,
        file,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a media file (image or document).

        Args:
            file: File object or path to file
            alt_text: Alternative text for accessibility (optional)

        Returns:
            Media file object with ID, URL, and metadata

        Example:
            # Upload from file path
            with open("product.jpg", "rb") as f:
                media = client.custom_objects.upload_media(f, alt_text="Product image")
            print(f"File ID: {media['id']}, URL: {media['url']}")

            # Use in custom object record
            record = client.custom_objects.create_record(
                object_definition="product",
                field_values={
                    "name": "Premium Widget",
                    "image": media["id"]  # Reference the uploaded file
                }
            )
        """
        files = {"file": file}
        data = {}
        if alt_text:
            data["alt_text"] = alt_text

        return self._request("POST", "/media/upload", data=data, files=files)

    def list_media(
        self,
        file_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        ordering: str = "-created_at",
    ) -> Dict[str, Any]:
        """
        List media files with optional filtering.

        Args:
            file_type: Filter by file type ('IMAGE' or 'FILE')
            search: Search in file names and alt text
            limit: Maximum number of results (default: 100)
            offset: Number of results to skip (default: 0)
            ordering: Sort order (default: "-created_at")

        Returns:
            Paginated list of media files

        Example:
            # List all images
            images = client.custom_objects.list_media(file_type="IMAGE", limit=20)
            for img in images["results"]:
                print(f"{img['file_name']}: {img['url']}")

            # Search for specific files
            results = client.custom_objects.list_media(search="logo")
        """
        params = {
            "limit": limit,
            "offset": offset,
            "ordering": ordering,
        }
        if file_type:
            params["file_type"] = file_type
        if search:
            params["search"] = search

        return self._request("GET", "/media", params=params)

    def get_media(self, media_id: str) -> Dict[str, Any]:
        """
        Get a specific media file by ID.

        Args:
            media_id: The media file ID (UUID)

        Returns:
            Media file object with metadata

        Example:
            media = client.custom_objects.get_media("media-uuid")
            print(f"File: {media['file_name']}, Size: {media['size_display']}")
        """
        return self._request("GET", f"/media/{media_id}")

    def update_media_metadata(
        self,
        media_id: str,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update media file metadata (e.g., alt text) without re-uploading.

        Args:
            media_id: The media file ID
            alt_text: Updated alternative text

        Returns:
            Updated media file object

        Example:
            updated = client.custom_objects.update_media_metadata(
                media_id="media-uuid",
                alt_text="Updated product image description"
            )
        """
        data = {}
        if alt_text is not None:
            data["alt_text"] = alt_text

        return self._request("PATCH", f"/media/{media_id}/update-metadata", data=data)

    def delete_media(self, media_id: str) -> None:
        """
        Delete a media file.

        Warning: This permanently deletes the file from storage.

        Args:
            media_id: The media file ID

        Example:
            client.custom_objects.delete_media("media-uuid")
        """
        self._request("DELETE", f"/media/{media_id}")
        return None
