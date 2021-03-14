36th Americas Cup Telemetry Data
---------------------------------
Data comes from the virtualEye dashboard https://www.americascup.com/en/advanced-dashboard

View the data at 
- https://ac36.herokuapp.com/map
- https://ac36.herokuapp.com/stats_app

This repo contains raw data with 20Hz resolution and interpolated 10Hz data in ac36data folder.

For convenience, it can be installed with `pip install git+https://github.com/dorox/ac36_data`: this will install the ac36data package containing 1Hz data with convenience data access functions.

Ongoing ideas:
-------------------------
1. Scraping all data packets for all races
2. Parsing rudder angle, if this is a useful data
3. Is it possible to get yaw angle from heading and boat track? -YES, but still need to do that.
4. Process course info for map app.

Getting boat data:
-------------------
1. Go to website: https://dx6j99ytnx80e.cloudfront.net/ 
2. Open the chrome debugger (F12) 
3. Go to "Sources" tab
4. Place the breakpoint on the line 8310 of the formatted bundle.js file.
5. Refresh the page, and select the race you want
6. Once the debugger stops at breakpoint, type `copy(e)` in the console below.
7. Voila! you have the raw data from boat 1 in the clipboard.
8. To get the data from  boat 2 : continue the debugger once, it will stop at the same line again, and repeat step 6

Getting all data packets:
--------------------------
1. Set a breakpoint in the formatted bundle.js file, on the line 7804 (`var a = n[t];`)
2. Load the race on the website
3. Type `copy(n)` in the console: You'll get the .json copied into clipboard.
