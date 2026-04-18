# Global Address Verification & Standardization API

A professional-grade FastAPI project for validating and standardizing global addresses. Designed to be hosted on **Cloudflare Workers** or any Python environment. It allows end-users to provide their own API keys for Google Maps or Smarty, or use the **completely free** OpenStreetMap integration.

## Features
- **Tiered Verification**: 
    1. **Smarty**: High-accuracy US address validation.
    2. **Google Maps**: Global coverage and geocoding.
    3. **OpenStreetMap (OSM)**: **Completely Free** global verification (using Nominatim).
    4. **Fallback Logic**: Robust built-in standardization for common abbreviations.
- **Bring Your Own Key (BYOK)**: Support for custom Google/Smarty keys via request headers.
- **Cloudflare Worker Ready**: Optimized for deployment on Cloudflare's new Python Workers.
- **Security**: API Key authentication included (`X-API-Key` header).
- **Rate Limiting**: Protect your server with built-in request limits per IP.
- **Geocoding**: Get latitude and longitude for every valid address.
- **Interactive Documentation**: Auto-generated Swagger/OpenAPI docs.

## Installation & Deployment

### Local Development
1. **Clone the project** and navigate to the directory.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Rename `.env.example` to `.env` and add your private API key:
   - `API_KEY`: Your private access key (e.g., `your-secret-key-123`).
   - `GOOGLE_MAPS_API_KEY`: (Optional) Default key for Google Cloud Console.
   - `SMARTY_AUTH_ID` & `SMARTY_AUTH_TOKEN`: (Optional) Default keys for Smarty.com.

4. **Run the Server**:
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Cloudflare Workers Deployment
1. Install Wrangler CLI: `npm install -g wrangler`
2. Login to Cloudflare: `wrangler login`
3. Deploy: `wrangler deploy`
   - The project includes `wrangler.toml` configured for Python Workers.

## API Usage
Access the interactive documentation at `http://localhost:8000/docs`.

**Endpoint**: `POST /verify`
**Required Header**: `X-API-Key: your-secret-key-123`

**Optional Headers (Bring Your Own Key)**:
- `X-Google-Key`: Custom Google Maps API Key.
- `X-Smarty-Id`: Custom Smarty Auth ID.
- `X-Smarty-Token`: Custom Smarty Auth Token.
- `X-OSM-User-Agent`: Custom User-Agent for OpenStreetMap (Recommended for high volume).
