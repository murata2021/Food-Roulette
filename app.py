import os

from flask import Flask, render_template, request, flash, redirect, session, g,url_for,jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

import requests
import json
from random import choice

from forms import UserAddForm, LoginForm, MessageForm, EditUserForm
from models import db, connect_db, Cuisine, Category,Message,Meal,User,MealLiked,RestaurantMealLiked,Like
from secrets import api_key


headers = {'Authorization': 'Bearer %s' % api_key}

yelp_url='https://api.yelp.com/v3/businesses/search'

# In the dictionary, term can take values like food, cafes or businesses like McDonalds
# params = {'term':'seafood','location':'New York City'}


CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///food-roulette-db').replace("postgres://", "postgresql://", 1))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)

##############################################################################
# User signup/login/logout


#Before any request it works
@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if not g.user:
    
        form = UserAddForm()

        if form.validate_on_submit():
            temp_username=form.username.data
            temp_email=form.email.data
            try:
                user = User.signup(
                    username=form.username.data,
                    password=form.password.data,
                    email=form.email.data,
                    location=form.location.data,
                    image_url=form.image_url.data or User.image_url.default.arg,
                )
                
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                if User.query.filter(User.username==form.username.data).all(): 
                    flash("Username already taken", 'danger')
                if User.query.filter(User.email==form.email.data).all(): 
                    flash("This email address already signed up", 'danger')
                
                return render_template('users/signup.html', form=form)

            do_login(user)

            return redirect("/")

        else:
            return render_template('users/signup.html', form=form)
    else:
        return redirect("/")


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""
    if not g.user:
        form = LoginForm()

        if form.validate_on_submit():
            user = User.authenticate(form.username.data,
                                    form.password.data)

            if user:
                do_login(user)
                flash(f"Hello, {user.username}!", "success")
                return redirect("/")

            flash("Invalid credentials.", 'danger')

        return render_template('users/login.html', form=form)
    else:
        return redirect("/")

@app.route('/logout')
def logout():
    """Handle logout of user."""

    if g.user:
        do_logout()
        flash(f"Goodbye {g.user.username}!", 'success')
        return redirect("/")
    else:
        return redirect("/")


##############################################################################

####search bar
@app.route('/meals')
def list_meals():
    """Page with listing of meals.

    Can take a 'q' param in querystring to search by that meal.
    """
    search = request.args.get('q')

    if not search:
        meals = Meal.query.all()
    else:
        meals = Meal.query.filter(Meal.meal_name.ilike(f"%{search.strip()}%")).all()
    
    return render_template('meals/list_meals.html', meals=meals,search=search)

@app.route('/meals/<int:meal_id>')
def show_meal(meal_id):
    """Show single meal"""
    
    meal=Meal.query.get_or_404(meal_id)

    
    ingredientKeys=["strIngredient"+str(i) for i in range(1,21)]

    detailed_meal_info=requests.get("http://www.themealdb.com/api/json/v1/1/search.php",params={"s":meal.meal_name}).json()
    
    ingredientList=[]
    for i in ingredientKeys:
        detailed_meal_info["meals"][0].get(i)
        if detailed_meal_info["meals"][0].get(i):
            ingredientList.append(detailed_meal_info["meals"][0].get(i))

    if not g.user:
        return render_template('meals/single_meal.html', meal=meal,ingredients=ingredientList)
    else:

        user_liked_meal=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==meal.id).first()
        return render_template('meals/single_meal.html', meal=meal,ingredients=ingredientList,user_liked_meal=user_liked_meal)

@app.route('/meals/<int:meal_id>/reviews')
def check_reviews(meal_id):
    """Show reviews of a meal"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        meal=Meal.query.get_or_404(meal_id)

        meals_liked_ids=[i[0] for i in MealLiked.query.with_entities(MealLiked.id).filter(MealLiked.meal_id==meal_id).all()]

        messages=Message.query.filter(Message.meals_liked_id.in_(meals_liked_ids)).all()
        

        a=RestaurantMealLiked.query.with_entities(RestaurantMealLiked.restaurant_yelp_id,RestaurantMealLiked.restaurant_name).all()

        d={yelp:name for yelp,name in a}

        return render_template('meals/check_reviews.html',messages=messages, meal=meal,d=d)

@app.route("/cuisines")
def show_cuisines():
    """Shows cuisine list."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:
        cuisines=Cuisine.query.all()

        return render_template("cuisines/cuisines.html",cuisines=cuisines)

