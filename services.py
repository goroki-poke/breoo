import os
import json
import logging
from js import fetch
from typing import Optional
from models import AddressBase, AddressResponse, AddressRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_google_component(components, type_name):
    """Helper to find a specific address component type from Google response."""
    for component in components:
        if type_name in component["types"]:
            return component["long_name"]
    return ""

async def verify_with_smarty(address: AddressRequest, env, auth_id: Optional[str] = None, auth_token: Optional[str] = None) -> Optional[AddressResponse]:
    """Verification using Smarty (US only for basic, global for international license)."""
    # Use provided keys or fall back to environment variables
    auth_id = auth_id or (env.SMARTY_AUTH_ID if hasattr(env, "SMARTY_AUTH_ID") else None)
    auth_token = auth_token or (env.SMARTY_AUTH_TOKEN if hasattr(env, "SMARTY_AUTH_TOKEN") else None)
    
    if not auth_id or not auth_token:
        return None
        
    logger.info("Using Smarty for verification")
    try:
        url = "https://us-street.api.smarty.com/street-address"
        query_params = f"?auth-id={auth_id}&auth-token={auth_token}&street={address.street}&city={address.city}&state={address.state}&zipcode={address.zip_code}&candidates=1"
        
        response = await fetch(url + query_params)
        data = await response.json()
        
        if data:
            result = data[0]
            metadata = result.get("metadata", {})
            components = result.get("components", {})
            
            # Reconstruct standardized address
            std_street = f"{components.get('primary_number', '')} {components.get('street_name', '')} {components.get('street_suffix', '')}".strip()
            
            standardized = AddressBase(
                street=std_street,
                city=components.get("city_name", address.city).upper(),
                state=components.get("state_abbreviation", address.state).upper(),
                zip_code=f"{components.get('zipcode', address.zip_code)}-{components.get('plus4_code', '')}".strip("-"),
                country="USA"
            )
            
            return AddressResponse(
                original_address=address,
                standardized_address=standardized,
                is_valid=True,
                confidence_score=1.0 if result.get("analysis", {}).get("active") == "Y" else 0.5,
                geocoding={"lat": metadata.get("latitude"), "lng": metadata.get("longitude")},
                formatted_address=result.get("delivery_line_1", "") + ", " + result.get("last_line", ""),
                provider="smarty"
            )
    except Exception as e:
        logger.error(f"Error calling Smarty API: {str(e)}")
    return None

async def verify_with_osm(address: AddressRequest, user_agent: Optional[str] = None) -> Optional[AddressResponse]:
    """Verification using OpenStreetMap (Nominatim) - Completely Free."""
    # OSM requires a descriptive User-Agent
    ua = user_agent or "GlobalAddressVerificationAPI/1.1 (Contact: support@yourdomain.com)"
    
    logger.info("Using OpenStreetMap (Nominatim) for verification")
    try:
        address_str = f"{address.street}, {address.city}, {address.state} {address.zip_code}, {address.country}"
        url = f"https://nominatim.openstreetmap.org/search?q={address_str}&format=json&addressdetails=1&limit=1"
        
        headers = {"User-Agent": ua}
        
        response = await fetch(url, headers=headers)
        data = await response.json()
        
        if data:
            result = data[0]
            osm_addr = result.get("address", {})
            
            # Reconstruct standardized address from OSM components
            standardized = AddressBase(
                street=f"{osm_addr.get('house_number', '')} {osm_addr.get('road', address.street)}".strip().upper(),
                city=osm_addr.get("city", osm_addr.get("town", address.city)).upper(),
                state=osm_addr.get("state", address.state).upper(),
                zip_code=osm_addr.get("postcode", address.zip_code),
                country=osm_addr.get("country", address.country).upper()
            )
            
            return AddressResponse(
                original_address=address,
                standardized_address=standardized,
                is_valid=True,
                confidence_score=0.8, # OSM is great but can be less precise than Google/Smarty
                geocoding={"lat": float(result["lat"]), "lng": float(result["lon"])},
                formatted_address=result.get("display_name", ""),
                provider="osm"
            )
    except Exception as e:
        logger.error(f"Error calling OSM API: {str(e)}")
    return None

