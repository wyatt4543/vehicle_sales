---HOW TO COMPILE AND RUN SOURCE CODE---

Once inside of the main code directory to run the code install python at: https://www.python.org/

then in the cmd prompt run:
pip install Flask mysql-connector-python bcrypt secure-smtplib

Double click the app.py python file, or run the python file from the python IDLE
afterwards connect to the host found in the console from a web browser:
my console says: * Running on http://127.0.0.1:5000

Note: the email function may not work due to it requiring a new app password for each new device in app.py on the line that says "server.login(email, "qewutidqrqlfokjh")"

---Database Information---
There are files that show the information in the database stored in the data directory

---INPUT PARAMETERS---
Various prefilled inputs that explain how to fill the information

How to fill the non-prefilled:
Street Address: String
Apt., Suite, Etc.: String
City: String
State/Province: String
Postal/Zip Code: Integer
Card Holder Name: String
Card Number: 16 digits
Card Date: Date
Security Code: 6 digits

---Authentication---
Admin:
Admin
1qart2QART!

User:
j400
1234

---Additional info---
Test Info for Purchase:
Mail:
404 Main St.
Apt. 1
Maize
Kansas
43534

Card:
John Smith

bad card number:
1234567890123456

good card number:
5438848981242319

11/27
666

Robot That Email Receipt Login:
vehiclesalesbot@gmail.com
1tarl4TARL!#

---Allowed Values---
All characters that can normally be found in file name are allowed as an input, certain inputs may be restricted to certain values (number and email inputs).