@app.route("/cuisines/<int:cuisine_id>")
def show_cuisine(cuisine_id):
    """Shows random meal from selected cuisine"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:
        cuisine=Cuisine.query.filter(Cuisine.cuisine_id==cuisine_id).first().cuisine_name
        
        ### meal database request
        meal_list=requests.get("http://www.themealdb.com/api/json/v1/1/filter.php",params={"a":cuisine})
        random_meal=choice(meal_list.json()["meals"])
        #meal_object
        meal_object=Meal.query.filter(Meal.meal_name==random_meal["strMeal"]).first()

        ####it is going to be used to check soft deletes: user_liked_meal.is_active
        user_liked_meal=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==meal_object.id).first()
        
        ingredientKeys=["strIngredient"+str(i) for i in range(1,21)]

        detailed_meal_info=requests.get("http://www.themealdb.com/api/json/v1/1/lookup.php",params={"i":random_meal["idMeal"]}).json()
        ingredientList=[]
        for i in ingredientKeys:
            detailed_meal_info["meals"][0].get(i)
            if detailed_meal_info["meals"][0].get(i):
                ingredientList.append(detailed_meal_info["meals"][0].get(i))

        ##### meal=random_meal for meal photo
        return render_template("cuisines/random_meal_by_cuisine.html",user_liked_meal=user_liked_meal,ingredients=ingredientList,meal=random_meal,id=cuisine_id,meal_object=meal_object)


@app.route("/categories")
def show_categories():
    """Shows category list."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        categories=Category.query.all()

        return render_template("categories/categories.html",categories=categories)


@app.route("/categories/<int:category_id>")
def show_category(category_id):
    """Shows random meal from selected category"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        category=Category.query.filter(Category.category_id==category_id).first().category_name

        meal_list=requests.get("http://www.themealdb.com/api/json/v1/1/filter.php",params={"c":category})
        random_meal=choice(meal_list.json()["meals"])

        meal_object=Meal.query.filter(Meal.meal_name==random_meal["strMeal"]).first()

        ####it is going to be used to check soft deletes: user_liked_meal.is_active
        user_liked_meal=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==meal_object.id).first()

        ingredientKeys=["strIngredient"+str(i) for i in range(1,21)]

        detailed_meal_info=requests.get("http://www.themealdb.com/api/json/v1/1/lookup.php",params={"i":random_meal["idMeal"]}).json()
        ingredientList=[]
        for i in ingredientKeys:
            detailed_meal_info["meals"][0].get(i)
            if detailed_meal_info["meals"][0].get(i):
                ingredientList.append(detailed_meal_info["meals"][0].get(i))
        
        ##### meal=random_meal for meal photo
        return render_template("categories/random_meal_by_category.html",user_liked_meal=user_liked_meal,ingredients=ingredientList,meal=random_meal,id=category_id,meal_object=meal_object)

@app.route("/surprise-me")
def show_surprise_meal():
    """Show random meal from all meals"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        random_meal=requests.get("http://www.themealdb.com/api/json/v1/1/random.php")
        meal=random_meal.json()["meals"][0]
        meal_object=Meal.query.filter(Meal.meal_name==meal["strMeal"]).first()

        ####it is going to be used to check soft deletes: user_liked_meal.is_active
        user_liked_meal=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==meal_object.id).first()

        ingredientKeys=["strIngredient"+str(i) for i in range(1,21)]

        detailed_meal_info=requests.get("http://www.themealdb.com/api/json/v1/1/lookup.php",params={"i":meal["idMeal"]}).json()
        ingredientList=[]
        for i in ingredientKeys:
            detailed_meal_info["meals"][0].get(i)
            if detailed_meal_info["meals"][0].get(i):
                ingredientList.append(detailed_meal_info["meals"][0].get(i))

        return render_template("surprise_me.html",user_liked_meal=user_liked_meal,ingredients=ingredientList,meal=meal,meal_object=meal_object)

