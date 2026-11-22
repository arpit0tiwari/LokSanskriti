# LokSanskriti — India's Living Heritage

LokSanskriti is a web platform concept for discovering, exploring, and preserving India's cultural heritage. It brings traditions, regional languages, locations, and community contributions together in one place.

## Features

- **Discover traditions:** Browse cultural traditions and search by tradition name, state, or language.
- **Filters:** Narrow results using state, category, and language filters.
- **Heritage map:** Explore cultural heritage locations on an interactive map powered by Leaflet and OpenStreetMap.
- **Heritage gallery:** View visual highlights related to India's culture and traditions.
- **Community contribution form:** Submit information about a tradition, including its name, state, district, language, category, and description.
- **Live statistics:** Display platform statistics retrieved from the backend.
- **Responsive interface:** Designed to work on desktop and mobile screens.

## Tech Stack

| Part | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Map | Leaflet.js, OpenStreetMap |
| Fonts | Google Fonts — DM Sans and Playfair Display |
| Backend API | Python / FastAPI |
| Data exchange | JSON over HTTP |

## Project Structure

The current frontend is a single-page website:

```text
LokSanskriti/
├── index.html       # Complete frontend: layout, styling and JavaScript
└── README.md        # Project documentation
```

The backend is maintained separately and is accessed by the frontend through the configured API URL.

## Run Locally

### 1. Download the project

Download or clone this repository, then open the project folder in VS Code.

### 2. Start a local web server

Open the VS Code terminal in the folder containing `index.html` and run:

```bash
python -m http.server 5500
```

If `python` is not recognized on Windows, try:

```powershell
py -m http.server 5500
```

### 3. Open the website

Visit:

http://localhost:5500

You can also use the VS Code **Live Server** extension and open `index.html` with Live Server.

## Backend API

The frontend is currently configured to use this API base URL:

https://loksanskriti.onrender.com

The page makes requests to these endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/stats` | Fetch dashboard statistics |
| GET | `/api/traditions` | Fetch traditions and apply available filters/search parameters |
| POST | `/api/traditions` | Submit a new tradition from the contribution form |

The backend must be running and accessible for live statistics, tradition data, and submissions to work. If you deploy your own backend, update the API base URL in the JavaScript inside `index.html` to your backend URL.

## External Services and Libraries

The frontend loads some resources from external services:

- [Google Fonts](https://fonts.google.com/)
- [Leaflet](https://leafletjs.com/)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [Unsplash](https://unsplash.com/) for gallery and visual imagery

An internet connection is required for these external resources and the hosted backend API.

## Future Improvements

- Add authentication and user profiles.
- Add moderation and verification for community-submitted traditions.
- Improve accessibility and multilingual support.
- Add richer cultural video archives.
- Add automated tests and deployment documentation for the backend.

## Contributing

Contributions and suggestions are welcome. For a code change, create a branch, make the change, and open a pull request with a short explanation of what was improved.

## License

No license has been specified for this project yet. Add a `LICENSE` file before permitting reuse or redistribution.
