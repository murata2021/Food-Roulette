import csv
import requests
import pandas as pd

import string

CUISINES_CSV_HEADERS = ['cuisine_id','cuisine_name']
CATEGORIES_CSV_HEADERS = ['category_id','category_name']


cuisines=requests.get(f" http://www.themealdb.com/api/json/v1/1/list.php?a=list?")
categories=requests.get(f" http://www.themealdb.com/api/json/v1/1/list.php?c=list?")



with open('cuisines.csv', 'w') as cuisines_csv:
    cuisines_writer = csv.DictWriter(cuisines_csv, fieldnames=CUISINES_CSV_HEADERS)
    cuisines_writer.writeheader()

    idx=1
    for cuisine in cuisines.json()["meals"]:

        cuisines_writer.writerow(dict(
            cuisine_id=idx,
            cuisine_name=cuisine['strArea']
        ))

        idx+=1


with open('categories.csv', 'w') as categories_csv:
    categories_writer = csv.DictWriter(categories_csv, fieldnames=CATEGORIES_CSV_HEADERS)
    categories_writer.writeheader()

    idx=1
    for category in categories.json()["meals"]:

        categories_writer.writerow(dict(
            category_id=idx,
            category_name=category['strCategory']
        ))
        idx+=1

MEALS_CSV_HEADERS=["meal_name","cuisine_name","category_name","image_url"]
with open("meals.csv","w") as meals_csv:
    meals_writer=csv.DictWriter(meals_csv,fieldnames=MEALS_CSV_HEADERS)
    meals_writer.writeheader()

    # for first_letter in string.ascii_lowercase:
    for first_letter in string.ascii_lowercase:

        meals=requests.get(f"http://www.themealdb.com/api/json/v1/1/search.php?f={first_letter}")
        try:
            for meal in meals.json()["meals"]:
                meals_writer.writerow(dict(
                    meal_name=meal["strMeal"],
                    cuisine_name=meal["strArea"],
                    category_name=meal["strCategory"],
                    image_url=meal["strMealThumb"]
                ))
        except TypeError:
            pass



df1 = pd.read_csv('meals.csv')
df2=pd.read_csv('categories.csv')
inner_join = pd.merge(df1,df2,on ='category_name',how ='inner')

df3=pd.read_csv('cuisines.csv')
result=pd.merge(inner_join,df3,on="cuisine_name",how="inner")

result.to_csv("meals.csv",index=False,columns=["meal_name","cuisine_id","category_id","image_url"])