@app.route("/like-it/<meal_name>",methods=["POST"])
def show_like_it(meal_name):
    """Like meal"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        address=request.form["address"] or g.user.location

        liked_meal=Meal.query.filter(Meal.meal_name==meal_name).first()

        #Checks for soft deleted entries
        checks_soft_deleted_meal_liked=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==liked_meal.id,MealLiked.is_active==False).first()
        ##if the meal in the database but it is inactive, this block is going to change its status
        if checks_soft_deleted_meal_liked:
            checks_soft_deleted_meal_liked.is_active=True
            
        ##else meal going to be added to meals_liked table
        else:
            g.user.meals_liked_list.append(liked_meal)
        db.session.commit()
        
        return redirect(url_for("show_restaurants_new_meal",meal_name=liked_meal.meal_name,address=address))

@app.route("/like-it/<meal_name>/restaurants/<address>")
def show_restaurants_new_meal(meal_name,address):
    """Show restaurant list based on the selected meal and the address"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:


        liked_meal=Meal.query.filter(Meal.meal_name==meal_name).first()
        restaurants=requests.get(yelp_url,headers=headers,params={"location":address,"term":meal_name}).json()
    

        meal_liked=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==liked_meal.id).first()

        restaurant_objects=RestaurantMealLiked.query.filter(RestaurantMealLiked.user_id==g.user.id,RestaurantMealLiked.meals_liked_id==meal_liked.id).all()
        restaurants_yelp=[r.restaurant_yelp_id  for r in restaurant_objects]


        soft_deleted_restaurants=[restaurant.restaurant_yelp_id for restaurant in restaurant_objects if restaurant.is_active==False]
        
        
        return render_template("show_restaurants.html",restaurant_objects=restaurant_objects,soft_deleted_restaurants=soft_deleted_restaurants,typed_address=address,restaurants=restaurants["businesses"],liked_meal=meal_liked,restaurants_yelp=restaurants_yelp)


@app.route("/show-it/<meal_name>/restaurants")
def show_restaurants_existing_meal(meal_name):
    """Show restaurant list if the meal is already liked"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        address=request.args["address"] or g.user.location
        
        liked_meal=Meal.query.filter(Meal.meal_name==meal_name).first()
        restaurants=requests.get(yelp_url,headers=headers,params={"location":address,"term":meal_name}).json()
        
        meal_liked=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==liked_meal.id).first()

        restaurant_objects=RestaurantMealLiked.query.filter(RestaurantMealLiked.user_id==g.user.id,RestaurantMealLiked.meals_liked_id==meal_liked.id).all()
        restaurants_yelp=[r.restaurant_yelp_id  for r in restaurant_objects]

        soft_deleted_restaurants=[restaurant.restaurant_yelp_id for restaurant in restaurant_objects if restaurant.is_active==False]


        return render_template("show_restaurants.html",soft_deleted_restaurants=soft_deleted_restaurants,typed_address=address,restaurants=restaurants["businesses"],liked_meal=meal_liked,restaurants_yelp=restaurants_yelp)


#####################################################################33#######
#Restaurant
@app.route("/restaurant/like-it",methods=["POST"])
def like_restaurant():
    """Like restaurant_meal"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

   
        restaurant_name=request.form["restaurant_name"]
        yelp_id=request.form["yelp_id"]
        meals_liked_id=int(request.form["meals_liked_id"])
        address=",".join(request.form['restaurant_address'])
        rating=float(request.form["rating"])
        restaurant_url=request.form["restaurant_url"]
        photo=request.form["photo"]


        checks_soft_deleted_restaurant_liked=RestaurantMealLiked.query.filter(RestaurantMealLiked.user_id==g.user.id,
                                                                            RestaurantMealLiked.restaurant_yelp_id==yelp_id,
                                                                            RestaurantMealLiked.meals_liked_id==meals_liked_id,
                                                                            RestaurantMealLiked.is_active==False).first()
        if checks_soft_deleted_restaurant_liked:
            checks_soft_deleted_restaurant_liked.is_active=True
            db.session.commit()
        else:
            try:

                restaurant_meal=RestaurantMealLiked(restaurant_name=restaurant_name,
                                                    restaurant_yelp_id=yelp_id,
                                                    meals_liked_id=meals_liked_id,
                                                    restaurant_address=address,
                                                    restaurant_rating=rating,
                                                    restaurant_url=restaurant_url,
                                                    restaurant_photo=photo,
                                                    user_id=g.user.id
                )

                db.session.add(restaurant_meal)
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
    
        return redirect(request.referrer)
