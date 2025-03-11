from flask import Flask,render_template, request, redirect, flash, session,url_for, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail,Message
from datetime import datetime
from bson.objectid import ObjectId
from authlib.integrations.flask_client import OAuth
from functools import wraps

#from config import Config
app=Flask(__name__)

#Configuration
app.config['MONGO_URI']='mongodb://localhost:27017/Major_Project'
app.config['SECRET_KEY'] = 'db0874988cf36807a8c6e0e0ba2c6f60'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '21it438@bvmengineering.ac.in'
app.config['MAIL_PASSWORD'] = 'Rumit@2003'

# Google OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = '1064395158995-4t434aq68r2ek64fj14mdsncq3o5f2gu.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'

#Initiliaze Extension
mongo=PyMongo(app)
users=mongo.db.Users_Data
car_data=mongo.db.Cars_Data
comp=mongo.db.Comparison_Data
review=mongo.db.Review_Data
mail=Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
oauth = OAuth(app)

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Get current user helper function
def get_current_user():
    if 'user_id' in session:
        return users.find_one({'_id': ObjectId(session['user_id'])})
    return None

# Configure Google OAuth
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

# Index API
@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)

# Login and SignUP API's
# SignUP API
@app.route('/signup',methods=['POST'])
def signup():
    email=request.form.get('email')
    pss=request.form.get('password')
    name=request.form.get('name')

    # Check if user exists
    existing_user = users.find_one({'email':email})
    if existing_user:
        if 'google_id' in existing_user:
            flash('This email is already registered with Google. Please use Google Sign In.', 'error')
        else:
            flash('User already exists! Please login.', 'error')
        return redirect(url_for('signup_page'))
    
    # Create new user
    user_data = {
        'name': name,
        'email': email,
        'password': generate_password_hash(pss),
        'created_at': datetime.utcnow()
    }
    
    users.insert_one(user_data)
    flash('Account created successfully! Please login.', 'success')
    return redirect(url_for('login_page'))

# Login API
@app.route('/login',methods=['POST'])
def login():
    email=request.form.get('email')
    pss=request.form.get('password')
    
    user=users.find_one({'email':email})
    if user:
        # Check if it's a Google user
        if 'google_id' in user:
            flash('Please use Google Sign In for this account', 'error')
            return redirect(url_for('login_page'))
        
        # Regular password check
        if check_password_hash(user['password'], pss):
            session['user_id']=str(user['_id'])
            session['email']=user['email']
            session['name']=user['name']
            session['is_google_user']=False
            
            flash('Login Successful!','success')
            return redirect(url_for('index'))
    
    flash('Invalid Email or Password', 'error')
    return redirect(url_for('login_page'))

# Profile API
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    user = session['user']
    return render_template('profile.html', user=user)

