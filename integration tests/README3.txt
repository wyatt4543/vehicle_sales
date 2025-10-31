The tests are manual due to the code being heavily dependent on the user-interface.
First, to run the integration tests you follow the steps in README1.txt to get the website running.

instructions for signing into the admin account:
on the homepage click the "sign in" button. enter the following information on the sign in page:
username: Admin
password: 1qart2QART!

Test 1:
load the homepage by following the instructions in README1.
the test passes if it loads 50 vehicles.

Test 2:
from the homepage click the "sign up" and fill out the information requested.
After submitting the information, attempt to login with the information just provided.
the test passes if the homepage loads and there is a user button in the nav area.

Test 3:
After successfully running test 2, stay signed in.
click on the "User" button. Then, click on the "Mail & Payment Info" button.
On that page input new information and submit it.
the test passes if the inputs autofill with the new information.

Test 4:
After successfully running test 2, stay signed in.
click on the purchase button of a vehicle. Then, fill out all of the required purchase information.
Finally, submit the purchase.
the test passes if the homepage loads and the vehicle has 1 less stock.

Test 5:
start on the homepage. click the different filter options next to the search box. enter different vehicle names in the search box.
the test passes if the filters work and the search box searches for the right vehicles.

Test 6:
follow the instructions for signing into the admin account. click the "Manager" button. Then, click on the "Manage User Information" button.
enter a user's username. update the fields that are provided for the user.
the test passes if you enter that same user's (new username if you updated it) username and the information autofills with updated information.

Test 7:
follow the instructions for signing into the admin account. click the "Manager" button. Then, click on the "Manage Vehicle Inventory" button.
fill out new vehicle information.
the test passes if select that same vehicle and the information autofills with updated information.

Test 8:
follow the instructions for signing into the admin account. click the "Manager" button. Then, click on the "Check Sales Report" button.
the test passes if you see all of the vehicles purchased inside of a table.