#************************************************************************************************************************
@app.route("/restaurant/<restaurant_yelp_id>/unlink-restaurant-meal/<int:meal_liked_id>",methods=["POST"])
def unlink_restaurant_meal(restaurant_yelp_id,meal_liked_id):
    """Unlink single meal restaurant relationship"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:
        user_restaurant=RestaurantMealLiked.query.filter(RestaurantMealLiked.restaurant_yelp_id==restaurant_yelp_id
        ,RestaurantMealLiked.user_id==g.user.id
        ,RestaurantMealLiked.meals_liked_id==meal_liked_id).all()
            
        for entry in user_restaurant:
            entry.is_active=False
        db.session.commit()

        return redirect(request.referrer)

#************************************************************************************************************************
@app.route("/restaurant/remove-it/<restaurant_yelp_id>",methods=["POST"])
def remove_restaurant(restaurant_yelp_id):
    """complete removal of restaurant (for all meals) from like list, soft-deletes it"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:


        user_restaurant=RestaurantMealLiked.query.filter(RestaurantMealLiked.restaurant_yelp_id==restaurant_yelp_id,RestaurantMealLiked.user_id==g.user.id).all()
        #Soft delete for user like restaurants

        #yelp_id and user_id together are not unique identifiers for this table. Users may get more than one dish at the same restaurant
        #That's why potentially we will have multiple rows in our restaurants_meals_liked table
        for entry in user_restaurant:
            entry.is_active=False
        db.session.commit()

        return redirect(request.referrer)

###################################################################################



@app.route("/meals-liked/remove-it/<meal_id>",methods=["POST"])
def remove_meal_from_fav_list(meal_id):
    """remove meal from the fav list, soft deletes it"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        #Selects the meal to removed
        meal_liked=MealLiked.query.filter(MealLiked.meal_id==meal_id,MealLiked.user_id==g.user.id).first()
        #Soft deletes it
        meal_liked.is_active=False
        
        db.session.commit()

        return redirect(request.referrer)

##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    #unique restaurants by yelp_id
    restaurant_list=db.session.query(RestaurantMealLiked.restaurant_yelp_id,RestaurantMealLiked.restaurant_name).filter(RestaurantMealLiked.user_id==g.user.id).distinct()

    form = MessageForm()
    
    form.meal.choices=[(meal.id,meal.meal_name)for meal in g.user.meals_liked_list]
    form.meal.choices.insert(0,("",""))
    form.restaurant.choices=[(restaurant.restaurant_yelp_id,restaurant.restaurant_name) for restaurant in restaurant_list ]
    form.restaurant.choices.insert(0,("",""))


    if form.validate_on_submit() or request.method=='POST':

        meals_liked_id=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==int(form.meal.data)).first().id

        msg = Message(text=form.text.data,restaurant_info=form.restaurant.data,meals_liked_id=meals_liked_id)
        g.user.messages.append(msg)
        db.session.commit()
        

        return redirect(f"/users/{g.user.id}/messages")

    
    return render_template('messages/new_message.html', form=form)

#####For Dynamic WTF forms
@app.route("/restaurants/<int:meal_id>")
def restaurants_meals(meal_id):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:
    
        meal_liked=MealLiked.query.filter(MealLiked.user_id==g.user.id,MealLiked.meal_id==meal_id).first()

        restaurants=meal_liked.restaurants
        
        restaurantsArray=[]
        
        for restaurant in restaurants:

            restaurantObj={}
            restaurantObj["id"]=restaurant.id
            restaurantObj["name"]=restaurant.restaurant_name
            restaurantObj["meal_liked_id"]=restaurant.meals_liked_id
            restaurantObj["yelp_id"]=restaurant.restaurant_yelp_id

            restaurantsArray.append(restaurantObj)

        return jsonify({"restaurants":restaurantsArray})


@app.route('/users/<int:user_id>/messages', methods=["GET"])
def messages_show(user_id):
    """Show a message."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        user=User.query.get_or_404(user_id)
        messages = Message.query.filter(Message.user_id==user.id).all()

        a=RestaurantMealLiked.query.with_entities(RestaurantMealLiked.restaurant_yelp_id,RestaurantMealLiked.restaurant_name).all()

        d={yelp:name for yelp,name in a}


        total_likes=sum([len(message.user_likes) for message in messages])
        
        return render_template('users/show.html', messages=messages,user=user,d=d,total_likes=total_likes)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/messages")



#####################################################################################
#users

