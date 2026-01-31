"""
Utility functions for synthetic data generation.

Common helpers for dates, distributions, and data generation patterns.
"""

import random
from datetime import datetime, timedelta
from typing import List, Tuple, Any, Dict


def add_months(date: datetime, months: int) -> datetime:
    """
    Add months to a date, handling month overflow properly.

    Args:
        date: Starting date
        months: Number of months to add (can be negative)

    Returns:
        New date with months added

    Example:
        >>> add_months(datetime(2024, 1, 31), 1)
        datetime(2024, 2, 29)  # Handles day overflow
    """
    month = date.month + months
    year = date.year + month // 12
    month = month % 12

    if month == 0:
        month = 12
        year -= 1

    # Handle day overflow (e.g., Jan 31 -> Feb 28/29)
    days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = min(date.day, days_in_month[month - 1])

    return date.replace(year=year, month=month, day=day)


def random_date_range(start_date: datetime, end_date: datetime) -> datetime:
    """
    Generate a random date between start and end dates.

    Args:
        start_date: Earliest possible date
        end_date: Latest possible date

    Returns:
        Random date in range

    Example:
        >>> start = datetime(2024, 1, 1)
        >>> end = datetime(2024, 12, 31)
        >>> result = random_date_range(start, end)
    """
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def weighted_choice(options: List[Any], weights: List[float]) -> Any:
    """
    Choose an item from options based on weights.

    Args:
        options: List of choices
        weights: Corresponding weights (don't need to sum to 1)

    Returns:
        One item from options

    Example:
        >>> weighted_choice(['A', 'B', 'C'], [70, 20, 10])
        'A'  # 70% chance
    """
    return random.choices(options, weights=weights)[0]


def tier_based_value(
    tier: str,
    tier_1_range: Tuple[int, int],
    tier_2_range: Tuple[int, int],
    tier_3_range: Tuple[int, int]
) -> int:
    """
    Generate a value based on tier classification.

    Args:
        tier: One of 'Tier 1', 'Tier 2', 'Tier 3'
        tier_1_range: (min, max) for Tier 1
        tier_2_range: (min, max) for Tier 2
        tier_3_range: (min, max) for Tier 3

    Returns:
        Random integer appropriate for the tier

    Example:
        >>> tier_based_value('Tier 1', (1000, 5000), (500, 2000), (100, 1000))
        3250  # Between 1000 and 5000
    """
    ranges = {
        'Tier 1': tier_1_range,
        'Tier 2': tier_2_range,
        'Tier 3': tier_3_range
    }

    min_val, max_val = ranges.get(tier, tier_2_range)
    return random.randint(min_val, max_val)


def add_variance(value: float, variance_pct: float = 0.05) -> float:
    """
    Add random variance to a value (for realism).

    Args:
        value: Base value
        variance_pct: Percentage variance (default 5%)

    Returns:
        Value with random variance applied

    Example:
        >>> add_variance(1000, 0.10)
        1047.23  # ±10% variance
    """
    multiplier = random.uniform(1 - variance_pct, 1 + variance_pct)
    return value * multiplier


def generate_id(prefix: str, number: int, width: int = 3) -> str:
    """
    Generate a formatted ID string.

    Args:
        prefix: ID prefix (e.g., 'ACC', 'TXN')
        number: Numeric portion
        width: Zero-pad width (default 3)

    Returns:
        Formatted ID

    Example:
        >>> generate_id('ACC', 42, width=3)
        'ACC042'
    """
    return f'{prefix}{number:0{width}d}'


