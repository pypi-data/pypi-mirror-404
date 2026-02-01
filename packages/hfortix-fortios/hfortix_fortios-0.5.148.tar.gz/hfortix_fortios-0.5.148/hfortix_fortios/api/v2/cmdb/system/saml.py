"""
FortiOS CMDB - System saml

Configuration endpoint for managing cmdb system/saml objects.

API Endpoints:
    GET    /cmdb/system/saml
    POST   /cmdb/system/saml
    PUT    /cmdb/system/saml/{identifier}
    DELETE /cmdb/system/saml/{identifier}

Example Usage:
    >>> from hfortix_fortios import FortiOS
    >>> fgt = FortiOS(host="192.168.1.99", token="your-api-token")
    >>>
    >>> # List all items
    >>> items = fgt.api.cmdb.system_saml.get()
    >>>
    >>> # Create with auto-normalization (strings/lists converted automatically)
    >>> result = fgt.api.cmdb.system_saml.post(
    ...     name="example",
    ...     srcintf="port1",  # Auto-converted to [{'name': 'port1'}]
    ...     dstintf=["port2", "port3"],  # Auto-converted to list of dicts
    ... )

Important:
    - Use **POST** to create new objects
    - Use **PUT** to update existing objects
    - Use **GET** to retrieve configuration
    - Use **DELETE** to remove objects
    - **Auto-normalization**: List fields accept strings or lists, automatically
      converted to FortiOS format [{'name': '...'}]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Union

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from hfortix_core.http.interface import IHTTPClient
    from hfortix_fortios.models import FortiObject

# Import helper functions from central _helpers module
from hfortix_fortios._helpers import (
    build_api_payload,
    build_cmdb_payload,  # Keep for backward compatibility / manual usage
    is_success,
    quote_path_param,  # URL encoding for path parameters
    normalize_table_field,  # For table field normalization
)
# Import metadata mixin for schema introspection
from hfortix_fortios._helpers.metadata_mixin import MetadataMixin

# Import Protocol-based type hints (eliminates need for local @overload decorators)
from hfortix_fortios._protocols import CRUDEndpoint

class Saml(CRUDEndpoint, MetadataMixin):
    """Saml Operations."""
    
    # Configure metadata mixin to use this endpoint's helper module
    _helper_module_name = "saml"
    
    # ========================================================================
    # Table Fields Metadata (for normalization)
    # Auto-generated from schema - supports flexible input formats
    # ========================================================================
    _TABLE_FIELDS = {
        "service_providers": {
            "mkey": "name",
            "required_fields": ['name', 'prefix', 'sp-entity-id', 'sp-single-sign-on-url'],
            "example": "[{'name': 'value', 'prefix': 'value', 'sp-entity-id': 'value', 'sp-single-sign-on-url': 'value'}]",
        },
    }
    
    # ========================================================================
    # Capabilities (from schema metadata)
    # ========================================================================
    SUPPORTS_CREATE = False
    SUPPORTS_READ = True
    SUPPORTS_UPDATE = True
    SUPPORTS_DELETE = False
    SUPPORTS_MOVE = True
    SUPPORTS_CLONE = True
    SUPPORTS_FILTERING = True
    SUPPORTS_PAGINATION = True
    SUPPORTS_SEARCH = False
    SUPPORTS_SORTING = False

    def __init__(self, client: "IHTTPClient"):
        """Initialize Saml endpoint."""
        self._client = client

    # ========================================================================
    # GET Method
    # Type hints provided by CRUDEndpoint protocol (no local @overload needed)
    # ========================================================================
    
    def get(
        self,
        name: str | None = None,
        filter: list[str] | None = None,
        count: int | None = None,
        start: int | None = None,
        payload_dict: dict[str, Any] | None = None,
        error_mode: Literal["raise", "return", "print"] | None = None,
        error_format: Literal["detailed", "simple", "code_only"] | None = None,
    ):  # type: ignore[no-untyped-def]
        """
        Retrieve system/saml configuration.

        Global settings for SAML authentication.

        Args:
            name: Name identifier to retrieve specific object. If None, returns all objects.
            filter: List of filter expressions to limit results.
                Each filter uses format: "field==value" or "field!=value"
                Operators: ==, !=, =@ (contains), !@ (not contains), <=, <, >=, >
                Multiple filters use AND logic. For OR, use comma in single string.
                Example: ["name==test", "status==enable"] or ["name==test,name==prod"]
            count: Maximum number of entries to return (pagination).
            start: Starting entry index for pagination (0-based).
            payload_dict: Additional query parameters for advanced options:
                - datasource (bool): Include datasource information
                - with_meta (bool): Include metadata about each object
                - with_contents_hash (bool): Include checksum of object contents
                - format (list[str]): Property names to include (e.g., ["policyid", "srcintf"])
                - scope (str): Query scope - "global", "vdom", or "both"
                - action (str): Special actions - "schema", "default"
                See FortiOS REST API documentation for complete list.
            error_mode: Override client-level error_mode. "raise" raises exceptions, "return" returns error dict, "print" prints errors.
            error_format: Override client-level error_format. "detailed" provides full context, "simple" is concise, "code_only" returns just status code.

        Returns:
            FortiObject instance or list of FortiObject instances. Returns Coroutine if using async client.
            Use .dict, .json, or .raw properties to access as dictionary.
            
            Response structure:
                - http_method: GET
                - results: Configuration object(s)
                - vdom: Virtual domain
                - path: API path
                - name: Object name (single object queries)
                - status: success/error
                - http_status: HTTP status code
                - build: FortiOS build number

        Examples:
            >>> # Get all system/saml objects
            >>> result = fgt.api.cmdb.system_saml.get()
            >>> print(f"Found {len(result['results'])} objects")
            
            >>> # Get with filter
            >>> result = fgt.api.cmdb.system_saml.get(
            ...     filter=["name==test", "status==enable"]
            ... )
            
            >>> # Get with pagination
            >>> result = fgt.api.cmdb.system_saml.get(
            ...     start=0, count=100
            ... )
            
            >>> # Get schema information  
            >>> schema = fgt.api.cmdb.system_saml.get_schema()

        See Also:
            - post(): Create new system/saml object
            - put(): Update existing system/saml object
            - delete(): Remove system/saml object
            - exists(): Check if object exists
            - get_schema(): Get endpoint schema/metadata
        """
        params = payload_dict.copy() if payload_dict else {}
        
        # Add explicit query parameters
        if filter is not None:
            params["filter"] = filter
        if count is not None:
            params["count"] = count
        if start is not None:
            params["start"] = start
        
        if name:
            endpoint = f"/system/saml/{quote_path_param(name)}"
            unwrap_single = True
        else:
            endpoint = "/system/saml"
            unwrap_single = False
        
        return self._client.get(
            "cmdb", endpoint, params=params, vdom=False, unwrap_single=unwrap_single
        )

    def get_schema(
        self,
        format: str = "schema",
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Get schema/metadata for this endpoint.
        
        Returns the FortiOS schema definition including available fields,
        their types, required vs optional properties, enum values, nested
        structures, and default values.
        
        This queries the live firewall for its current schema, which may
        vary between FortiOS versions.
        
        Args:
            format: Schema format - "schema" (FortiOS native) or "json-schema" (JSON Schema standard).
                Defaults to "schema".
                
        Returns:
            Schema definition as dict. Returns Coroutine if using async client.
            
        Example:
            >>> # Get FortiOS native schema
            >>> schema = fgt.api.cmdb.system_saml.get_schema()
            >>> print(schema['results'])
            
            >>> # Get JSON Schema format (if supported)
            >>> json_schema = fgt.api.cmdb.system_saml.get_schema(format="json-schema")
        
        Note:
            Not all endpoints support all schema formats. The "schema" format
            is most widely supported.
        """
        return self.get(action=format)


    # ========================================================================
    # PUT Method
    # Type hints provided by CRUDEndpoint protocol (no local @overload needed)
    # ========================================================================
    
    def put(
        self,
        payload_dict: dict[str, Any] | None = None,
        status: Literal["enable", "disable"] | None = None,
        role: Literal["identity-provider", "service-provider"] | None = None,
        default_login_page: Literal["normal", "sso"] | None = None,
        default_profile: str | None = None,
        cert: str | None = None,
        binding_protocol: Literal["post", "redirect"] | None = None,
        portal_url: str | None = None,
        entity_id: str | None = None,
        single_sign_on_url: str | None = None,
        single_logout_url: str | None = None,
        idp_entity_id: str | None = None,
        idp_single_sign_on_url: str | None = None,
        idp_single_logout_url: str | None = None,
        idp_cert: str | None = None,
        server_address: str | None = None,
        require_signed_resp_and_asrt: Literal["enable", "disable"] | None = None,
        tolerance: int | None = None,
        life: int | None = None,
        service_providers: str | list[str] | list[dict[str, Any]] | None = None,
        q_action: Literal["move"] | None = None,
        q_before: str | None = None,
        q_after: str | None = None,
        q_scope: str | None = None,
        error_mode: Literal["raise", "return", "print"] | None = None,
        error_format: Literal["detailed", "simple", "code_only"] | None = None,
    ):  # type: ignore[no-untyped-def]
        """
        Update existing system/saml object.

        Global settings for SAML authentication.

        Args:
            payload_dict: Object data as dict. Must include name (primary key).
            status: Enable/disable SAML authentication (default = disable).
            role: SAML role.
            default_login_page: Choose default login page.
            default_profile: Default profile for new SSO admin.
            cert: Certificate to sign SAML messages.
            binding_protocol: IdP Binding protocol.
            portal_url: SP portal URL.
            entity_id: SP entity ID.
            single_sign_on_url: SP single sign-on URL.
            single_logout_url: SP single logout URL.
            idp_entity_id: IDP entity ID.
            idp_single_sign_on_url: IDP single sign-on URL.
            idp_single_logout_url: IDP single logout URL.
            idp_cert: IDP certificate name.
            server_address: Server address.
            require_signed_resp_and_asrt: Require both response and assertion from IDP to be signed when FGT acts as SP (default = disable).
            tolerance: Tolerance to the range of time when the assertion is valid (in minutes).
            life: Length of the range of time when the assertion is valid (in minutes).
            service_providers: Authorized service providers.
                Default format: [{'name': 'value', 'prefix': 'value', 'sp-entity-id': 'value', 'sp-single-sign-on-url': 'value'}]
                Required format: List of dicts with keys: name, prefix, sp-entity-id, sp-single-sign-on-url
                  (String format not allowed due to multiple required fields)
            error_mode: Override client-level error_mode. "raise" raises exceptions, "return" returns error dict, "print" prints errors.
            error_format: Override client-level error_format. "detailed" provides full context, "simple" is concise, "code_only" returns just status code.

        Returns:
            FortiObject instance. Use .dict, .json, or .raw to access as dictionary.

        Raises:
            ValueError: If name is missing from payload

        Examples:
            >>> # Update specific fields
            >>> result = fgt.api.cmdb.system_saml.put(
            ...     name="existing-object",
            ...     # ... fields to update
            ... )
            
            >>> # Update using payload dict
            >>> payload = {
            ...     "name": "existing-object",
            ...     "field1": "new-value",
            ... }
            >>> result = fgt.api.cmdb.system_saml.put(payload_dict=payload)

        See Also:
            - post(): Create new object
            - set(): Intelligent create or update
        """
        # Apply normalization for table fields (supports flexible input formats)
        if service_providers is not None:
            service_providers = normalize_table_field(
                service_providers,
                mkey="name",
                required_fields=['name', 'prefix', 'sp-entity-id', 'sp-single-sign-on-url'],
                field_name="service_providers",
                example="[{'name': 'value', 'prefix': 'value', 'sp-entity-id': 'value', 'sp-single-sign-on-url': 'value'}]",
            )
        
        # Build payload using helper function
        payload_data = build_api_payload(
            api_type="cmdb",
            status=status,
            role=role,
            default_login_page=default_login_page,
            default_profile=default_profile,
            cert=cert,
            binding_protocol=binding_protocol,
            portal_url=portal_url,
            entity_id=entity_id,
            single_sign_on_url=single_sign_on_url,
            single_logout_url=single_logout_url,
            idp_entity_id=idp_entity_id,
            idp_single_sign_on_url=idp_single_sign_on_url,
            idp_single_logout_url=idp_single_logout_url,
            idp_cert=idp_cert,
            server_address=server_address,
            require_signed_resp_and_asrt=require_signed_resp_and_asrt,
            tolerance=tolerance,
            life=life,
            service_providers=service_providers,
            data=payload_dict,
        )
        
        # Check for deprecated fields and warn users
        from ._helpers.saml import DEPRECATED_FIELDS
        if DEPRECATED_FIELDS:
            from hfortix_core import check_deprecated_fields
            check_deprecated_fields(
                payload=payload_data,
                deprecated_fields=DEPRECATED_FIELDS,
                endpoint="cmdb/system/saml",
            )
        
        # Singleton endpoint - no identifier needed
        endpoint = "/system/saml"

        # Add explicit query parameters for PUT
        params: dict[str, Any] = {}
        if q_action is not None:
            params["action"] = q_action
        if q_before is not None:
            params["before"] = q_before
        if q_after is not None:
            params["after"] = q_after
        if q_scope is not None:
            params["scope"] = q_scope
        
        return self._client.put(
            "cmdb", endpoint, data=payload_data, params=params, vdom=False        )





    # ========================================================================
    # Action: Move
    # ========================================================================
    
    def move(
        self,
        name: str,
        action: Literal["before", "after"],
        reference_name: str,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Move system/saml object to a new position.
        
        Reorders objects by moving one before or after another.
        
        Args:
            name: Name of object to move
            action: Move "before" or "after" reference object
            reference_name: Name of reference object
            **kwargs: Additional parameters
            
        Returns:
            API response dictionary
            
        Example:
            >>> # Move policy 100 before policy 50
            >>> fgt.api.cmdb.system_saml.move(
            ...     name="object1",
            ...     action="before",
            ...     reference_name="object2"
            ... )
        """
        return self._client.request(
            method="PUT",
            path=f"/api/v2/cmdb/system/saml",
            params={
                "name": name,
                "action": "move",
                action: reference_name,
                **kwargs,
            },
        )

    # ========================================================================
    # Action: Clone
    # ========================================================================
    
    def clone(
        self,
        name: str,
        new_name: str,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Clone system/saml object.
        
        Creates a copy of an existing object with a new identifier.
        
        Args:
            name: Name of object to clone
            new_name: Name for the cloned object
            **kwargs: Additional parameters
            
        Returns:
            API response dictionary
            
        Example:
            >>> # Clone an existing object
            >>> fgt.api.cmdb.system_saml.clone(
            ...     name="template",
            ...     new_name="new-from-template"
            ... )
        """
        return self._client.request(
            method="POST",
            path=f"/api/v2/cmdb/system/saml",
            params={
                "name": name,
                "new_name": new_name,
                "action": "clone",
                **kwargs,
            },
        )

    # ========================================================================
    # Helper: Check Existence
    # ========================================================================
    
    def exists(
        self,
        name: str,
    ) -> bool:
        """
        Check if system/saml object exists.
        
        Args:
            name: Name to check
            
        Returns:
            True if object exists, False otherwise
            
        Example:
            >>> # Check before creating
            >>> if not fgt.api.cmdb.system_saml.exists(name="myobj"):
            ...     fgt.api.cmdb.system_saml.post(payload_dict=data)
        """
        # Use direct request with silent error handling to avoid logging 404s
        # This is expected behavior for exists() - 404 just means "doesn't exist"
        endpoint = "/system/saml"
        endpoint = f"{endpoint}/{quote_path_param(name)}"
        
        # Make request with silent=True to suppress 404 error logging
        # (404 is expected when checking existence - it just means "doesn't exist")
        # Use _wrapped_client to access the underlying HTTPClient directly
        # (self._client is ResponseProcessingClient, _wrapped_client is HTTPClient)
        try:
            result = self._client._wrapped_client.get(
                "cmdb",
                endpoint,
                params=None,
                vdom=False,
                raw_json=True,
                silent=True,
            )
            
            if isinstance(result, dict):
                # Synchronous response - check status
                return result.get("status") == "success"
            else:
                # Asynchronous response
                async def _check() -> bool:
                    r = await result
                    return r.get("status") == "success"
                return _check()
        except Exception:
            # Any error (404, network, etc.) means we can't confirm existence
            return False