@app.route('/users/profile', methods=["GET", "POST"])
def update_profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user=User.query.get_or_404(g.user.id)
    form=EditUserForm(obj=user)


    if form.validate_on_submit():
        if User.authenticate(user.username,form.password.data):
            #checks new username is unique
                #all users usernames excluding the current user
            all_users_usernames=db.session.query(User.username).filter(User.username!=user.username).all()
            if (form.username.data.strip(),) in all_users_usernames:
                flash("this username already exists!","danger")
                return redirect('/users/profile')

            #checks updated email is unique
                #all users emails excluding the current user
            all_users_emails=db.session.query(User.email).filter(User.email!=user.email).all()
            if (form.email.data,) in all_users_emails:
                flash("this email already exists!","danger")
                return redirect('/users/profile')

            user.username=form.username.data
            user.email = form.email.data
            user.image_url=form.image_url.data
            user.location=form.location.data

            db.session.commit()

            return redirect(f"/users/{g.user.id}")

        else:
            flash("Invalid password!","danger")
            return redirect('/users/profile')

    return render_template('users/edit.html', form=form)

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


@app.route("/users/<int:user_id>")
def show_user(user_id):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:
        user=User.query.get_or_404(user_id)

        
        return render_template("users/user_profile.html",user=user,messages=user.messages)


    #fav lists

@app.route("/users/<int:user_id>/liked-food")
def show_liked_meals(user_id):

    #check meals in the fav list
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        meal_list=[liked_meal.meal for liked_meal in MealLiked.query.filter(MealLiked.user_id==user_id,MealLiked.is_active==True).all()]
        user=User.query.get_or_404(user_id)

        return render_template("users/user_liked_food.html",meals=meal_list,user=user)


@app.route("/users/<int:user_id>/liked-food/<int:meal_id>")
def show_liked_meal_detail(user_id,meal_id):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        meal=Meal.query.get_or_404(meal_id)
        user=User.query.get_or_404(user_id)

        meal_liked=MealLiked.query.filter(MealLiked.user_id==user_id,MealLiked.meal_id==meal_id).first()
        restaurant_list=[restaurant for restaurant in meal_liked.restaurants if restaurant.is_active==True]
        
        return render_template("users/user_liked_food_details.html",restaurants=restaurant_list,meal=meal,user=user,meal_liked=meal_liked)


@app.route("/users/<int:user_id>/liked-restaurants")
def show_liked_restaurants(user_id):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        user=User.query.get_or_404(user_id)


        restaurant_list=db.session.query(RestaurantMealLiked.restaurant_yelp_id,RestaurantMealLiked.restaurant_name,RestaurantMealLiked.restaurant_url,RestaurantMealLiked.restaurant_photo).filter(RestaurantMealLiked.user_id==user_id,RestaurantMealLiked.is_active==True).distinct()
        
        return render_template("users/user_liked_restaurants.html",restaurants=restaurant_list,user=user)


@app.route("/users/<int:user_id>/liked-restaurants/<yelp_id>")
def show_liked_restaurants_details(user_id,yelp_id):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:
        user=User.query.get_or_404(user_id)

        restaurants=RestaurantMealLiked.query.filter(RestaurantMealLiked.user_id==user_id,RestaurantMealLiked.restaurant_yelp_id==yelp_id,RestaurantMealLiked.is_active==True).all()

        if len(restaurants)==0:
            return redirect(f"/users/{user.id}/liked-restaurants")

        else:
            meals_liked=[restaurant.meal_liked for restaurant in restaurants if restaurant.meal_liked.is_active]
            

        
        return render_template("users/liked_restaurant_detailed.html",restaurant=restaurants[0],user=user,restaurants=restaurants,meals_liked=meals_liked)


##############################################################################
# Likes routes:

@app.route("/users/add_like/<int:message_id>",methods=['POST'])
def add_like(message_id):
    """Add & Remove Like"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg=Message.query.get_or_404(message_id)

    if msg.user_id!=g.user.id:
        if g.user in msg.user_likes:
            g.user.likes.remove(msg)
        
        else:
            g.user.likes.append(msg)

        db.session.commit()
    
        
    return redirect(request.referrer)

@app.route("/users/<int:user_id>/liked-messages")
def show_liked_messages(user_id):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:

        user=User.query.get_or_404(user_id)

        messages=user.likes
        a=RestaurantMealLiked.query.with_entities(RestaurantMealLiked.restaurant_yelp_id,RestaurantMealLiked.restaurant_name).all()

        d={yelp:name for yelp,name in a}
        
        return render_template("users/user_liked_messages.html",messages=messages,user=user,d=d)

##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        
        messages=Message.query.all()
        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')

@app.errorhandler(404)
def page_not_found(e):
    """404 page"""
    # note that we set the 404 status explicitly
    return render_template('error_page.html'), 404

##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req