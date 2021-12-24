"""User model tests."""

# run these tests like:
#
#    python -m unittest test_mealLiked_model.py


import os
from unittest import TestCase

from models import db, Cuisine, Category,Message,Meal,User,MealLiked,RestaurantMealLiked,Like

from sqlalchemy.exc import IntegrityError

from csv import DictReader


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



class MealLikedModelTestCase(TestCase):
    """Test MealLiked model."""

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

    def test_mealLiked_model(self):
        """Does basic model work?"""

        user=User.query.filter(User.username=='testuser1').first()
        meal=Meal.query.filter(Meal.id==1).first()
        
        meal_liked=MealLiked(user_id=user.id,meal_id=meal.id)

        db.session.add(meal_liked)
        db.session.commit()

        # MealLiked model should have correct meal id and user id
        self.assertEqual(len(meal_liked.restaurants),0)
        self.assertEqual(len(meal_liked.messages),0)

        self.assertEqual(meal_liked.user_id, user.id)
        self.assertEqual(meal_liked.meal_id, meal.id)

        # The relationship between user,meal and mealLiked must work correctly
        self.assertEqual(len(user.meals_liked),1)
        self.assertEqual(user.meals_liked_list[0],meal)


        #meal_id and user_id must be unique pairs
        meal_liked2=MealLiked(user_id=user.id,meal_id=meal.id)
        try:
            db.session.add(meal_liked2)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        self.assertIsNone(meal_liked2.id)


        

    
