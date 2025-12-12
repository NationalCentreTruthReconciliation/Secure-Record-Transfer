# Frontend Code (JS, CSS)

Assets in this directory are bundled by Bun. These assets get loaded in the application by the Django webpack loader. The bundled assets get copied directly to the static directory without running collectstatic.

Assets that are in static/ directories within individual Django apps are loaded by the Django static app. This includes, for example, small JS and CSS utilities used by the admin.
