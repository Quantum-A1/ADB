**Welcome to the DayZ Alt Detector Bot**

The DayZ Alt Detector Bot is designed to detect and manage potential alternate (alt) accounts on your DayZ console servers. It integrates with Nitrado server logs, processes player connection data, and stores this data in a MySQL database. The bot scans logs every 5 minutes, detects potential alt accounts based on shared device IDs, and sends alerts to a specific Discord channel.

🚀 Key Features:

**Automated Log Scanning:**

Fetches .RPT logs from Nitrado servers every 5 minutes.
Extracts player data: Gamertag, Gamertag ID, and Device ID.
Stores data and tracks historical changes.

**Alt Account Detection:**

Flags accounts as potential alts if they share the same device ID with different gamertag IDs.
Sends alerts to a Discord channel when an alt is detected.

**Player Data Management:**

Tracks player history, including device changes and gamertag updates.
Allows manual control over alt flags, whitelisting, and watchlisting.

**Database Integration:**

Uses MySQL for efficient data storage.
Provides real-time database status and player statistics.


**🔍 How Alt Detection Works:**

Log Scanning: The bot reads recent DayZ .RPT logs.

Data Extraction: It extracts player gamertags, IDs, and device IDs.

Database Check: Compares device IDs to identify multiple accounts using the same device.

Alert System: Flags potential alts and sends alerts to the configured Discord channel.