async def standardize_address(
    address: AddressRequest, 
    env,
    google_key: Optional[str] = None, 
    smarty_id: Optional[str] = None, 
    smarty_token: Optional[str] = None,
    osm_user_agent: Optional[str] = None
) -> AddressResponse:
    """
    Standardizes and validates an address using multiple providers.
    1. Try Smarty (best for US accuracy)
    2. Try Google (best for global)
    3. Try OpenStreetMap (Free Global)
    4. Fallback to basic logic
    """
    logger.info(f"Standardizing address: {address}")
    
    # 1. Try Smarty (Only if user provided keys or they are set in env)
    smarty_id = smarty_id or (env.SMARTY_AUTH_ID if hasattr(env, "SMARTY_AUTH_ID") else None)
    smarty_token = smarty_token or (env.SMARTY_AUTH_TOKEN if hasattr(env, "SMARTY_AUTH_TOKEN") else None)
    
    if smarty_id and smarty_token:
        smarty_result = await verify_with_smarty(address, env, auth_id=smarty_id, auth_token=smarty_token)
        if smarty_result:
            return smarty_result

    # 2. Try Google Maps (Only if user provided key or it's set in env)
    google_api_key = google_key or (env.GOOGLE_MAPS_API_KEY if hasattr(env, "GOOGLE_MAPS_API_KEY") else None)
    if google_api_key:
        logger.info("Using Google Maps Geocoding API for verification")
        try:
            address_str = f"{address.street}, {address.city}, {address.state} {address.zip_code}, {address.country}"
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address_str}&key={google_api_key}"
            response = await fetch(url)
            data = await response.json()
            
            if data["status"] == "OK":
                result = data["results"][0]
                components = result["address_components"]
                
                # Refined component mapping
                street_num = get_google_component(components, "street_number")
                route = get_google_component(components, "route")
                city = get_google_component(components, "locality") or get_google_component(components, "sublocality")
                state = get_google_component(components, "administrative_area_level_1")
                country = get_google_component(components, "country")
                zip_code = get_google_component(components, "postal_code")
                
                standardized = AddressBase(
                    street=f"{street_num} {route}".strip().upper() or address.street.upper(),
                    city=city.upper() or address.city.upper(),
                    state=state.upper() or address.state.upper(),
                    zip_code=zip_code or address.zip_code,
                    country=country.upper() or address.country.upper()
                )
                
                return AddressResponse(
                    original_address=address,
                    standardized_address=standardized,
                    is_valid=True,
                    confidence_score=1.0,
                    geocoding=result["geometry"]["location"],
                    formatted_address=result["formatted_address"],
                    provider="google"
                )
            else:
                logger.warning(f"Google Maps API returned status: {data['status']}")
        except Exception as e:
            logger.error(f"Error calling Google Maps API: {str(e)}")

    # 3. Try OpenStreetMap (Free Global)
    osm_result = await verify_with_osm(address, user_agent=osm_user_agent)
    if osm_result:
        return osm_result

    # 4. Fallback to Basic logic
    logger.info("Using basic fallback standardization logic")
    try:
        std_street = address.street.strip().upper()
        std_city = address.city.strip().upper()
        std_state = address.state.strip().upper()
        std_zip = address.zip_code.strip()
        std_country = address.country.strip().upper()
        
        abbreviations = {
            "STREET": "ST", "AVENUE": "AVE", "ROAD": "RD", "DRIVE": "DR",
            "COURT": "CT", "BOULEVARD": "BLVD", "LANE": "LN",
        }
        
        for full, abbr in abbreviations.items():
            if std_street.endswith(full):
                std_street = std_street.replace(full, abbr)
                break
                
        standardized = AddressBase(
            street=std_street, city=std_city, state=std_state,
            zip_code=std_zip, country=std_country
        )
        
        formatted = f"{std_street}, {std_city}, {std_state} {std_zip}, {std_country}"
        is_valid = all([std_street, std_city, std_state, std_zip, std_country])
        
        return AddressResponse(
            original_address=address,
            standardized_address=standardized,
            is_valid=is_valid,
            confidence_score=0.9 if is_valid else 0.0,
            formatted_address=formatted,
            provider="fallback"
        )
    except Exception as e:
        logger.error(f"Error in fallback: {str(e)}")
        raise