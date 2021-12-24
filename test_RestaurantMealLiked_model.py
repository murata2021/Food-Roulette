# run these tests like:
#
#    python -m unittest test_RestaurantMealLiked_model.py


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



class RestaurantMealLikedModelTestCase(TestCase):
    """Test RestaurantMealLiked model."""

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

    def test_RestaurantMealLiked_model(self):
        """Does basic model work?"""

        user=User.query.filter(User.username=='testuser1').first()
        meal=Meal.query.filter(Meal.id==1).first()
        
        meal_liked=MealLiked(user_id=user.id,meal_id=meal.id)

        db.session.add(meal_liked)
        db.session.commit()

        # MealLiked model should have correct meal id and user id
        self.assertEqual(len(meal_liked.restaurants),0)
        
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

        self.assertEqual(len(meal_liked.restaurants),1)


        #meals_liked_id and restaurant_yelp_id must be unique pairs
        restaurant_meal2=RestaurantMealLiked(restaurant_name='somethingBurger',
                                                    restaurant_yelp_id='yelp_id',
                                                    meals_liked_id=meal_liked.id,
                                                    restaurant_address='address21312312',
                                                    restaurant_rating=2.3,
                                                    restaurant_url='url',
                                                    restaurant_photo='photo',
                                                    user_id=user.id
                )
        try:
            db.session.add(restaurant_meal2)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        self.assertIsNone(restaurant_meal2.id)

        #this must work since unique pair of meals_liked_id and restaurant_yelp_id is provided
        restaurant_meal3=RestaurantMealLiked(restaurant_name='somethingBurger',
                                                    restaurant_yelp_id='yelp_id1231321313',
                                                    meals_liked_id=meal_liked.id,
                                                    restaurant_address='address21312312',
                                                    restaurant_rating=2.3,
                                                    restaurant_url='url',
                                                    restaurant_photo='photo',
                                                    user_id=user.id
                )

        try:
            db.session.add(restaurant_meal3)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        self.assertIsNotNone(restaurant_meal3.id)
        self.assertEqual(len(meal_liked.restaurants),2)

        