"""SQLAlchemy models for Food Roulette."""


from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """
    db.app = app
    db.init_app(app)

class Cuisine(db.Model):

    __tablename__="cuisines"

    cuisine_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    cuisine_name=db.Column(db.Text,nullable=False,unique=True)
    cuisine_image=db.Column(db.Text,nullable=False)

    def __repr__(self):
        return f"<Cuisine #{self.cuisine_id}, {self.cuisine_name}>"

    #one to many relationship
    meals=db.relationship("Meal",backref="cuisine",passive_deletes=True)

class Category(db.Model):

    __tablename__="categories"

    category_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    category_name=db.Column(db.Text,nullable=False,unique=True)
    category_image=db.Column(db.Text,nullable=False)


    def __repr__(self):
        return f"<Category #{self.category_id}, {self.category_name}>"
    
    #one to many relationship
    meals=db.relationship("Meal",backref="category",passive_deletes=True)


class Meal(db.Model):

    __tablename__="meals"

    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    meal_name=db.Column(db.Text,nullable=False,unique=True)
    cuisine_id=db.Column(db.Integer,db.ForeignKey("cuisines.cuisine_id",ondelete="cascade"),nullable=False)
    category_id=db.Column(db.Integer,db.ForeignKey("categories.category_id",ondelete="cascade"),nullable=False)
    image_url=db.Column(db.Text)

    def __repr__(self):
        return f"<Meal #{self.id}, {self.meal_name}, {self.cuisine_id}, {self.category_id}>"

    meals_liked=db.relationship("MealLiked",backref="meal",passive_deletes=True)


class MealLiked(db.Model):

    __tablename__='meals_liked'

    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    meal_id=db.Column(db.Integer,db.ForeignKey("meals.id",ondelete="cascade"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="cascade"),nullable=False)
    is_active=db.Column(db.Boolean,nullable=False,default=True)

    __table_args__ = (db.UniqueConstraint('meal_id', 'user_id'),)

    def __repr__(self):
        return f"<MealLiked #{self.id}, {self.meal_id}, {self.user_id}>"
    
    restaurants=db.relationship("RestaurantMealLiked",backref="meal_liked",passive_deletes=True)

    messages=db.relationship("Message",backref="meal_liked",passive_deletes=True)



class RestaurantMealLiked(db.Model):

    __tablename__='restaurants_meals_liked'

    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    restaurant_name=db.Column(db.Text,nullable=False)
    restaurant_yelp_id=db.Column(db.Text,nullable=False)
    restaurant_address=db.Column(db.Text,nullable=False)
    restaurant_rating=db.Column(db.Float)
    restaurant_url=db.Column(db.Text,nullable=False)
    restaurant_photo=db.Column(db.Text,default="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAM8AAADPCAMAAABlX3VtAAAAMFBMVEX19fXDvrjQzMfc2tfp5+bGwbzy8vHs6+rMyMPW08/JxcDv7u3i4N7Tz8vf3drZ1tPsNjAMAAAD8UlEQVR4nO2c25KrIBBFIwpGvP3/354RAcPVGBv1VO31ZjkqS5sWaTKvFwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMCDqCsa3u3dJgv9m0jnj+lumder4XQ6VTWKm3VmSps/5K0x1+pYY/V5Zv2g6/t0BtIm2JtzU8yJbr0+b556wkO0kr4Lm+Qy053yWybdgWlTrEn+7570tLuIsVQ6mu+IORMXJV4X5tzddWlBD3D4UOTsgumYu+hVVP56Ze+Xh81BBeOhKZA7E1zTX8vlG5fr8mmZ94EH7QAnT/nhz8XjkdKXu368WDQcTEBfOZ63t5C8u5qEU0l2KVWhmNOxfB/ET4jtX7EsxA/odp8Cz4df23UsavBDq6N8GPE5v6WGzy7woQM++8CHDvjsAx+F6EjLQxqCmaUffahKkR78Lp9Sw1j4EPo8cbR9xuf0xR1osh187GHwyQKfGPCxh8EnC3xipHzE0K1jgG6IlR1yPoKlSxVdek1FSZ/emdYewznZnM8yw9/Fd6laRqIaXM5HBIvFgjUDOZ9MCKs2JwozxXzayMJEv36b81kGlu9Mmy/2ac2Xp2R1PRo33gaHJUoDoko3TLV5jO8by/iIVYfPeuK/r3lEiKVvdFOlXVW3THyE8vRjPUDgsz6Q8aOMoUt4UniHVTJ6xjWVRBOCvldRV3Ubzq8n832mWGuGyr8YSzas1wEaq+voWYdosshE8BE8n/UOBjd38pvIwkemMfXYSC/pTc+MNHtKP/BDeD7qtJEoHj1NPX8QRpWplsdeMzZv8mBeak1CBOuUPB+ZuH2915HNfIgvtEamjAmJj3e0P9G26pzPBr5PmwzvzhW18zvuSqn1RfzuZdDhvOX2bp1er6+gWKPk+qTHIyr91M5humW1NRqkiSb9DpP2VCbrb4y29Q1LBehpH5WA4hVn98mpJugm8nFqmmYyM8Cqc5iXMu+WfbUzXWfi7j0Py2F6SRyNjueTGca8wz+M/mJD9/U2Nr/NVDzGJ4uJ1iyGPomhZEw8HLhuXwqCBftqM0YzyxQ3yNZ4nvLZYl8jP7t54z6+rt/GnMLtTpJuQelJn7+ePptmy85P9K3dxybVK7cxtBhGnjrsVp+FZiHxSbrsshnG/SYoX8/60edr4HMU+Ngt+MDnMPCxW/CBz2HgY7fgA5/DwMduwQc+h4GP3YLPw32aw3SP9vkR+JT3OfGzyK0q9iCfaPngO7a56gf5vMTxZLDyUV16kg8F8NkHPnTAZx/40AGffZZmSvu/9KSz5ZDZ9Ss/fnTs+twKfLKM+1f8r3xODJRJuORfjQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACk+QdvISUvRNWLXgAAAABJRU5ErkJggg==")
    meals_liked_id=db.Column(db.Integer,db.ForeignKey("meals_liked.id",ondelete="cascade"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="cascade"),nullable=False)
    is_active=db.Column(db.Boolean,nullable=False,default=True)

    
    __table_args__ = (db.UniqueConstraint('meals_liked_id', 'restaurant_yelp_id'),)



    def __repr__(self):
        p=self
        return f"<RestaurantMealLiked #{p.id}, {p.restaurant_name}, {p.restaurant_yelp_id}, {p.meals_liked_id}>"


class Message(db.Model):
    
    __tablename__='messages'

    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="cascade"),nullable=False)
    text=db.Column(db.Text,nullable=False)
    meals_liked_id=db.Column(db.Integer,db.ForeignKey("meals_liked.id",ondelete="cascade"), nullable=False)
    restaurant_info=db.Column(db.Text,nullable=False)
    timestamp = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())

    def __repr__(self):
        p=self
        return f"<Message #{p.id}, {p.user_id}, {p.text}, {p.meals_liked_id}>"


class Like(db.Model):
    """Mapping user likes to messages."""

    __tablename__ = 'likes' 

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
    )

    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='cascade'),
    )

    __table_args__ = (db.UniqueConstraint('user_id', 'message_id'),)

    def __repr__(self):
        p=self
        return f"<Like #{p.id}, {p.user_id}, {p.message_id}>"

    

class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )

    location = db.Column(
        db.Text, nullable=False
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    meals_liked=db.relationship("MealLiked",backref="user",passive_deletes=True)

    meals_liked_list=db.relationship("Meal",secondary="meals_liked",backref='users_liked',passive_deletes=True)

    messages=db.relationship("Message",backref="user",passive_deletes=True)


    restaurants_meals_liked=db.relationship("RestaurantMealLiked",backref="users",passive_deletes=True)

    likes = db.relationship(
        'Message',
        secondary="likes",backref="user_likes",passive_deletes=True
    )

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password, location, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            location=location,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False