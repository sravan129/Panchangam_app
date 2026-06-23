# నిత్య పంచాంగం

Mobile-first Telugu daily Panchangam web app.

## Features

- Tithi, Nakshatra, Yoga, and Karana start/end times
- Sunrise, sunset, Rahu Kalam, Yamagandam, and Gulika
- Hyderabad, Vijayawada, Visakhapatnam, Tirupati, and Warangal
- Date navigation and installable PWA shell
- Lahiri ayanamsa calculations through Swiss Ephemeris

## Run

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    python app.py

Open http://localhost:5000.

## Production note

Panchangam conventions vary. Compare a representative year of results with the exact Telugu tradition you plan to publish before a public release.