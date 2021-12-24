# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, Cuisine, Category,Message,Meal,User,MealLiked,RestaurantMealLiked,Like

from sqlalchemy.exc import IntegrityError

from csv import DictReader

from secrets import api_key


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///food-roulette-test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()



class MessageModelTestCase(TestCase):
    """Test Message model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        MealLiked.query.delete()
        RestaurantMealLiked.query.delete()
        Cuisine.query.delete()
        Meal.query.delete()
        Category.query.delete()
        RestaurantMealLiked.query.delete()

        with open('generator/cuisines.csv') as cuisines:
            db.session.bulk_insert_mappings(Cuisine, DictReader(cuisines))

        with open('generator/categories.csv') as categories:
            db.session.bulk_insert_mappings(Category, DictReader(categories))

        with open('generator/meals.csv') as meals:
            db.session.bulk_insert_mappings(Meal, DictReader(meals))


        user1 = User(
            email="test1@test1.com",
            username="testuser1",
            password="HASHED_PASSWORD1",
            location="Philadelphia"
        )

        db.session.add(user1)
        db.session.commit()

        self.client = app.test_client()

    def test_Message_model(self):
        """Does basic model work?"""

        user=User.query.filter(User.username=='testuser1').first()
        meal=Meal.query.filter(Meal.id==1).first()
        
        meal_liked=MealLiked(user_id=user.id,meal_id=meal.id)

        db.session.add(meal_liked)
        db.session.commit()

        #Initialy user and meal_liked shouldn't have any messages
        self.assertEqual(len(user.messages),0)

        self.assertEqual(len(meal_liked.messages),0)


        restaurant_meal=RestaurantMealLiked(restaurant_name='restaurant_name',
                                                    restaurant_yelp_id='yelp_id',
                                                    meals_liked_id=meal_liked.id,
                                                    restaurant_address='address',
                                                    restaurant_rating=4.6,
                                                    restaurant_url='restaurant_url',
                                                    restaurant_photo='photo',
                                                    user_id=user.id
                )

        db.session.add(restaurant_meal)
        db.session.commit()

        
        msg = Message(text="something something",user_id=user.id,restaurant_info=restaurant_meal.restaurant_yelp_id,meals_liked_id=meal_liked.id)
        db.session.add(msg)
        db.session.commit()

        #User and meal_liked should have one message
        self.assertEqual(len(user.messages),1)
        self.assertEqual(len(meal_liked.messages),1)



        #message doesn't have likes when it is created
        self.assertEqual(len(msg.user_likes),0)

        user2 = User(
            email="test2@test2.com",
            username="tester2",
            password="HASHED_PASSWORD1",
            location="Philadelphia"
        )
        
        #message should have 1 like

        user2.likes.append(msg)
        db.session.commit()

        self.assertEqual(len(msg.user_likes),1)
        self.assertEqual(len(user2.likes),1)


        #user_id and message_id are unique pairs
        like=Like(user_id=user2.id,message_id=msg.id)
        try:
            db.session.add(like)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        self.assertIsNone(like.id)