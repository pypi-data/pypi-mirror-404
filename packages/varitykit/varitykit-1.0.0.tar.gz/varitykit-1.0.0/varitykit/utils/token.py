"""
Token utility functions for VarityKit

CRITICAL: Varity L3 uses USDC with 6 decimals (not 18 like ETH)
All token calculations must use proper decimal handling to avoid
catastrophic errors (e.g., sending 1 trillion USDC instead of 1 USDC)
"""

from decimal import Decimal
from typing import Optional, Union


# USDC Constants
USDC_DECIMALS = 6
USDC_SYMBOL = "USDC.e"
USDC_NAME = "Bridged USDC"

# ETH Constants (for reference)
ETH_DECIMALS = 18
WEI_PER_ETH = 10**18


def to_usdc(amount: Union[float, str, Decimal]) -> int:
    """
    Convert USDC amount to 6-decimal integer (base units)

    CRITICAL: USDC uses 6 decimals, not 18!

    Args:
        amount: USDC amount as float, string, or Decimal (e.g., 1.5, "100.25")

    Returns:
        Integer representing USDC in base units (e.g., 1.0 USDC = 1_000_000)

    Examples:
        >>> to_usdc(1.0)
        1000000
        >>> to_usdc("100.50")
        100500000
        >>> to_usdc(0.000001)  # Minimum USDC unit
        1

    Raises:
        ValueError: If amount cannot be converted or has too many decimals
    """
    try:
        # Convert to Decimal for precision
        decimal_amount = Decimal(str(amount))

        # Check for too many decimal places (max 6 for USDC)
        exponent = decimal_amount.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -USDC_DECIMALS:
            raise ValueError(
                f"Amount has too many decimal places. "
                f"USDC supports maximum {USDC_DECIMALS} decimals, "
                f"got: {amount}"
            )

        # Convert to base units (multiply by 10^6)
        base_units = decimal_amount * (10**USDC_DECIMALS)

        # Return as integer
        return int(base_units)

    except (ValueError, ArithmeticError) as e:
        raise ValueError(f"Invalid USDC amount '{amount}': {e}")


def from_usdc(amount: int) -> Decimal:
    """
    Convert USDC base units (6-decimal integer) to Decimal

    Args:
        amount: USDC in base units (e.g., 1_000_000 = 1.0 USDC)

    Returns:
        Decimal representing USDC amount

    Examples:
        >>> from_usdc(1_000_000)
        Decimal('1.0')
        >>> from_usdc(100_500_000)
        Decimal('100.5')
        >>> from_usdc(1)
        Decimal('0.000001')
    """
    if not isinstance(amount, int):
        raise TypeError(f"Amount must be integer, got {type(amount)}")

    if amount < 0:
        raise ValueError(f"Amount must be non-negative, got {amount}")

    # Explicitly cast to Decimal to satisfy type checker
    return Decimal(amount) / Decimal(10**USDC_DECIMALS)


def format_usdc(amount: Union[int, Decimal], symbol: bool = True) -> str:
    """
    Format USDC amount for display

    Args:
        amount: USDC in base units (int) or as Decimal
        symbol: Whether to include USDC symbol

    Returns:
        Formatted string (e.g., "1,234.50 USDC")

    Examples:
        >>> format_usdc(1_000_000)
        '1.0 USDC'
        >>> format_usdc(1_234_567_890)
        '1,234.567890 USDC'
        >>> format_usdc(Decimal('100.5'), symbol=False)
        '100.5'
    """
    if isinstance(amount, int):
        decimal_amount = from_usdc(amount)
    else:
        decimal_amount = amount

    # Format with thousand separators
    formatted = f"{decimal_amount:,.6f}".rstrip('0').rstrip('.')

    if symbol:
        return f"{formatted} {USDC_SYMBOL}"
    return formatted


def parse_usdc(amount_str: str) -> int:
    """
    Parse USDC amount from string (may include symbol)

    Args:
        amount_str: String like "100 USDC", "1,234.56", "100.5 USDC.e"

    Returns:
        USDC in base units (integer)

    Examples:
        >>> parse_usdc("100 USDC")
        100000000
        >>> parse_usdc("1,234.56")
        1234560000
        >>> parse_usdc("0.5 USDC.e")
        500000
    """
    # Remove USDC symbols and whitespace
    cleaned = amount_str.upper().strip()
    for symbol in [USDC_SYMBOL.upper(), "USDC", "USD"]:
        cleaned = cleaned.replace(symbol, "").strip()

    # Remove thousand separators
    cleaned = cleaned.replace(",", "")

    # Convert to base units
    return to_usdc(cleaned)


