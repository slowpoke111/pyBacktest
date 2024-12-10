from pyBacktest.tradeTypes import InvalidCommissionTypeError

def calculate_commission(commisionType: str, commision: float, price: float, numShares: int) -> float:
    if commisionType == "FLAT":
        return commision
    elif commisionType == "PERCENTAGE":
        return price * commision * numShares
    elif commisionType == "PERCENTAGE_PER_SHARE":
        return commision * numShares
    elif commisionType == "PER_SHARE":
        return commision * numShares
    else:
        raise InvalidCommissionTypeError(f"Invalid commission type: {commisionType}, accepted types are FLAT, PERCENTAGE, PERCENTAGE_PER_SHARE, and PER_SHARE")