def distribution_80_20(total: int, num_top_items: int) -> List[int]:
    """
    Create an 80/20 distribution (Pareto principle).

    80% of the total value goes to top 20% of items.

    Args:
        total: Total value to distribute
        num_top_items: Number of items in top 20%

    Returns:
        List of values following 80/20 distribution

    Example:
        >>> distribution_80_20(1000, 2)  # 2 items get 800, rest get 200
        [400, 400, 50, 50, 50, 50]
    """
    top_portion = int(total * 0.8)
    bottom_portion = total - top_portion

    # Distribute top 80% among top 20% of items
    top_values = [top_portion // num_top_items] * num_top_items

    # Calculate remaining items
    num_bottom_items = num_top_items * 4  # To make 20% top, 80% bottom

    if num_bottom_items > 0:
        bottom_values = [bottom_portion // num_bottom_items] * num_bottom_items
    else:
        bottom_values = []

    return top_values + bottom_values


def realistic_email(first_name: str, last_name: str, domain: str = None) -> str:
    """
    Generate a realistic email address.

    Args:
        first_name: First name
        last_name: Last name
        domain: Email domain (default: example.com)

    Returns:
        Email address

    Example:
        >>> realistic_email('John', 'Doe', 'company.com')
        'john.doe@company.com'
    """
    if domain is None:
        domain = 'example.com'

    formats = [
        f'{first_name}.{last_name}@{domain}',
        f'{first_name[0]}{last_name}@{domain}',
        f'{first_name}{last_name[0]}@{domain}',
        f'{first_name}.{last_name[0]}@{domain}'
    ]

    return random.choice(formats).lower()


def realistic_phone(country_code: str = 'US') -> str:
    """
    Generate a realistic phone number.

    Args:
        country_code: Country code (US, UK, etc.)

    Returns:
        Formatted phone number

    Example:
        >>> realistic_phone('US')
        '555-123-4567'
    """
    if country_code == 'US':
        area_code = random.randint(200, 999)
        prefix = random.randint(200, 999)
        line = random.randint(0, 9999)
        return f'{area_code}-{prefix:03d}-{line:04d}'
    elif country_code == 'UK':
        return f'+44 20 {random.randint(1000, 9999)} {random.randint(1000, 9999)}'
    else:
        return f'+{random.randint(1, 999)}-{random.randint(100000, 999999)}'


class NameGenerator:
    """Generate realistic company and person names."""

    COMPANY_PREFIXES = [
        'Global', 'Tech', 'Data', 'Cloud', 'Digital', 'Smart', 'Advanced',
        'Premier', 'United', 'American', 'National', 'International'
    ]

    COMPANY_BASES = [
        'Solutions', 'Systems', 'Tech', 'Data', 'Analytics', 'Services',
        'Group', 'Partners', 'Industries', 'Corp', 'Enterprises'
    ]

    COMPANY_SUFFIXES = [
        'Inc', 'LLC', 'Corp', 'Ltd', 'Co', 'Group', 'Partners',
        'Associates', 'Holdings', 'GmbH', 'AG', 'SA'
    ]

    FIRST_NAMES = [
        'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard',
        'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara',
        'Sarah', 'Jessica', 'Ashley', 'Emily', 'Samantha', 'Amanda'
    ]

    LAST_NAMES = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
        'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
        'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson'
    ]

    @classmethod
    def company_name(cls, format_type: str = 'full') -> str:
        """
        Generate a company name.

        Args:
            format_type: 'full', 'short', or 'simple'

        Returns:
            Company name string
        """
        if format_type == 'full':
            prefix = random.choice(cls.COMPANY_PREFIXES)
            base = random.choice(cls.COMPANY_BASES)
            suffix = random.choice(cls.COMPANY_SUFFIXES)
            return f'{prefix} {base} {suffix}'
        elif format_type == 'short':
            base = random.choice(cls.COMPANY_BASES)
            suffix = random.choice(cls.COMPANY_SUFFIXES)
            return f'{base} {suffix}'
        else:  # simple
            return f'{random.choice(cls.COMPANY_PREFIXES)} {random.choice(cls.COMPANY_BASES)}'

    @classmethod
    def person_name(cls) -> Tuple[str, str]:
        """
        Generate a person's name.

        Returns:
            Tuple of (first_name, last_name)
        """
        first = random.choice(cls.FIRST_NAMES)
        last = random.choice(cls.LAST_NAMES)
        return first, last


def csv_safe_string(value: Any) -> str:
    """
    Convert value to CSV-safe string.

    Handles None, empty strings, and special characters.

    Args:
        value: Value to convert

    Returns:
        CSV-safe string representation
    """
    if value is None or value == '':
        return ''

    s = str(value)

    # Escape quotes
    if '"' in s:
        s = s.replace('"', '""')

    # Quote if contains comma, newline, or quote
    if ',' in s or '\n' in s or '"' in s:
        s = f'"{s}"'

    return s