def validate_usdc_amount(amount: int, min_amount: int = 0, max_amount: Optional[int] = None) -> bool:
    """
    Validate USDC amount is within acceptable range

    Args:
        amount: USDC in base units
        min_amount: Minimum acceptable amount (default: 0)
        max_amount: Maximum acceptable amount (default: no limit)

    Returns:
        True if valid, raises ValueError otherwise

    Examples:
        >>> validate_usdc_amount(1_000_000)  # 1 USDC
        True
        >>> validate_usdc_amount(-100)  # Negative
        Traceback (most recent call last):
        ValueError: Amount must be non-negative
    """
    if amount < 0:
        raise ValueError("Amount must be non-negative")

    if amount < min_amount:
        raise ValueError(
            f"Amount too small: {format_usdc(amount)} < {format_usdc(min_amount)}"
        )

    if max_amount is not None and amount > max_amount:
        raise ValueError(
            f"Amount too large: {format_usdc(amount)} > {format_usdc(max_amount)}"
        )

    return True


# Revenue split helpers (for 70/30 thirdweb split)
def calculate_revenue_split(total_amount: int, platform_percentage: int = 70) -> tuple:
    """
    Calculate revenue split between platform and thirdweb

    Args:
        total_amount: Total USDC amount in base units
        platform_percentage: Platform's percentage (default: 70%)

    Returns:
        Tuple of (platform_amount, thirdweb_amount) in base units

    Examples:
        >>> calculate_revenue_split(100_000_000)  # 100 USDC
        (70000000, 30000000)  # 70 USDC, 30 USDC
    """
    if not 0 <= platform_percentage <= 100:
        raise ValueError(f"Percentage must be 0-100, got {platform_percentage}")

    platform_amount = (total_amount * platform_percentage) // 100
    thirdweb_amount = total_amount - platform_amount

    return (platform_amount, thirdweb_amount)


# Comparison with ETH (for educational purposes)
def usdc_to_wei_comparison(usdc_amount: float) -> dict:
    """
    Show the difference between USDC (6 decimals) and ETH (18 decimals)

    WARNING: This is for educational purposes only!
    DO NOT use this for actual conversions!

    Args:
        usdc_amount: Amount in USDC (e.g., 1.0)

    Returns:
        Dictionary showing the massive difference

    Example:
        >>> usdc_to_wei_comparison(1.0)
        {
            'usdc_amount': 1.0,
            'usdc_base_units': 1000000,
            'if_treated_as_eth_wei': 1000000000000000000,
            'error_multiplier': 1000000000000,
            'warning': 'Using ETH decimals for USDC would send 1 TRILLION times more!'
        }
    """
    usdc_base = to_usdc(usdc_amount)
    eth_wei = int(usdc_amount * WEI_PER_ETH)
    error_multiplier = WEI_PER_ETH // (10**USDC_DECIMALS)

    return {
        "usdc_amount": usdc_amount,
        "usdc_base_units": usdc_base,
        "usdc_decimals": USDC_DECIMALS,
        "if_treated_as_eth_wei": eth_wei,
        "eth_decimals": ETH_DECIMALS,
        "error_multiplier": error_multiplier,
        "warning": f"Using ETH decimals for USDC would send {error_multiplier:,} times more!"
    }


if __name__ == "__main__":
    # Quick tests
    print("USDC Token Utilities - Quick Tests")
    print("=" * 50)

    print("\n1. Basic Conversions:")
    print(f"   to_usdc(1.0) = {to_usdc(1.0):,}")
    print(f"   to_usdc(100.50) = {to_usdc(100.50):,}")
    print(f"   from_usdc(1_000_000) = {from_usdc(1_000_000)}")

    print("\n2. Formatting:")
    print(f"   format_usdc(1_234_567_890) = {format_usdc(1_234_567_890)}")
    print(f"   format_usdc(500_000) = {format_usdc(500_000)}")

    print("\n3. Parsing:")
    print(f"   parse_usdc('100 USDC') = {parse_usdc('100 USDC'):,}")
    print(f"   parse_usdc('1,234.56') = {parse_usdc('1,234.56'):,}")

    print("\n4. Revenue Split (70/30):")
    platform, thirdweb = calculate_revenue_split(100_000_000)
    print(f"   Total: {format_usdc(100_000_000)}")
    print(f"   Platform (70%): {format_usdc(platform)}")
    print(f"   thirdweb (30%): {format_usdc(thirdweb)}")

    print("\n5. CRITICAL WARNING - USDC vs ETH Decimals:")
    comparison = usdc_to_wei_comparison(1.0)
    print(f"   1 USDC = {comparison['usdc_base_units']:,} base units")
    print(f"   1 ETH  = {comparison['if_treated_as_eth_wei']:,} wei")
    print(f"   ⚠️  {comparison['warning']}")
