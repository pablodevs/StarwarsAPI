"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, Fav_planet, Fav_character
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False # url/endpoint == url/endpoint/
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

##### USERS #####
# All users
@app.route('/user', methods=['GET', 'POST'])
def handle_users():
    """
    All Users
    """
    # GET all users
    if request.method == 'GET':
        users = User.query.all()
        all_users = list(map(lambda x: x.serialize(), users))
        return jsonify(all_users), 200

    # Create (POST) a new user
    if request.method == 'POST':
        user_to_add = request.json

        # Data validation
        if user_to_add is None:
            raise APIException("You need to specify the request body as a json object", status_code=400)
        if 'user_name' not in user_to_add:
            raise APIException('You need to specify the username', status_code=400)
        if 'email' not in user_to_add:
            raise APIException('You need to specify the email', status_code=400)
        if 'password' not in user_to_add:
            raise APIException('You need to create a valid password', status_code=400)

        new_user = User(user_name=user_to_add["user_name"], email=user_to_add["email"], password=user_to_add["password"])
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.serialize()), 200

    return "Invalid Method", 404

# Get, Edit or delete a specific user
@app.route('/user/<int:user_id>', methods=['PUT', 'GET', 'DELETE'])
def handle_single_user(user_id):
    """
    Single user
    """
    user = User.query.get(user_id)

    # Data validation
    if user is None:
        raise APIException('User not found in data base', status_code=404)
        
    # Modify (PUT) a user
    if request.method == 'PUT':
        request_body = request.json

        if "user_name" in request_body:
            user.user_name = request_body["user_name"]
        if "email" in request_body:
            user.email = request_body["email"]
        if "password" in request_body:
            user.password = request_body["password"]
        if "is_active" in request_body:
            user.is_active = request_body["is_active"]

        db.session.commit()
        return jsonify(user.serialize()), 200

    # GET a user
    elif request.method == 'GET':
        return jsonify(user.serialize()), 200
    
    # DELETE a user
    elif request.method == 'DELETE':
        user_planet_list = Fav_planet.query.filter_by(user_id=user_id).first()
        db.session.delete(user_planet_list)
        db.session.delete(user)
        db.session.commit()
        return "User deleted", 200

    return "Invalid Method", 404

##### FAVORITES #####
@app.route('/user/<int:user_id>/favorites', methods=['GET'])
def get_favs(user_id):
    if request.method is not 'GET': return "Invalid Method", 404

    fav_planets = Fav_planet.query.filter_by(user_id=user_id)
    fav_characters = Fav_character.query.filter_by(user_id=user_id)

    all_favs = list(map(lambda x: x.serialize(), fav_planets))
    all_favs = all_favs + list(map(lambda x: x.serialize(), fav_characters))
    return jsonify(all_favs), 200

##### ADD FAVORITE #####
# (PUT)Add item_id to the favorites list of user_id
@app.route('/user/<int:user_id>/<category>/<int:item_id>', methods=['POST', 'DELETE'])
def handle_fav(user_id, category, item_id):
    """
    Add Fav (Planet or Character)
    """
    user = User.query.get(user_id)
    # Data validation
    if user is None:
        raise APIException('User not found in data base', status_code=404)

    if request.method == 'POST':
        if category == "planet":
            planet = Planet.query.get(item_id)
            # Data validation
            if planet is None:
                raise APIException('Planet not found in data base', status_code=404)

            fav_planet = Fav_planet.query.filter_by(user_id=user.id, planet_id=item_id).first()
            if fav_planet is None:
                fav = Fav_planet(user_id=user.id, planet_id=planet.id)
            else: raise APIException('Fav already exists', status_code=404)

        if category == "character":
            character = Character.query.get(item_id)
            # Data validation
            if character is None:
                raise APIException('Character not found in data base', status_code=404)

            fav_character = Fav_character.query.filter_by(user_id=user.id, character_id=item_id).first()
            if fav_character is None:
                fav = Fav_character(user_id=user.id, character_id=character.id)
            else: raise APIException('Fav already exists', status_code=404)

        db.session.add(fav)
        db.session.commit()
        return jsonify(fav.serialize()), 200

    elif request.method == 'DELETE':
        if category == "planet":
            fav = Fav_planet.query.filter_by(user_id=user.id, planet_id=item_id).first()
            # Data validation
            if fav is None:
                raise APIException('Planet not found in data base', status_code=404)

        if category == "character":
            fav = Fav_character.query.filter_by(user_id=user.id, character_id=item_id).first()
            # Data validation
            if fav is None:
                raise APIException('Character not found in data base', status_code=404)

        db.session.delete(fav)
        db.session.commit()
        return "Deleted successfully", 200

    return "Invalid Method", 404

