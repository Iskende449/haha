# iOS Backend Handoff

Use the `explorer` API as the primary mobile contract. The older `/route` endpoint is legacy/demo and should not be the default integration path.

## Auth

- `POST /auth/register`
  - body: `{ "email": "...", "password": "...", "full_name": "..." }`
- `POST /auth/login`
  - returns:
  ```json
  {
    "access_token": "jwt",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "Nomad Traveler",
      "experience_points": 0
    }
  }
  ```
- `GET /auth/me`
  - returns the current user.

Send `Authorization: Bearer <token>` on all protected requests.

## Bootstrap

- `GET /explorer/bootstrap`
  - public endpoint
  - contains app defaults, map themes, marker presets, transport presets, route rendering presets, and voice defaults.

Important fields:

- `map.themes`
  - use `tile_url`, `attribution`, `tile_size`, `zoom_offset`, `max_zoom`
- `markers`
  - canonical marker accent/icon metadata by location kind
- `voice`
  - default TTS guidance settings
- `route_rendering.segment_presets`
  - generic meaning of route segment kinds

## Catalog

- `GET /explorer/locations`

Supported query params:

- `query`
- `kind`: `all | petroglyph | sacred_site | calendar_event`
- `terrain`: `all | mountain | lake | valley | steppe | city`
- `verified_only`: `true | false`
- `route_ready_only`: `true | false`
- `sort`: `smart | distance | name`
- `limit`
- `offset`
- `user_lat`
- `user_lon`

The server already handles filtering, ranking, and direct-distance calculation. Do not reimplement the web ranking logic on iOS.

Important fields per item:

- `distance_from_user_m`
- `media.hero_image_url`
- `map_marker`
- `badges`
- `route_available`

Response-level helpers:

- `recommended_source_id`
- `applied_filters`

## Location Detail

- `GET /explorer/locations/{source_id}?user_lat=...&user_lon=...`

Important fields:

- `gallery`
- `media`
- `archaeological_description`
- `ethnographic_description`
- `distance_from_user_m`

## Route

- `POST /explorer/route`
  - body:
  ```json
  {
    "source_id": 123,
    "user_lat": 42.87,
    "user_lon": 74.61,
    "transport_mode": "car",
    "locale": "ru",
    "route_style": "smart"
  }
  ```

Important fields in response:

- `route_geometry`
  - raw GeoJSON feature
- `render_segments`
  - preferred source for drawing the route
  - already includes segment kind, colors, dash pattern, width, opacity, distance, duration
- `viewport`
  - preferred camera mode and bounds/zoom hints
- `legend`
  - localized legend rows for the current route
- `voice_guidance`
  - canonical TTS payload: `text`, `locale`, `rate`, `pitch`, `volume`, `preferred_voice_gender`
- `analysis`
  - narrative summary
- `steps`
  - turn-by-turn list

Route rendering rules:

- draw from `render_segments` first
- use `route_geometry` as a fallback only if `render_segments` is empty
- do not infer dashed/solid logic client-side if server styles are present

## Profile

- `GET /profile`
  - returns current user, stats, and unlocked legend quests from completed check-ins

## Check-in

- `POST /checkin`
  - use after route arrival / on-site interaction
  - returns either `pending_quest` or `success`

## Deploy Notes

- Set a real `JWT_SECRET_KEY`
- Configure routing providers as available:
  - `OSRM_BASE_URL`
  - `MAPBOX_ACCESS_TOKEN`
  - `ORS_API_KEY`
- Optional AI text:
  - `GEMINI_API_KEY`

The backend has routing fallback order:

1. OSRM
2. Mapbox
3. OpenRouteService
4. internal straight-line fallback

That means iOS should still render a route payload even if premium providers are unavailable.
