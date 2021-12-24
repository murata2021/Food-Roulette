"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from csv import DictReader


from models import db, connect_db,Cuisine, Category,Message,Meal,User,MealLiked,RestaurantMealLiked,Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///food-roulette-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        MealLiked.query.delete()
        RestaurantMealLiked.query.delete()
        Cuisine.query.delete()
        Meal.query.delete()
        Category.query.delete()
        RestaurantMealLiked.query.delete()

        self.client = app.test_client()
        app.config['TESTING'] = True

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    location='Philadelphia',
                                    image_url=None)

        self.new_user=User.signup(username="newuser",
                                    email="user@test.com",
                                    password="testuser",
                                    location='San Francisco',
                                    image_url=None)

        with open('generator/cuisines.csv') as cuisines:
            db.session.bulk_insert_mappings(Cuisine, DictReader(cuisines))

        with open('generator/categories.csv') as categories:
            db.session.bulk_insert_mappings(Category, DictReader(categories))

        with open('generator/meals.csv') as meals:
            db.session.bulk_insert_mappings(Meal, DictReader(meals))

        db.session.commit()

        meal=Meal.query.filter(Meal.meal_name=='Rock Cakes').first()
        meal_liked=MealLiked(user_id=self.new_user.id,meal_id=meal.id)
        db.session.add(meal_liked)
        db.session.commit()

        restaurant_meal=RestaurantMealLiked(restaurant_name='Amazing restaurant LLC',
                                                    restaurant_yelp_id='yelp_id',
                                                    meals_liked_id=meal_liked.id,
                                                    restaurant_address='address',
                                                    restaurant_rating=4.6,
                                                    restaurant_url='restaurant_url',
                                                    restaurant_photo='photo',
                                                    user_id=self.new_user.id
                )

        db.session.add(restaurant_meal)
        db.session.commit()

    # When you’re logged in, can you see the follower / following pages for any user?

    def test_user_not_loggedin(self):
        """Tests User will not be able to pages when they are not authorized"""

        with self.client as c:

            u=User.query.filter(User.username=='testuser').first()

            meal=Meal.query.filter(Meal.meal_name=='Carrot Cake').first()

            #when user is not logged in, he/she should not be able to view unauthorized pages
            resp= c.get(f"/users/profile",follow_redirects=True)
            html = resp.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp.status_code, 200)

            resp1= c.get(f"/users/profile")
            self.assertEqual(resp1.status_code, 302)
            self.assertEqual(resp1.location,f"http://localhost/")
  
            resp2=c.get(f"/users/{u.id}",follow_redirects=True)
            html = resp2.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp2.status_code, 200)

            resp3=c.get(f"/logout")
            self.assertEqual(resp3.status_code, 302)
            self.assertEqual(resp3.location,f"http://localhost/")

            resp4=c.get(f"/cuisines",follow_redirects=True)
            html = resp4.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp4.status_code, 200)

            resp5=c.get('/meals/1/reviews',follow_redirects=True)
            html = resp5.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp5.status_code, 200)

            resp6=c.get('/categories',follow_redirects=True)
            html = resp6.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp6.status_code, 200)

            resp6=c.get('/surprise-me',follow_redirects=True)
            html = resp6.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp6.status_code, 200)

            ###
            resp7=c.post(f'/like-it/{meal.meal_name}',follow_redirects=True)
            html = resp7.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp7.status_code, 200)

            resp8=c.get(f'/show-it/{meal.meal_name}/restaurants',follow_redirects=True)
            html = resp8.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp8.status_code, 200)

            resp9=c.get(f'/like-it/{meal.meal_name}/restaurants/{u.location}',follow_redirects=True)
            html = resp9.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp9.status_code, 200)

            resp10=c.post(f'/restaurant/like-it',follow_redirects=True)
            html = resp10.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp10.status_code, 200)

            resp11=c.post("/restaurant/<restaurant_yelp_id>/unlink-restaurant-meal/1",follow_redirects=True)
            html = resp11.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp11.status_code, 200)

            resp12=c.post("/restaurant/remove-it/<restaurant_yelp_id>",follow_redirects=True)
            html = resp12.get_data(as_text=True)            # Make sure it redirects
            self.assertIn("Access unauthorized", html)
            self.assertEqual(resp12.status_code, 200)

    def test_user_when_loggedin(self):
        """Tests User when he/she is logged in"""

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            ###When we add a meal we should be able to see that on our liked food page
            meal=Meal.query.filter(Meal.meal_name=='Carrot Cake').first()
            meal_liked=MealLiked(user_id=self.testuser.id,meal_id=meal.id)
            db.session.add(meal_liked)
            db.session.commit()

            resp=c.get(f"/users/{sess[CURR_USER_KEY]}/liked-food")
            html = resp.get_data(as_text=True)
            self.assertIn(f"{self.testuser.username}'s favorite meals", html)
            self.assertIn("Carrot Cake", html)
            self.assertEqual(resp.status_code, 200)

            ##Soft delete carrot cake from users fav meals
            resp1=c.post(f"/meals-liked/remove-it/{meal.id}")
            
            #when we soft deleted a meal we should not be able to see it on our page
            resp=c.get(f"/users/{sess[CURR_USER_KEY]}/liked-food")
            html = resp.get_data(as_text=True)
            self.assertIn(f"{self.testuser.username}'s favorite meals", html)
            self.assertNotIn("Carrot Cake", html)
            self.assertEqual(resp.status_code, 200)

            ###We should be able to view another person's fav meal
            u=User.query.filter(User.username=='newuser').first()
            resp=c.get(f"/users/{u.id}/liked-food")
            html = resp.get_data(as_text=True)
            self.assertIn(f"{u.username}'s favorite meals", html)
            self.assertIn("Rock Cakes", html)
            self.assertEqual(resp.status_code, 200)

            ###We should be able to view another person's fav restaurant
            
            resp=c.get(f"/users/{u.id}/liked-restaurants")
            html = resp.get_data(as_text=True)
            self.assertIn(f"{u.username}'s favorite restaurants", html)
            self.assertIn("Amazing restaurant LLC", html)
            self.assertEqual(resp.status_code, 200)

    def test_remove_restaurants(self):
        """Test remove restaurant"""

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.new_user.id
            
            ###logged in user can see his/her fav restaurants
            resp=c.get(f"/users/{sess[CURR_USER_KEY]}/liked-restaurants")
            html = resp.get_data(as_text=True)
            self.assertIn(f"{self.new_user.username}'s favorite restaurants", html)
            self.assertIn("Amazing restaurant LLC", html)
            self.assertEqual(resp.status_code, 200)

            ###it soft deletes restaurant
            resp=c.post(f"/restaurant/remove-it/yelp_id")

            ###when the restaurant is soft deleted from fav list, we should not view it
            resp=c.get(f"/users/{sess[CURR_USER_KEY]}/liked-restaurants")
            html = resp.get_data(as_text=True)
            self.assertIn(f"{self.new_user.username}'s favorite restaurants", html)
            self.assertNotIn("Amazing restaurant LLC", html)
            self.assertEqual(resp.status_code, 200)

    def test_delete_user(self):
        """Test delete user"""

        with self.client as c:
            user=User.query.filter(User.username=='username').first()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.new_user.id
            
            ##when you delete your profile, you will be redirected to signup page
            resp=c.post(f"users/delete")
            html = resp.get_data(as_text=True)            # Make sure it redirects
            self.assertEqual(resp.location,f"http://localhost/signup")

        

