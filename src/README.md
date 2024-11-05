# Sharing Torrent-like Application
HCMUTorrent

## Setup
**Install libraries**

`pip install -r requirements.txt`

**Configure**

Assign the IP address of the tracker to the ***tracker_url*** variable in the BackEnd/Helper.py

Create ***Share_File*** folder in BackEnd folder

**Run tracker**

`cd BackEnd`

`python TrackerBackEnd.py`

**Run app**

`streamlit run app.py`
