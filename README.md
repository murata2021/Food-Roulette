# Food-Roulette

Food Roulette is my capstone one project for my software engineering bootcamp with Springboard. It is a web application that helps users decide what to eat and where to eat by randomly suggesting meals based on the user’s selection of cuisine or food category, and showing the nearby restaurants offering the selected meals It is hosted on https://food-roulette-2021.herokuapp.com/

## Project Proposal

Please click on [the link](https://github.com/murata2021/Food-Roulette/blob/main/project-proposal.md "Title") to view the original project proposal.

## Navigation
Here the general process for a user:

1. Without signup and login, the user will be able to use the search bar to search meals in the database. The user will be able to view the single meal and its ingredients. To see/write/like reviews the user has to be logged in.
2. Sign-up or log in to the food roulette: It’ll prompt the user on the home page. On the home page, there are three options for the user to proceed.The user will be able to pick his/her random food from the selected category, selected cuisine, or in a totally random way from all meals in the database. 
3. After he/she selects the option he/she wants, a random meal will appear on his/her screen. The user will pass it or like it. If he/she passes it, another meal will pop out on his/her screen.
4. The liked meal will be added to the database. When the user likes the meal, based on the location preference, restaurants that serve this meal will be displayed.
5. The user will be able to see each restaurant’s details.
6. The user can like the restaurants or he/she can move on.
7. After the user likes meal or meal&restaurant together, he/she will be able to write review.Each individual user will have their own user pages.
8. User pages have four contents. The user's own reviews, user's favorite meals, user's favorite restaurants, reviews that user found useful.
9. At any time, the user will be able to remove restaurants, meals from their favorite list.

## API List

- The Mealdb Api: https://www.themealdb.com/api.php
- The Yelp Fusion Api: https://www.yelp.com/developers/documentation/v3/get_started

## Technologies & Tools Used

- HTML
- CSS
- JavaScript
- PostgreSQL
- Python
- Flask 
   * Jinja
   * Flask SQL-Alchemy
   * Flask WTForms
   * Flask Bcrypt 
