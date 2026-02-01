"""
FortiOS CMDB - System ptp

Configuration endpoint for managing cmdb system/ptp objects.

API Endpoints:
    GET    /cmdb/system/ptp
    POST   /cmdb/system/ptp
    PUT    /cmdb/system/ptp/{identifier}
    DELETE /cmdb/system/ptp/{identifier}

Example Usage:
    >>> from hfortix_fortios import FortiOS
    >>> fgt = FortiOS(host="192.168.1.99", token="your-api-token")
    >>>
    >>> # List all items
    >>> items = fgt.api.cmdb.system_ptp.get()
    >>>
    >>> # Create with auto-normalization (strings/lists converted automatically)
    >>> result = fgt.api.cmdb.system_ptp.post(
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

class Ptp(CRUDEndpoint, MetadataMixin):
    """Ptp Operations."""
    
    # Configure metadata mixin to use this endpoint's helper module
    _helper_module_name = "ptp"
    
    # ========================================================================
    # Table Fields Metadata (for normalization)
    # Auto-generated from schema - supports flexible input formats
    # ========================================================================
    _TABLE_FIELDS = {
        "server_interface": {
            "mkey": "id",
            "required_fields": ['id', 'server-interface-name'],
            "example": "[{'id': 1, 'server-interface-name': 'value'}]",
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
        """Initialize Ptp endpoint."""
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
        Retrieve system/ptp configuration.

        Configure system PTP information.

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
            >>> # Get all system/ptp objects
            >>> result = fgt.api.cmdb.system_ptp.get()
            >>> print(f"Found {len(result['results'])} objects")
            
            >>> # Get with filter
            >>> result = fgt.api.cmdb.system_ptp.get(
            ...     filter=["name==test", "status==enable"]
            ... )
            
            >>> # Get with pagination
            >>> result = fgt.api.cmdb.system_ptp.get(
            ...     start=0, count=100
            ... )
            
            >>> # Get schema information  
            >>> schema = fgt.api.cmdb.system_ptp.get_schema()

        See Also:
            - post(): Create new system/ptp object
            - put(): Update existing system/ptp object
            - delete(): Remove system/ptp object
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
            endpoint = f"/system/ptp/{quote_path_param(name)}"
            unwrap_single = True
        else:
            endpoint = "/system/ptp"
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
            >>> schema = fgt.api.cmdb.system_ptp.get_schema()
            >>> print(schema['results'])
            
            >>> # Get JSON Schema format (if supported)
            >>> json_schema = fgt.api.cmdb.system_ptp.get_schema(format="json-schema")
        
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
        mode: Literal["multicast", "hybrid"] | None = None,
        delay_mechanism: Literal["E2E", "P2P"] | None = None,
        request_interval: int | None = None,
        interface: str | None = None,
        server_mode: Literal["enable", "disable"] | None = None,
        server_interface: str | list[str] | list[dict[str, Any]] | None = None,
        q_action: Literal["move"] | None = None,
        q_before: str | None = None,
        q_after: str | None = None,
        q_scope: str | None = None,
        error_mode: Literal["raise", "return", "print"] | None = None,
        error_format: Literal["detailed", "simple", "code_only"] | None = None,
    ):  # type: ignore[no-untyped-def]
        """
        Update existing system/ptp object.

        Configure system PTP information.

        Args:
            payload_dict: Object data as dict. Must include name (primary key).
            status: Enable/disable setting the FortiGate system time by synchronizing with an PTP Server.
            mode: Multicast transmission or hybrid transmission.
            delay_mechanism: End to end delay detection or peer to peer delay detection.
            request_interval: The delay request value is the logarithmic mean interval in seconds between the delay request messages sent by the slave to the master.
            interface: PTP client will reply through this interface.
            server_mode: Enable/disable FortiGate PTP server mode. Your FortiGate becomes an PTP server for other devices on your network.
            server_interface: FortiGate interface(s) with PTP server mode enabled. Devices on your network can contact these interfaces for PTP services.
                Default format: [{'id': 1, 'server-interface-name': 'value'}]
                Required format: List of dicts with keys: id, server-interface-name
                  (String format not allowed due to multiple required fields)
            error_mode: Override client-level error_mode. "raise" raises exceptions, "return" returns error dict, "print" prints errors.
            error_format: Override client-level error_format. "detailed" provides full context, "simple" is concise, "code_only" returns just status code.

        Returns:
            FortiObject instance. Use .dict, .json, or .raw to access as dictionary.

        Raises:
            ValueError: If name is missing from payload

        Examples:
            >>> # Update specific fields
            >>> result = fgt.api.cmdb.system_ptp.put(
            ...     name="existing-object",
            ...     # ... fields to update
            ... )
            
            >>> # Update using payload dict
            >>> payload = {
            ...     "name": "existing-object",
            ...     "field1": "new-value",
            ... }
            >>> result = fgt.api.cmdb.system_ptp.put(payload_dict=payload)

        See Also:
            - post(): Create new object
            - set(): Intelligent create or update
        """
        # Apply normalization for table fields (supports flexible input formats)
        if server_interface is not None:
            server_interface = normalize_table_field(
                server_interface,
                mkey="id",
                required_fields=['id', 'server-interface-name'],
                field_name="server_interface",
                example="[{'id': 1, 'server-interface-name': 'value'}]",
            )
        
        # Build payload using helper function
        # Note: auto_normalize=False because this endpoint has unitary fields
        # (like 'interface') that would be incorrectly converted to list format
        payload_data = build_api_payload(
            api_type="cmdb",
            auto_normalize=False,
            status=status,
            mode=mode,
            delay_mechanism=delay_mechanism,
            request_interval=request_interval,
            interface=interface,
            server_mode=server_mode,
            server_interface=server_interface,
            data=payload_dict,
        )
        
        # Check for deprecated fields and warn users
        from ._helpers.ptp import DEPRECATED_FIELDS
        if DEPRECATED_FIELDS:
            from hfortix_core import check_deprecated_fields
            check_deprecated_fields(
                payload=payload_data,
                deprecated_fields=DEPRECATED_FIELDS,
                endpoint="cmdb/system/ptp",
            )
        
        # Singleton endpoint - no identifier needed
        endpoint = "/system/ptp"

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
        Move system/ptp object to a new position.
        
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
            >>> fgt.api.cmdb.system_ptp.move(
            ...     name="object1",
            ...     action="before",
            ...     reference_name="object2"
            ... )
        """
        return self._client.request(
            method="PUT",
            path=f"/api/v2/cmdb/system/ptp",
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
        Clone system/ptp object.
        
        Creates a copy of an existing object with a new identifier.
        
        Args:
            name: Name of object to clone
            new_name: Name for the cloned object
            **kwargs: Additional parameters
            
        Returns:
            API response dictionary
            
        Example:
            >>> # Clone an existing object
            >>> fgt.api.cmdb.system_ptp.clone(
            ...     name="template",
            ...     new_name="new-from-template"
            ... )
        """
        return self._client.request(
            method="POST",
            path=f"/api/v2/cmdb/system/ptp",
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
        Check if system/ptp object exists.
        
        Args:
            name: Name to check
            
        Returns:
            True if object exists, False otherwise
            
        Example:
            >>> # Check before creating
            >>> if not fgt.api.cmdb.system_ptp.exists(name="myobj"):
            ...     fgt.api.cmdb.system_ptp.post(payload_dict=data)
        """
        # Use direct request with silent error handling to avoid logging 404s
        # This is expected behavior for exists() - 404 just means "doesn't exist"
        endpoint = "/system/ptp"
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

