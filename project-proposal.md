# Food Roulette

##  Project Proposal

###  Problem Definition

People often get confused when there are many options available in front of them. In psychology, this phenomenon is called “over choice” or “choice overload”. Overchoice can be seen in many different settings from increased career options to prospective romantic relationships. Making a decision becomes overwhelming due to the many potential outcomes and overall satisfaction level declines. An abundance of information, opportunities, and products in modern society are the main reasons for over choice.

### Food Roulette

This application (Food Roulette) is focusing on one particular situation when users face over choice phenomenon: making a decision on what to eat and where to eat. Most of the time, people have a difficult time when they pick a restaurant or meal. Sometimes, the picking process takes really long time and the outcome may not be satisfactory.Because people think about the other options they gave up. Food Roulette aims to streamline the users’ decision-making process and increase overall satisfaction by randomizing the selection process and nudging users with the images of meals.The application works in the following way:

- It randomly shows an image of the meal. 
- If the user likes the option, the app shows the nearby restaurants that serve the meal.
- If not, the application shows another random image and the process goes on.

### Target Audience

The target demographic of this application is anyone who has a difficult time when he/she decides where and what to eat.

### Database Schema and APIs

The database scheme will consist of:

- Users: id, username, first name, last name, email, password, location

- Broad meal categories: category id, name

- Individual meals: meal id, meal name, category of the meal

- Users’ likes: id, username, meal id, restaurant id

- Comments: id, username, meal id, restaurant id

- Favorite List: id, username, restaurant id, meal id

- Restaurants: id, name, address

This application uses two APIs:

- Mealdb: for meals, images, meal categories

- Yelp: for nearby restaurants

### Features

Users will log in/signup for the application. They will make a search based on their location selection. If they will like the search results, the application will show the restaurant's detail that serves the selected meal. Users will be able to like the individual meals/restaurants and add them to their favorite list. Also, they can make comments on the meal. There will be a page showing the most liked meals, restaurants, and broad meal categories. The stretch goals for this application would be making the application more like a social platform that users can follow each other, like each other’s messages.