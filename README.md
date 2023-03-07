# ibudget_web
Welcome to my iBudget web app! Originally, this web page was built as an excercise to learn more about python apps, web design, database management, and my first serious journey into learning JavaScript. It was also designed to solve a couple of problems I had with my extensive budget spreadsheet. Today, this application serves as my main budget-tracking tool. Weekly updates expand the features available to end users making the app easier and more convenient to use.

The project was built in Python 3.10 using Flask and Pandas. I have been able to launch a live test server using PythonAnywhere so I can use the budget app anywhere. While the mobile experience is not ideal at this stage, being able to access and edit the data over the cloud is extremely useful to my daily routine.


## Instructions:
1) Clone this repository

2) (Recommended) setup Python virtual environment using Python 3.10

3) Use pip to install requirements

4) Run `python budget_server.py`
 > -- db_file [optional] Defaults to the file specified in config.ini [database.live] section -- Passing a file location as an argument will open an existing or create an empty database at that location. There are python scripts in the /tools directory to create and setup a database file that isn't empty.
 
 > -- port [optional] Default: 9000 -- Specify port to run the flask development server from your local machine

5) (Optional) If you plan on editing, modifying, or deploying the code, it may be helpful to setup your live and testing environment(s).
  - Create environ.ini file at project root, if none exists. The app will create a default file when launched for the first time and set the environment up as "live". An example file is available in /tools directory. This file defines what type of environment the application will be running in. Every time the app launches, it will use that file to determine how to treat the config file. My only use for this is swapping the database file location depending on which computer I'm using to test or modify the code.
  - Update config.ini file to match your preferences and file locations. The main setting to update is directory for the database (.db) file(s).


## Alternative:
Visit https://www.pythonanywhere.com/ and follow their guide to setup a WSGI/Flask app on their hardware. iBudget_web has been suitable for this since v0.1.


## Limitations:
- In general, an adventurous spirit towards reading/modifying the source code is recommended. Certain settings are still held directly within the code, Eventually, I intend to add a settings control page to make edits from the front-end.
- Fewer and fewer things are hard-coded in the source material, but some items remain set to my personal values. In the future, I would like to make it more flexible and almost all aspects of the project are setup to expand the database or configuration files for that flexibility.
