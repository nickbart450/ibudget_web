# ibudget_web
Welcome to my iBudget web app. Originally, this web page was built as an excercise to learn more about python apps, web design, database management, and my first serious journey into learning JavaScript. It also solved a couple of problems I had with my fairly extensive budget spreadsheet.

The project was built in Python 3.10 using Flask and Pandas. At this stage, I am only using the built-in flask webserver to run the app locally on my home machine.

To run:
1) clone this repository
2) use pip to install requirements
3) Run: python3 budget_server.py budget_file.db --port <optional port # definition>
  - budget_file.db -- If you do not have an existing database file, the file passed as an argument here will be created and setup for use. There are python scripts in the /tools directory to create and setup a database file that isn't empty
  - port -- [optional] Default: 9000 -- Specify port to run the flask development server from your local machine


Limitations:
- My account names and arbitrary codes are hard-coded all over the place. In the future, I would like to make it more flexible and aspects of the project are setup to utilize database tables for that flexibility.
- Account values are also hard-coded. In the future, this will be updated to include a database table and relevant some setup tools.
- In general, source code editing is still required for a lot of the settings. Eventually, they should be editable from the webpage.
