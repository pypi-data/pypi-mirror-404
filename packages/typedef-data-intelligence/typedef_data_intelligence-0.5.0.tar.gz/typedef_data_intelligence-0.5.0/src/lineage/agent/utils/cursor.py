"""Query result cursor for pagination."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryCursor:
    """Cursor for paginated access to query results.

    Stores the full query result and provides paginated access.
    Used by orchestrators to pass large result sets to presenters
    without overwhelming their context windows.

    WARNING: This cursor stores raw query results. Orchestrators MUST
    ensure PII is filtered or masked before creating cursors.
    """

    cursor_id: str = field(default_factory=lambda: f"cursor_{uuid.uuid4().hex[:12]}")
    query: str = ""
    description: str = ""
    result: List[Dict[str, Any]] = field(default_factory=list)
    page_size: int = 50
    semantic_pii_columns: List[str] = field(default_factory=list)  # PII columns from semantic layer

    # EGREGIOUS PII patterns - only truly sensitive data
    # Business identifiers (customer_id, customer_name, account_name) are NOT flagged
    # Rely on semantic layer for comprehensive PII detection
    EGREGIOUS_PII_PATTERNS: Set[str] = field(default_factory=lambda: {
        # Financial - highly sensitive
        'ssn', 'social_security_number', 'social_security',
        'credit_card', 'card_number', 'cvv', 'ccn', 'card_cvv', 'cvc',
        'routing_number', 'bank_account', 'iban', 'swift',
        'tax_id', 'ein', 'itin',
        # Government IDs
        'passport', 'passport_number', 'driver_license', 'drivers_license',
        'license_number', 'national_id',
        # Medical - HIPAA protected
        'medical_record', 'medical_record_number', 'mrn',
        'diagnosis', 'prescription', 'patient_id',
        # Biometric
        'fingerprint', 'retina', 'facial_recognition', 'biometric',
    })

    def detect_pii_columns(self, semantic_pii_columns: List[str] = None) -> List[str]:
        """Detect PII columns using semantic layer metadata and egregious patterns.

        This method uses a two-tier approach:
        1. Check semantic layer metadata (authoritative source)
        2. Check for egregious PII patterns (SSN, credit cards, etc.)

        Business identifiers like customer_id, customer_name, account_name are NOT
        flagged by pattern matching. They should be marked in the semantic layer if
        they contain actual PII.

        Args:
            semantic_pii_columns: List of columns marked as PII in semantic layer metadata

        Returns:
            List of column names that are PII (from semantic layer or egregious patterns)

        Note:
            The semantic layer is the authoritative source for PII detection.
            Pattern matching only catches truly egregious cases (SSN, CVV, etc.).
        """
        if not self.result:
            return []

        pii_columns = []

        # 1. Use semantic layer metadata if available (authoritative)
        if semantic_pii_columns:
            pii_columns.extend(semantic_pii_columns)

        # 2. Check for egregious PII patterns as fallback
        schema = self.schema
        for col in schema:
            if col in pii_columns:
                continue  # Already flagged by semantic layer

            col_lower = col.lower()
            # Check if column name contains any EGREGIOUS PII pattern
            for pattern in self.EGREGIOUS_PII_PATTERNS:
                if pattern in col_lower:
                    pii_columns.append(col)
                    break

        return pii_columns

    def log_pii_warning(self) -> None:
        """Log warning if PII columns are detected in the result set."""
        pii_columns = self.detect_pii_columns(semantic_pii_columns=self.semantic_pii_columns)
        if pii_columns:
            logger.warning(
                "⚠️  Cursor %s contains PII columns: %s. "
                "Orchestrator should have filtered these before cursor creation. "
                "Presenter will redact PII from reports.",
                self.cursor_id, pii_columns
            )

    @property
    def total_rows(self) -> int:
        """Total number of rows in result set."""
        return len(self.result)

    @property
    def total_pages(self) -> int:
        """Total number of pages (rounded up)."""
        if not self.result:
            return 0
        return (self.total_rows + self.page_size - 1) // self.page_size

    @property
    def schema(self) -> List[str]:
        """Column names from result."""
        return list(self.result[0].keys()) if self.result else []

    def get_page(self, page_num: int) -> Dict[str, Any]:
        """Get a specific page of results.

        Args:
            page_num: 0-indexed page number

        Returns:
            Dictionary with rows, page_num, page_size

        Raises:
            ValueError: If page_num is out of bounds
        """
        if page_num < 0 or page_num >= self.total_pages:
            raise ValueError(
                f"Page {page_num} out of bounds (total pages: {self.total_pages})"
            )

        start = page_num * self.page_size
        end = start + self.page_size

        return {
            "rows": self.result[start:end],
            "page_num": page_num,
            "page_size": self.page_size,
        }

    def has_more_pages(self, current_page: int) -> bool:
        """Check if there are more pages after the given page."""
        return current_page < self.total_pages - 1

    def _serialize_for_json(self, obj: Any) -> Any:
        """Recursively serialize objects to be JSON-safe.

        Handles date, datetime, Decimal, and other non-JSON types.
        """
        from datetime import date, datetime
        from decimal import Decimal

        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        else:
            return obj

    def to_lightweight_payload(self, include_first_page: bool = True) -> Dict[str, Any]:
        """Create lightweight payload for passing to subagents.

        Args:
            include_first_page: Include first page of rows

        Returns:
            Dictionary with cursor metadata and optional first page

        Note:
            Automatically includes PII column warnings if detected.
            All date/datetime objects are serialized to ISO format strings.
        """
        payload = {
            "cursor_id": self.cursor_id,
            "description": self.description,
            "query": self.query,
            "schema": self.schema,
            "total_rows": self.total_rows,
            "total_pages": self.total_pages,
        }

        # Check for PII columns and add warning
        pii_columns = self.detect_pii_columns(semantic_pii_columns=self.semantic_pii_columns)
        if pii_columns:
            payload["pii_warning"] = {
                "detected_pii_columns": pii_columns,
                "message": "⚠️ PII detected. Redact these columns from user-facing reports."
            }

        if include_first_page and self.result:
            # Serialize first page to ensure JSON compatibility
            first_page = self.get_page(0)
            payload["first_page"] = self._serialize_for_json(first_page)
            payload["has_more"] = self.has_more_pages(0)

        return payload


@dataclass
class CursorRegistry:
    """Registry for managing query cursors.

    Orchestrators use this to store and retrieve cursors
    during subagent interactions.
    """

    _cursors: Dict[str, QueryCursor] = field(default_factory=dict)

    def register(self, cursor: QueryCursor) -> str:
        """Register a cursor and return its ID."""
        self._cursors[cursor.cursor_id] = cursor
        return cursor.cursor_id

    def get(self, cursor_id: str) -> QueryCursor:
        """Retrieve a cursor by ID.

        Raises:
            KeyError: If cursor not found
        """
        if cursor_id not in self._cursors:
            raise KeyError(f"Cursor not found: {cursor_id}")
        return self._cursors[cursor_id]

    def remove(self, cursor_id: str) -> None:
        """Remove a cursor from registry."""
        self._cursors.pop(cursor_id, None)

    def clear(self) -> None:
        """Clear all cursors."""
        self._cursors.clear()

    def get_page(self, cursor_id: str, page_num: int) -> Dict[str, Any]:
        """Get a page from a cursor (convenience method).

        Args:
            cursor_id: Cursor ID
            page_num: Page number (0-indexed)

        Returns:
            Page data with rows

        Raises:
            KeyError: If cursor not found
            ValueError: If page out of bounds
        """
        cursor = self.get(cursor_id)
        return cursor.get_page(page_num)