##### PLANETS #####
# GET all planets
@app.route('/planet', methods=['GET', 'POST'])
def handle_planets():
    """
    All Planets
    """
    # GET all planets
    if request.method == 'GET':
        planets = Planet.query.all()
        all_planets = list(map(lambda p: p.serialize(), planets))
        return jsonify(all_planets), 200

    # Create (POST) a new planet
    if request.method == 'POST':
        planet_to_add = request.json

        # Data validation
        if planet_to_add is None:
            raise APIException("You need to specify the request body as a json object", status_code=400)
        if 'name' not in planet_to_add:
            raise APIException('You need to specify the name', status_code=400)
        if 'img_url' not in planet_to_add:
            url = None
        else: url = planet_to_add["img_url"]

        new_planet = Planet(name=planet_to_add["name"], img_url=url)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(new_planet.serialize()), 200
    
    return "Invalid Method", 404

# Get, Edit or delete a specific planet
@app.route('/planet/<int:planet_id>', methods=['PUT', 'GET', 'DELETE'])
def handle_single_planet(planet_id):
    """
    Single planet
    """
    planet = Planet.query.get(planet_id)

    # Data validation
    if planet is None:
        raise APIException('Planet not found', status_code=404)

    # Modify (PUT) a planet
    if request.method == 'PUT':
        request_body = request.json

        if "name" in request_body:
            planet.name = request_body["name"]
        if "img_url" in request_body:
            planet.img_url = request_body["img_url"]

        db.session.commit()
        return jsonify(planet.serialize()), 200
    
    # GET a planet
    elif request.method == 'GET':
        return jsonify(planet.serialize()), 200

    # DELETE a planet
    elif request.method == 'DELETE':
        db.session.delete(planet)
        db.session.commit()
        return "Planet deleted", 200

    return "Invalid Method", 404

##### CHARACTERS #####
# GET all characters
@app.route('/character', methods=['GET', 'POST'])
def handle_characters():
    """
    All Characters
    """
    # GET all characters
    if request.method == 'GET':
        characters = Character.query.all()
        all_characters = list(map(lambda p: p.serialize(), characters))
        return jsonify(all_characters), 200

    # Create (POST) a new character
    if request.method == 'POST':
        character_to_add = request.json

        # Data validation
        if character_to_add is None:
            raise APIException("You need to specify the request body as a json object", status_code=400)
        if 'name' not in character_to_add:
            raise APIException('You need to specify the name', status_code=400)
        if 'img_url' not in character_to_add:
            url = None
        else: url = character_to_add["img_url"]

        new_character = Character(name=character_to_add["name"], img_url=url)
        db.session.add(new_character)
        db.session.commit()
        return jsonify(new_character.serialize()), 200
    
    return "Invalid Method", 404

# Get, Edit or delete a specific character
@app.route('/character/<int:character_id>', methods=['PUT', 'GET', 'DELETE'])
def handle_single_character(character_id):
    """
    Single character
    """
    character = Character.query.get(character_id)

    # Data validation
    if character is None:
        raise APIException('Character not found', status_code=404)

    # Modify (PUT) a character
    if request.method == 'PUT':
        request_body = request.json

        if "name" in request_body:
            character.name = request_body["name"]
        if "img_url" in request_body:
            character.img_url = request_body["img_url"]

        db.session.commit()
        return jsonify(character.serialize()), 200
    
    # GET a character
    elif request.method == 'GET':
        return jsonify(character.serialize()), 200

    # DELETE a character
    elif request.method == 'DELETE':
        db.session.delete(character)
        db.session.commit()
        return "Character deleted", 200

    return "Invalid Method", 404

##### LAST LINES OF CODE #####
# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)