# Forgot_Password API
@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method=='POST':
        email=request.form['email']
        user=users.find_one({'email':email})
        if not user:
            flash('No account found with this email!','error')
            return redirect(url_for('forgot_passoword'))
        
        token=serializer.dumps(email, salt='password-reset-salt')
        print(f"Generated Token: {token}")
        reset_link=url_for('reset_password',token=token, _external=True)
        print(f"Generated Reset Link: {reset_link}")


        try:
            msg = Message("Password Reset Request",
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[email])
            msg.body = f'Hello,\n\nTo reset your password, click the link below:\n\n{reset_link}\n\nIf you did not request this, please ignore this email.'
            mail.send(msg)
            flash('A password reset link has been sent to your email.', 'success')
        except Exception as e:
            flash('An error occurred while sending the email. Please try again later.', 'error')
            print(f"Email error: {e}")
        return redirect(url_for('index'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
        print(f"Token is valid for email: {email}")
    except SignatureExpired:
        print("Token expired.")
        flash('The password reset link has expired.', 'error')
        return redirect(url_for('forgot_password'))
    except BadSignature:
        print("Invalid token signature.")
        flash('The password reset link is invalid.', 'error')
        return redirect(url_for('forgot_password'))
    except Exception as e:
        print(f"Unexpected token error: {e}")
        flash('An error occurred. Please request a new password reset.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_pss = request.form.get('password')
        if len(new_pss) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(request.url)

        hash_pss = generate_password_hash(new_pss)
        users.update_one({'email': email}, {'$set': {'password': hash_pss}})
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('reset_password.html')

# Google Login Routes
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    try:
        token = oauth.google.authorize_access_token()
        resp = oauth.google.get('userinfo')
        user_info = resp.json()
        
        # Check if user exists
        user = users.find_one({'email': user_info['email']})
        
        if not user:
            # Create new user
            user_data = {
                'name': user_info['name'],
                'email': user_info['email'],
                'google_id': user_info['id'],
                'profile_pic': user_info.get('picture'),
                'created_at': datetime.utcnow()
            }
            result = users.insert_one(user_data)
            user_id = str(result.inserted_id)
        else:
            # Update existing user's Google info
            users.update_one(
                {'email': user_info['email']},
                {'$set': {
                    'google_id': user_info['id'],
                    'profile_pic': user_info.get('picture'),
                    'last_login': datetime.utcnow()
                }}
            )
            user_id = str(user['_id'])

        # Set session
        session['user_id'] = user_id
        session['email'] = user_info['email']
        session['name'] = user_info['name']
        session['is_google_user'] = True
        
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('index'))
    
    except Exception as e:
        print(f"Google login error: {e}")
        flash('Failed to log in with Google. Please try again.', 'error')
        return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('index'))

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

# Comparison Module API's
@app.route('/comparison')
@login_required
def comparison():
    user = get_current_user()
    car_company=car_data.distinct("car_company")
    # Organizing car models under their respective companies
    car_models = {}
    car_variants={}
    for company in car_company:
        models = car_data.distinct("car_model", {"car_company": company})
        car_models[company] = models  # Store models under the company key

        for model in models:
            variants=car_data.distinct("car_new_name",{"car_model": model})
            car_variants[model]=variants # get all cars name
    print("Car Models Data:", car_models)
    return render_template('c.html', car_company=car_company, car_model=car_models, car_variant=car_variants, user=user)

@app.route('/compare_cars', methods=['POST'])
@login_required
def compare_cars():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No car data received"}), 400
        car_details = {}
        print("Received car data:", data)  # Debug log
        
        for i, car_name in enumerate(data.values(), 1):
            if not car_name or car_name == "select car":
                continue
                
            print(f"Searching for car: {car_name}")  # Debug log
            car = car_data.find_one({'car_name': car_name})  # Changed from 'name' to 'car_name'
            
            if not car:
                print(f"Car not found: {car_name}")  # Debug log
                continue
                
            print(f"Found car data: {car}")  # Debug log
            
            try:
                # Clean and standardize the data
                engine = str(car.get('engine', 'N/A')).replace('CC', '').strip()
                engine = int(engine) if engine.isdigit() else 0
                
                mileage = str(car.get('mileage', 'N/A')).replace('kmpl', '').strip()
                mileage = float(mileage) if mileage.replace('.', '').isdigit() else 0
                
                max_power = str(car.get('max_power', 'N/A')).replace('bhp', '').strip()
                max_power = float(max_power) if max_power.replace('.', '').isdigit() else 0
                
                car_details[f'car{i}'] = {
                    'car_company': car.get('car_company', 'N/A'),
                    'car_model': car.get('car_model', 'N/A'),
                    'car_name': car.get('car_name', 'N/A'),
                    'engine': engine,
                    'mileage': mileage,
                    'max_power': max_power,
                    'torque': car.get('torque', 'N/A'),
                    'seats': car.get('seats', 'N/A'),
                    'fuel_type': car.get('fuel', 'N/A'),
                    'transmission': car.get('transmission', 'N/A'),
                    'selling_price': car.get('selling_price', 'N/A'),
                    'year': car.get('year', 'N/A')
                }
            except Exception as e:
                print(f"Error processing car data for {car_name}: {e}")  # Debug log
                continue
        
        if not car_details:
            return jsonify({"error": "No valid cars found in database"}), 400
            
        print("Returning car details:", car_details)  # Debug log
        return jsonify(car_details)
        
    except Exception as e:
        print(f"Error in compare_cars: {e}")
        return jsonify({"error": "An error occurred while comparing cars"}), 500

@app.route('/save_comparison', methods=['POST'])
@login_required
def save_comparison():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Validate required fields
        if 'cars' not in data or 'details' not in data:
            return jsonify({"error": "Missing required fields: cars and details"}), 400

        user = get_current_user()
        if not user:
            return jsonify({"error": "User not found"}), 401

        # Create comparison document
        comparison_data = {
            "user_id": str(user['_id']),
            "user_name": user['name'],
            "user_email": user['email'],
            "cars": data['cars'],
            "details": data['details'],
            "created_at": datetime.utcnow()
        }
        
        # Save to database
        result = comp.insert_one(comparison_data)
        
        if not result.inserted_id:
            return jsonify({"error": "Failed to save comparison"}), 500
            
        return jsonify({
            "message": "Comparison saved successfully",
            "comparison_id": str(result.inserted_id)
        })
    
    except Exception as e:
        print(f"Error saving comparison: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/my_comparisons')
@login_required
def my_comparisons():
    try:
        user = get_current_user()
        user_comparisons = list(comp.find({"user_id": session['user_id']}).sort("created_at", -1))
        
        for comparison in user_comparisons:
            comparison['_id'] = str(comparison['_id'])
            comparison['created_at'] = comparison['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            for car_key, car_name in comparison.get('cars', {}).items():
                car_details = car_data.find_one({'name': car_name})
                if car_details:
                    comparison[f'{car_key}_details'] = {
                        'name': car_details.get('name'),
                        'company': car_details.get('company'),
                        'model': car_details.get('model'),
                        'year': car_details.get('year'),
                        'price': car_details.get('selling_price')
                    }

        return render_template('my_comparisons.html', comparisons=user_comparisons, user=user)
    
    except Exception as e:
        print(f"Error retrieving comparisons: {e}")
        flash('Error retrieving your comparisons', 'error')
        return redirect(url_for('comparison'))

# About US page API's
@app.route('/about', methods=['GET', 'POST'])
def about():
    user = get_current_user()
    return render_template('about.html', user=user)
# Contact Form API's
@app.route('/contact', methods=['POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('All fields are required!', 'error')
            return redirect(url_for('contact_form'))  # Redirect back to contact form page

        # ✅ Send confirmation email to user
        try:
            user_msg = Message(
                "Your message has been received - CarInfoX",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            user_msg.body = f"Hello {name},\n\nThank you for reaching out to CarInfoX. We have received your message:\n\n\"{message}\"\n\nWe will get back to you shortly.\n\nBest regards,\nCarInfoX Team"
            mail.send(user_msg)
        except Exception as e:
            flash('Error sending confirmation email to user.', 'error')
            print(f"Email error (User): {e}")

        # ✅ Send details to CarInfoX team
        try:
            admin_email = "rumitrvr@gmail.com"  # Replace with CarInfoX team email
            admin_msg = Message(
                "New Contact Form Submission - CarInfoX",
                sender=app.config['MAIL_USERNAME'],
                recipients=[admin_email]
            )
            admin_msg.body = f"New contact form submission:\n\nName: {name}\nEmail: {email}\nMessage: {message}\n\nPlease respond as soon as possible."
            mail.send(admin_msg)
        except Exception as e:
            flash('Error sending message to CarInfoX team.', 'error')
            print(f"Email error (Admin): {e}")

        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('index'))  # Redirect to home page

    return render_template('contact.html')

# Recommendation page API's
@app.route('/recommendation')
@login_required
def recommendation():
    user = get_current_user()
    return render_template('recommendation.html', user=user)

# Analysis Dashboard page API's
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    return render_template('dashboard.html', user=user)

# Latest Cars page API
@app.route('/latest_cars')
def latest_cars():
    user = get_current_user()
    return render_template('latest_cars.html', user=user)

# Car Review page API
@app.route('/car_review')
@login_required
def car_review():
    user = get_current_user()
    return render_template('car_review.html', user=user)

@app.route('/submit_review',methods=['POST'])
@login_required
def submit_review():
    try:
        user=get_current_user()
        review_details={
            "car":request.form.get("car"),
            "rating":request.form.get("rating"),
            "title":request.form.get("title"),
            "content":request.form.get("content"),
            "pros":request.form.get("pros"),
            "cons":request.form.get("cons"),
            "ownership_duration":request.form.get("ownershipDuration"),
            "username":user.name,
            "email":user.email,
            "timestamp":datetime.utcnow()
        }
        review.insert_one(review_details)
        return jsonify({"success": True, "message": "Review submitted successfully!"})
    except Exception as e:
        return jsonify({"success":False, "message": str(e)})

# My history API
@app.route('/my_history')
@login_required
def my_history():
    user=get_current_user()
    return render_template('my_history.html',user=user)

# Privacy Policy page API
@app.route('/privacy_policy')
def privacy_policy():
    user = get_current_user()
    return render_template('privacy_policy.html', user=user)

if __name__=='__main__':
    app.run(debug=True)
