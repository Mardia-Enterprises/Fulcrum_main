Let's just focus on frontend folder. Always remember to maintain onlt one .env file. This should only be present in the root directory. we can reference variables from that .env file. Do not expose API keys in code files.

The Teams page is not functioning correctly in frontend, by default as soon as the user opens up the teams page all Employees should be loaded, each employee should have its own card like shown in the image with a place holder for profile photo. when clicked on this card it should take to each employee page which contains all details about the employee. This information can be fetched using API, refer the readme for how to use the API@README.md . Similarly add employee button should have 2 options just like how it is merntioned in API one for file upload and other for manual, same for remove, role etc. Make sure u dont make changes in backend folder.
The data is not loading on teams page right now. the API is up and running on localhost for now.

Secondly the styling of the Navbar is not correct, it is on the left side of the screen, while it should show under the hamburger icon on the right side of the screen

Same goes for the chat floating button, it should also be on the right bottom corner of the screen.

Same the Profile page has weird styling, fix the styling in the Profile page.