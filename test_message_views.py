"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


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


class MessageViewTestCase(TestCase):
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

        msg=Message(text='amazing food',restaurant_info='No Restaurant Selected',meals_liked_id=meal_liked.id)
        self.new_user.messages.append(msg)

        db.session.commit()

    def test_messages(self):
        """Test messages"""

        with self.client as c:

            meal=Meal.query.filter(Meal.meal_name=='Rock Cakes').first()

            meal2=Meal.query.filter(Meal.meal_name=='Carrot Cake').first()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.new_user.id

            #check messages written by new_user
            resp=c.get(f"/users/{sess[CURR_USER_KEY]}/messages")
            html = resp.get_data(as_text=True)
            #message is there
            self.assertIn("Rock Cakes", html)
            #No one like it yet!
            self.assertIn("0 user(s) found it useful", html)
            self.assertEqual(resp.status_code, 200)
            

            resp1=c.get(f'/meals/{meal.id}/reviews')
            html = resp1.get_data(as_text=True)
            #message is there
            self.assertIn("Rock Cakes", html)
            #No one like it yet!
            self.assertIn("0 user(s) found it useful", html)
            self.assertEqual(resp1.status_code, 200)

            ####There shouldn't be any review about Carrot Cake
            resp1=c.get(f'/meals/{meal2.id}/reviews')
            html = resp1.get_data(as_text=True)
            self.assertIn("No reviews found", html)
            self.assertNotIn("0 user(s) found it useful", html)
            self.assertEqual(resp1.status_code, 200)



    def test_add_like(self):
        """Test add like"""
            
        with self.client as c:

            user=User.query.filter(User.username=='newuser').first()
            message=user.messages[0]

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            ##initially user doesn't have any liked messages
            resp=c.get(f"/users/{sess[CURR_USER_KEY] }/liked-messages")
            html = resp.get_data(as_text=True)
            self.assertIn("Sorry, no reviews found", html)
            self.assertEqual(resp.status_code, 200)

             ##Like number of user should be 0
            resp2=c.get(f"/users/{user.id}/messages")
            html = resp2.get_data(as_text=True)
            self.assertIn(f"""<p class="small">Likes</p>
                <h4>
                  <a href=''>{0}</a>""", html)
            self.assertEqual(resp2.status_code, 200)

            ##send post request - like the message
            resp=c.post(f"/users/add_like/{message.id}")


            #When you like the message the like number should increase
            resp1=c.get(f"/users/{user.id}/messages")
            html = resp1.get_data(as_text=True)
            self.assertIn("Rock Cakes", html)
            self.assertIn("1 user(s) found it useful", html)  ##1 user like it
            self.assertEqual(resp1.status_code, 200)

            ##we should be able to see messages on the liked-messages page
            resp2=c.get(f"/users/{sess[CURR_USER_KEY] }/liked-messages")
            html = resp1.get_data(as_text=True)
            self.assertIn("Rock Cakes", html)
            self.assertIn("1 user(s) found it useful", html)  ##1 user like it
            self.assertEqual(resp1.status_code, 200)

            ##Like number of user should be 1
            resp2=c.get(f"/users/{user.id}/messages")
            html = resp2.get_data(as_text=True)
            self.assertIn(f"""<p class="small">Likes</p>
                <h4>
                  <a href=''>{1}</a>""", html)
            self.assertEqual(resp2.status_code, 200)

    def test_remove_like(self):
        """Test remove like"""
            
        with self.client as c:

            user=User.query.filter(User.username=='newuser').first()
            message=user.messages[0]

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            ##send post request - like the message
            resp1=c.post(f"/users/add_like/{message.id}")

            resp1=c.get(f"/users/{user.id}/messages")
            html = resp1.get_data(as_text=True)
            self.assertIn("Rock Cakes", html)
            self.assertIn("1 user(s) found it useful", html)  ##1 user like it
            self.assertEqual(resp1.status_code, 200)

            ##When you click on like button again it should remove the like
            resp1=c.post(f"/users/add_like/{message.id}")
            resp1=c.get(f"/users/{user.id}/messages")
            html = resp1.get_data(as_text=True)
            self.assertIn("Rock Cakes", html)
            self.assertIn("0 user(s) found it useful", html)  ##1 user like it
            self.assertEqual(resp1.status_code, 200)

            
    def test_delete_message(self):
        """Test delete message"""

        with self.client as c:

            user=User.query.filter(User.username=='newuser').first()
            message=user.messages[0]

            testuser=User.query.filter(User.username=='testuser').first()

            meal=Meal.query.filter(Meal.meal_name=='Rock Cakes').first()


            with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.new_user.id

            resp=c.get(f"/users/{user.id}/messages")
            html = resp.get_data(as_text=True)
            self.assertIn("Rock Cakes", html)
            self.assertEqual(resp.status_code, 200)

            #after we delete it the user shouldn't be able to see it on his page
            resp1=c.post(f'/messages/{message.id}/delete')

            resp2=c.get(f"/users/{user.id}/messages")
            html = resp2.get_data(as_text=True)
            self.assertNotIn("Rock Cakes", html)
            self.assertEqual(resp2.status_code, 200)

            #also, we shouldn't see any reviews on rock cakes on check-reviews page

            ####There shouldn't be any review about Carrot Cake
            resp1=c.get(f'/meals/{meal.id}/reviews')
            html = resp1.get_data(as_text=True)
            self.assertIn("Rock Cakes", html)
            self.assertIn("No reviews found", html)
            self.assertEqual(resp1.status_code, 200)