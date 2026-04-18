from models import AddressRequest
from services import standardize_address

def test_direct():
    address = AddressRequest(
        street="123 main street",
        city="new york",
        state="ny",
        zip_code="10001",
        country="usa"
    )
    
    print(f"Testing address: {address}")
    result = standardize_address(address)
    print("\n--- Direct Verification Result ---")
    print(f"Is Valid: {result.is_valid}")
    print(f"Standardized: {result.formatted_address}")
    print(f"Confidence: {result.confidence_score}")
    print("--------------------------------\n")

if __name__ == "__main__":
    test_direct()
