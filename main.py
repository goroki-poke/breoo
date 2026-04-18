import json
from js import Response, Request
from services import standardize_address
from models import AddressRequest

async def on_fetch(request, env):
    # Get the request method and path
    method = request.method
    url = request.url
    path = "/" + "/".join(url.split("/")[3:])

    # Root endpoint for health check
    if method == "GET" and path == "/":
        return Response.new(json.dumps({
            "api": "Global Address Verification & Standardization",
            "version": "1.1.0",
            "status": "online",
            "monetization": "RapidAPI Ready",
            "auth": "API Key Required (X-API-Key)"
        }), {"headers": {"Content-Type": "application/json"}})

    # Verify endpoint
    if method == "POST" and path == "/verify":
        # 1. Check API Key Security
        api_key = request.headers.get("X-API-Key")
        expected_key = env.API_KEY or "your-secret-key-123"
        
        # DEBUG LOGS - View these in 'wrangler tail'
        print(f"DEBUG: Received X-API-Key: '{api_key}'")
        print(f"DEBUG: Expected API_KEY: '{expected_key}'")
        
        if api_key != expected_key:
            return Response.new(json.dumps({"detail": "Invalid API Key"}), {
                "status": 403, 
                "headers": {"Content-Type": "application/json"}
            })

        # 2. Parse Request Body
        try:
            body = await request.json()
            # Convert dict to Pydantic model
            address_req = AddressRequest(**body)
        except Exception as e:
            return Response.new(json.dumps({"detail": f"Invalid request body: {str(e)}"}), {
                "status": 400, 
                "headers": {"Content-Type": "application/json"}
            })

        # 3. Process Address Verification
        try:
            # Get optional BYOK headers
            google_key = request.headers.get("X-Google-Key")
            smarty_id = request.headers.get("X-Smarty-Id")
            smarty_token = request.headers.get("X-Smarty-Token")
            osm_ua = request.headers.get("X-OSM-User-Agent")

            result = await standardize_address(
                address_req,
                env,
                google_key=google_key,
                smarty_id=smarty_id,
                smarty_token=smarty_token,
                osm_user_agent=osm_ua
            )
            
            # Return JSON response
            return Response.new(json.dumps(result.to_json()), {
                "headers": {"Content-Type": "application/json"}
            })
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR processing address: {error_details}")
            return Response.new(json.dumps({
                "detail": "Internal Server Error",
                "error": str(e)
            }), {
                "status": 500, 
                "headers": {"Content-Type": "application/json"}
            })

    # 404 Not Found
    return Response.new(json.dumps({"detail": "Not Found"}), {
        "status": 404, 
        "headers": {"Content-Type": "application/json"}
    })