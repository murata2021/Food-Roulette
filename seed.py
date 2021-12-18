from csv import DictReader
from app import db
from models import Cuisine,Category,Meal,User,Message,MealLiked,RestaurantMealLiked


db.drop_all()
db.create_all()

with open('generator/cuisines.csv') as cuisines:
    db.session.bulk_insert_mappings(Cuisine, DictReader(cuisines))

with open('generator/categories.csv') as categories:
    db.session.bulk_insert_mappings(Category, DictReader(categories))

with open('generator/meals.csv') as meals:
    db.session.bulk_insert_mappings(Meal, DictReader(meals))


db.session.commit()
