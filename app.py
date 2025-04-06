from flask import Flask,render_template, request, redirect, flash, session,url_for, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail,Message
from datetime import datetime
from bson.objectid import ObjectId
from authlib.integrations.flask_client import OAuth
from functools import wraps
import os, cv2, PyPDF2, pytesseract, re
from werkzeug.utils import secure_filename
from bson import Binary  # Add this import for handling binary data
from pathlib import Path  # Add this import
import pandas as pd
import numpy as np
import joblib

#from config import Config
app=Flask(__name__)

#Configuration
app.config['MONGO_URI']='mongodb+srv://rumitpatel7660:Rumit%402003@carinfoxx.aqmgmdx.mongodb.net/CARINFOX'
app.config['SECRET_KEY'] = 'db0874988cf36807a8c6e0e0ba2c6f60'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '21it438@bvmengineering.ac.in'
app.config['MAIL_PASSWORD'] = 'Rumit@2003'
# Google OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = '1064395158995-4t434aq68r2ek64fj14mdsncq3o5f2gu.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'
app.config['GOOGLE_REDIRECT_URI'] = "http://127.0.0.1:5000/login/google/authorize"
#Initiliaze Extension
mongo=PyMongo(app)
users=mongo.db.Users_Data
car_data=mongo.db.Cars_Data
comp=mongo.db.Comparison_Data
review=mongo.db.Review_Data
mail=Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
oauth = OAuth(app)

# Update the configuration section at the top of your app.py
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'documents')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size
# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # Explicitly set userinfo endpoint
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',  # Manually specify the JWKs URI
    client_kwargs={'scope': 'openid email profile'},
)

# Load the model
try:
    model = joblib.load('static/models/car_price_predict.pkl')
    print("Model loaded successfully")
    label_encoders = joblib.load('static/models/label_encoders.pkl')
    print("Label encoders loaded successfully")
except Exception as e:
    print(f"Error loading model or encoders: {str(e)}")
    print(f"Error type: {type(e)}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
    model = None
    label_encoders = None

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

    try:
        user_msg=Message("Welcome to CarInfoX",
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[email])
        user_msg.body=f"""Hi {name},
    
    Welcome to CarInfoX! We're excited to have you on board.Get ready to explore the best car information and insights.

    Best Regards,
    CarInfoX Team"""
        mail.send(user_msg)
    except Exception as e:
        print(f"Error sending e-mail: {e}")
    
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
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()
        user = users.find_one({'google_id': user_info['id']})
        if not user:
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
            users.update_one(
                {'google_id': user_info['id']},
                {'$set': {
                    'profile_pic': user_info.get('picture'),
                    'last_login': datetime.utcnow()
                }}
            )
            user_id = str(user['_id'])
        session['user_id'] = user_id
        session['email'] = user_info['email']
        session['name'] = user_info['name']
        session['is_google_user'] = True
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Google login error: {e}")  # Print the exact error
        flash('Failed to log in with Google. Please try again.', 'error')
        return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
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
    car_models = {}
    car_variants={}
    for company in car_company:
        models = car_data.distinct("car_model", {"car_company": company})
        car_models[company] = models
        for model in models:
            variants=car_data.distinct("car_new_name",{"car_model": model})
            car_variants[model]=variants
    return render_template('c.html', car_company=car_company, car_model=car_models, car_variant=car_variants, user=user)

@app.route('/compare_cars', methods=['POST'])
@login_required
def compare_cars():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No car data received"}), 400
        car_details = {}
        for i, car_name in enumerate(data.values(), 1):
            if not car_name or car_name == "select car":
                continue
            car = car_data.find_one({'car_name': car_name})
            if not car:
                continue
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
                continue
        if not car_details:
            return jsonify({"error": "No valid cars found in database"}), 400
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
            return redirect(url_for('contact_form'))
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
        # ✅ Send details to CarInfoX team
        try:
            admin_email = "rumitrvr@gmail.com"
            admin_msg = Message(
                "New Contact Form Submission - CarInfoX",
                sender=app.config['MAIL_USERNAME'],
                recipients=[admin_email]
            )
            admin_msg.body = f"New contact form submission:\n\nName: {name}\nEmail: {email}\nMessage: {message}\n\nPlease respond as soon as possible."
            mail.send(admin_msg)
        except Exception as e:
            flash('Error sending message to CarInfoX team.', 'error')
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('index'))  # Redirect to home page
    return render_template('contact.html')

# Recommendation page API's
@app.route('/recommendation')
@login_required
def recommendation():
    user = get_current_user()
    df = pd.read_csv('NewCarData.csv')
    brands = sorted(df['Make'].unique().tolist())
    return render_template('recommendation.html', user=user, brands=brands)

@app.route('/predict_price', methods=['POST'])
@login_required
def predict_price():
    try:
        if model is None or label_encoders is None:
            return jsonify({'error': 'Model or encoders not loaded. Please try again later.'}), 500
        # Get data from form
        data = request.get_json()
        print("Received data:", data)
        # Extract features
        year = float(data.get('year', 0))
        km_driven = float(data.get('km_driven', 0))
        engine = float(data.get('engine', 0))
        max_power = float(data.get('max_power', 0))
        seats = float(data.get('seats', 0))
        fuel_tank = float(data.get('fuel_tank', 0))
        car_company = data.get('car_company', '')
        fuel_type = data.get('fuel_type', '')
        transmission = data.get('transmission', '')
        color = data.get('color', '')

        # Encode categorical features
        try:
            car_company_encoded = label_encoders['Make'].transform([car_company])[0]
            fuel_type_encoded = label_encoders['Fuel Type'].transform([fuel_type])[0]
            transmission_encoded = label_encoders['Transmission'].transform([transmission])[0]
            color_encoded = label_encoders['Color'].transform([color])[0]
        except Exception as e:
            print(f"Error encoding categorical features: {str(e)}")
            return jsonify({'error': f'Invalid categorical value: {str(e)}'}), 400

        # Create feature array with encoded values
        features = np.array([
            car_company_encoded,  # Make (encoded)
            fuel_type_encoded,    # Fuel Type (encoded)
            transmission_encoded, # Transmission (encoded)
            color_encoded,       # Color (encoded)
            year, km_driven, engine, max_power, seats, fuel_tank]).reshape(1, -1)
        # Make prediction
        prediction = model.predict(features)[0]
        print("Prediction:", prediction)
        return jsonify({
            'predicted_price': float(prediction),
            'features_used': {
                'car_company': car_company,
                'fuel_type': fuel_type,
                'transmission': transmission,
                'color': color,
                'year': year,
                'km_driven': km_driven,
                'engine': engine,
                'max_power': max_power,
                'seats': seats,
                'fuel_tank': fuel_tank
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Document validation helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_rc_book(text):
    """Validate RC Book content"""
    # Check for common RC Book patterns
    patterns = {
        'registration_number': r'[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}',
        'chassis_number': r'[A-Z0-9]{17}',
        'engine_number': r'[A-Z0-9]{6,17}',
        'owner_name': r'owner[:\s]+([a-zA-Z\s]+)',
        'vehicle_class': r'(MCWG|LMV|TRANSPORT|MOTOR CAR)',
        'registration_date': r'\d{2}/\d{2}/\d{4}'
    }
    matches = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        matches[key] = bool(match)
    # Return True if at least 3 patterns are found
    return sum(matches.values()) >= 3

def validate_puc(text):
    """Validate PUC certificate content"""
    patterns = {
        'puc_number': r'certificate\s+no[.:]\s*([A-Z0-9]+)',
        'valid_until': r'valid\s+(?:till|until)[:\s]+(\d{2}/\d{2}/\d{4})',
        'emission_values': r'(CO|HC|CO2|O2|RPM)[:\s]+\d+\.?\d*',
        'vehicle_number': r'[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}'
    }
    matches = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        matches[key] = bool(match)
    # Check if PUC is expired
    if matches['valid_until']:
        valid_until = re.search(patterns['valid_until'], text, re.IGNORECASE).group(1)
        valid_date = datetime.strptime(valid_until, '%d/%m/%Y')
        if valid_date < datetime.now():
            return False
    return sum(matches.values()) >= 2

def validate_insurance(text):
    """Validate Insurance document content"""
    patterns = {
        'policy_number': r'policy\s+no[.:]\s*([A-Z0-9-/]+)',
        'valid_until': r'valid\s+(?:till|until|up\s+to)[:\s]+(\d{2}/\d{2}/\d{4})',
        'insurer_name': r'(TATA|HDFC|ICICI|BAJAJ|NEW INDIA|ORIENTAL|UNITED|NATIONAL)',
        'vehicle_number': r'[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}'
    }
    matches = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        matches[key] = bool(match)
    # Check if insurance is expired
    if matches['valid_until']:
        valid_until = re.search(patterns['valid_until'], text, re.IGNORECASE).group(1)
        valid_date = datetime.strptime(valid_until, '%d/%m/%Y')
        if valid_date < datetime.now():
            return False
    return sum(matches.values()) >= 2

def extract_text_from_image(image_path):
    """Extract text from image using OCR"""
    try:
        # Read image using OpenCV
        img = cv2.imread(image_path)
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply threshold to get image with only black and white
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        # Extract text using pytesseract
        text = pytesseract.image_to_string(thresh)
        return text
    except Exception as e:
        print(f"Error in OCR processing: {e}")
        return ""

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error in PDF processing: {e}")
        return ""

@app.route('/validate_document', methods=['POST'])
def validate_document():
    try:
        if 'document' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No document uploaded'
            })

        file = request.files['document']
        document_type = request.form.get('document_type')

        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No selected file'
            })

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Invalid file type'
            })

        # Create upload directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        # Extract text based on file type
        file_extension = filename.rsplit('.', 1)[1].lower()
        if file_extension == 'pdf':
            text = extract_text_from_pdf(temp_path)
        else:
            text = extract_text_from_image(temp_path)

        # Validate document based on type
        validation_result = False
        if document_type == 'rc_book':
            validation_result = validate_rc_book(text)
        elif document_type == 'puc':
            validation_result = validate_puc(text)
        elif document_type == 'insurance':
            validation_result = validate_insurance(text)

        # Clean up temporary file
        os.remove(temp_path)

        if validation_result:
            return jsonify({
                'success': True,
                'message': 'Document validated successfully',
                'document_type': document_type
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Invalid {document_type.replace("_", " ")} document'
            })

    except Exception as e:
        print(f"Error in document validation: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing document: {str(e)}'
        }), 500

# Analysis Dashboard page API's
@app.route('/addcarsurvey', methods=['POST'])
@login_required
def addcarsurvey():
    try:
        # Get the current user
        user = get_current_user()
        if not user:
            return jsonify({
                "success": False,
                "message": "User not authenticated"
            }), 401
        # Get form data and file
        data = request.form.to_dict()
        document_file = request.files.get('document')
        document_type = data.get('document_type')
        document_binary = None
        filename = None

        # Validate document if provided
        if document_file and document_type:
            try:
                # Check if file type is allowed
                if not allowed_file(document_file.filename):
                    return jsonify({
                        "success": False,
                        "message": "Invalid file type. Allowed types are PDF and images."
                    }), 400
                # Secure the filename and create full path
                filename = secure_filename(document_file.filename)
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # Save file temporarily
                document_file.save(temp_path)
                # Extract text based on file type
                file_extension = filename.rsplit('.', 1)[1].lower()
                if file_extension == 'pdf':
                    text = extract_text_from_pdf(temp_path)
                else:
                    text = extract_text_from_image(temp_path)
                # Validate document based on type
                is_valid = False
                if document_type == 'rc_book':
                    is_valid = validate_rc_book(text)
                elif document_type == 'puc':
                    is_valid = validate_puc(text)
                elif document_type == 'insurance':
                    is_valid = validate_insurance(text)
                # If document is not valid, return error
                if not is_valid:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return jsonify({
                        "success": False,
                        "message": f"Invalid {document_type.replace('_', ' ')}. Please upload a valid document."
                    }), 400
                # If valid, read file into binary
                with open(temp_path, 'rb') as file:
                    document_binary = Binary(file.read())
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                # Clean up temporary file in case of error
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"Document processing error: {e}")
                return jsonify({
                    "success": False,
                    "message": f"Error processing document: {str(e)}"
                }), 500
        # Create the survey document
        survey_document = {
            # Basic Information
            'car_company': data.get('car_company'),
            'car_model': data.get('car_model'),
            'car_new_name': data.get('car_new_name'),
            'car_name': f"{data.get('car_company')} {data.get('car_model')} {data.get('car_new_name')}",
            # Car Details
            'year': int(data.get('year')),
            'selling_price': int(data.get('selling_price')),
            'km_driven': int(data.get('km_driven')),
            # Location
            'Region': data.get('Region'),
            'city': data.get('city'),
            # Specifications
            'fuel': data.get('fuel'),
            'transmission': data.get('transmission'),
            'owner': data.get('owner'),
            'mileage': float(data.get('mileage')),
            'engine': int(data.get('engine')),
            'max_power': float(data.get('max_power')),
            'seats': int(data.get('seats')),
            # Document Information
            'document_type': document_type if document_binary else None,
            'document_file': document_binary,
            'document_filename': filename,
            'document_verified': True if document_binary else False,
            # Additional Information
            'car_age': datetime.now().year - int(data.get('year')),
            # Metadata
            'user_id': str(user['_id']),
            'user_email': user['email'],
            'created_at': datetime.utcnow(),
        }

        # Validate required fields
        required_fields = [
            'car_company', 'car_model', 'car_new_name', 'year', 
            'selling_price', 'km_driven', 'Region', 'city',
            'fuel', 'transmission', 'owner', 'mileage',
            'engine', 'max_power', 'seats'
        ]
        missing_fields = [field for field in required_fields if not survey_document.get(field)]
        if missing_fields:
            return jsonify({
                "success": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        # Insert into database
        result = car_data.insert_one(survey_document)
        if result.inserted_id:
            return jsonify({
                "success": True,
                "message": "Car survey saved successfully with verified documents",
                "id": str(result.inserted_id)
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to save car survey"
            }), 500
    except Exception as e:
        print(f"Error in addcarsurvey: {e}")
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    # Get total number of cars
    total_cars = car_data.count_documents({})
    # Get total number of unique companies
    companies = car_data.distinct('car_company')
    total_companies = len(companies)
    # Calculate average price
    price_pipeline = [
        {'$group': {'_id': None, 'avg_price': {'$avg': '$selling_price'}}}
    ]
    avg_price_result = list(car_data.aggregate(price_pipeline))
    avg_price = int(avg_price_result[0]['avg_price']) if avg_price_result else 0
    # Calculate average mileage
    mileage_pipeline = [{'$group': {'_id': None, 'avg_mileage': {'$avg': '$mileage'}}}]
    avg_mileage_result = list(car_data.aggregate(mileage_pipeline))
    avg_mileage = round(avg_mileage_result[0]['avg_mileage'], 2) if avg_mileage_result else 0
    # Get price trends by year and company
    price_trend_pipeline = [
        {'$group': {
            '_id': {
                'year': '$year',
                'company': '$car_company'
            },
            'avg_price': {'$avg': '$selling_price'}
        }},
        {'$project': {
            '_id': '$_id.year',
            'company': '$_id.company',
            'avg_price': 1
        }},
        {'$sort': {'_id': 1}}
    ]
    price_data = list(car_data.aggregate(price_trend_pipeline))
    # Get company distribution
    company_pipeline = [
        {'$group': {
            '_id': '$car_company',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 12}
    ]
    company_data = list(car_data.aggregate(company_pipeline))
    # Get fuel type distribution with company info
    fuel_pipeline = [
        {
            '$group': {
                '_id': {
                    'fuel': '$fuel',
                    'company': '$car_company'
                },
                'count': {'$sum': 1}
            }
        },
        {
            '$group': {
                '_id': {
                    'fuel': '$_id.fuel',
                    'company': '$_id.company'
                },
                'count': {'$first': '$count'},
                'total_count': {'$sum': '$count'}
            }
        },
        {
            '$project': {
                '_id': '$_id.fuel',
                'company': '$_id.company',
                'count': '$count',
                'total_count': '$total_count'
            }
        },
        {'$sort': {'count': -1}}
    ]
    fuel_data = list(car_data.aggregate(fuel_pipeline))
    # Get region distribution
    region_pipeline = [
        {
            '$group': {
                '_id': {
                    'region': '$Region',
                    'company': '$car_company'
                },
                'count': {'$sum': 1},
                'avg_price': {'$avg': '$selling_price'}
            }
        },
        {
            '$group': {
                '_id': '$_id.region',
                'count': {'$sum': '$count'},
                'company_data': {
                    '$push': {
                        'company': '$_id.company',
                        'count': '$count',
                        'avg_price': '$avg_price'
                    }
                },
                'total_avg_price': {'$avg': '$avg_price'}
            }
        },
        {'$sort': {'count': -1}}
    ]
    region_data = list(car_data.aggregate(region_pipeline))

    return render_template('dashboard.html',
                        total_cars=total_cars,
                        total_companies=total_companies,
                        companies=companies,
                        avg_price="{:,.0f}".format(avg_price),
                        avg_mileage=avg_mileage,
                        price_data=price_data,
                        company_data=company_data,
                        fuel_data=fuel_data,
                        user=user,
                        region_data=region_data)

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
        user = get_current_user()
        data = request.get_json() if request.is_json else request.form.to_dict()
        if not data:
            return jsonify({"success": False, "message": "No data received!"}), 400
        review_details = {
            "car": data.get("car"),
            "rating": data.get("rating"),
            "title": data.get("title"),
            "content": data.get("content"),
            "pros": data.get("pros"),
            "cons": data.get("cons"),
            "ownership_duration": data.get("ownershipDuration"),
            "username": user.get("name"),
            "email": user.get("email"),
            "timestamp": datetime.utcnow()
        }

        if any(value in [None, ""] for key, value in review_details.items() if key not in ["username", "email", "timestamp"]):
            return jsonify({"success": False, "message": "All fields are required!"}), 400

        review.insert_one(review_details)
        return jsonify({"success": True, "message": "Review submitted successfully!"})
    except Exception as e:
        return jsonify({"success":False, "message": str(e)})

# My history API
@app.route('/my_history')
@login_required
def my_history():
    try:
        user = get_current_user()
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('index'))
        # Get user's comparisons
        user_comparisons = []
        try:
            user_comparisons = list(comp.find({"user_id": session['user_id']}).sort("created_at", -1))
            for comparison in user_comparisons:
                comparison['id'] = str(comparison['_id'])
                comparison['date'] = comparison['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                cars = comparison.get('cars', {})
                car_details = []

                # Fetch car details for all cars in the comparison
                for car_key, car_name in cars.items():
                    car = car_data.find_one({'car_name': car_name})
                    if car:
                        car_details.append({
                            'name': f"{car.get('car_company', '')} {car.get('car_model', '')}",
                            'engine': car.get('engine', 'N/A'),
                            'mileage': float(str(car.get('mileage', '0')).replace('kmpl', '').strip() or 0),
                            'max_power': float(str(car.get('max_power', '0')).replace('bhp', '').strip() or 0),
                            'torque': car.get('torque', 'N/A'),
                            'fuel_type': car.get('fuel', 'N/A'),
                            'transmission': car.get('transmission', 'N/A'),
                            'seats': car.get('seats', 'N/A'),
                            'price': float(str(car.get('selling_price', '0')).replace(',', '').strip() or 0),
                            'year': car.get('year', 'N/A')
                        })

                # Add car details to the comparison
                comparison['car_details'] = car_details
                # Calculate metrics if there are at least two cars
                if len(car_details) > 1:
                    try:
                        # Calculate price, mileage, and power differences
                        price_differences = [
                            abs(car_details[i]['price'] - car_details[j]['price'])
                            for i in range(len(car_details)) for j in range(i + 1, len(car_details))
                        ]
                        mileage_differences = [
                            abs(car_details[i]['mileage'] - car_details[j]['mileage'])
                            for i in range(len(car_details)) for j in range(i + 1, len(car_details))
                        ]
                        power_differences = [
                            abs(car_details[i]['max_power'] - car_details[j]['max_power'])
                            for i in range(len(car_details)) for j in range(i + 1, len(car_details))
                        ]
                        # Find the best car based on price, mileage, and power
                        comparison['best_price_car'] = min(car_details, key=lambda x: x['price'])['name']
                        comparison['best_mileage_car'] = max(car_details, key=lambda x: x['mileage'])['name']
                        comparison['best_power_car'] = max(car_details, key=lambda x: x['max_power'])['name']
                        # Add summary metrics
                        comparison['price_differences'] = price_differences
                        comparison['mileage_differences'] = mileage_differences
                        comparison['power_differences'] = power_differences
                    except Exception as e:
                        print(f"Error calculating comparison metrics: {e}")
                        comparison['calculation_error'] = True
        except Exception as e:
            print(f"Error processing comparisons: {e}")
            user_comparisons = []
        # Get user's reviews
        user_reviews = []
        try:
            user_reviews = list(review.find({"email": user['email']}).sort("timestamp", -1))
            for rev in user_reviews:
                rev['car_name'] = rev.get('car', 'Unknown Car')
                rev['date'] = rev.get('timestamp', datetime.utcnow()).strftime('%d-%m-%Y %H:%M:%S')
                rev['rating'] = int(rev.get('rating', 0))
                rev['comment'] = rev.get('content', '')
                rev['pros'] = rev.get('pros', [])
                rev['cons'] = rev.get('cons', [])
                rev['ownership_duration'] = rev.get('ownership_duration', 'Not specified')
                rev['title'] = rev.get('title', '')
        except Exception as e:
            print(f"Error processing reviews: {e}")
            user_reviews = []
        # Add join date to user info
        if 'created_at' in user:
            user['join_date'] = user['created_at'].strftime('%B %Y')
        else:
            user['join_date'] = 'Unknown'
        # Add user statistics
        try:
            last_activity = 'No activity'
            if user_comparisons or user_reviews:
                comparison_dates = [c.get('created_at') for c in user_comparisons if c.get('created_at')]
                review_dates = [r.get('timestamp') for r in user_reviews if r.get('timestamp')]
                if comparison_dates or review_dates:
                    last_activity = max(comparison_dates + review_dates).strftime('%d-%m-%Y %H:%M:%S')
            user['stats'] = {
                'total_comparisons': len(user_comparisons),
                'total_reviews': len(user_reviews),
                'avg_rating': round(sum(r.get('rating', 0) for r in user_reviews) / len(user_reviews), 1) if user_reviews else 0,
                'last_activity': last_activity
            }
        except Exception as e:
            print(f"Error calculating user stats: {e}")
            user['stats'] = {
                'total_comparisons': 0,
                'total_reviews': 0,
                'avg_rating': 0,
                'last_activity': 'No activity'
            }
        return render_template('my_history.html',
                            user=user,
                            comparisons=user_comparisons,
                            reviews=user_reviews)
    except Exception as e:
        print(f"Error in my_history route: {e}")
        flash('Error retrieving your history. Please try again later.', 'error')
        return redirect(url_for('index'))

# Update Profile API
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        # Get form data
        new_name = request.form.get('name')
        new_email = request.form.get('email')

        # Validate inputs
        if not new_name or not new_email:
            return jsonify({
                "success": False,
                "message": "Name and email are required"
            }), 400
        # Check if email already exists for another user
        existing_user = users.find_one({
            'email': new_email,
            '_id': {'$ne': ObjectId(session['user_id'])}
        })
        if existing_user:
            return jsonify({
                "success": False,
                "message": "Email already in use by another account"
            }), 400
        # Update user in database
        result = users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {
                'name': new_name,
                'email': new_email,
                'updated_at': datetime.utcnow()
            }}
        )
        if result.modified_count > 0:
            # Update session data
            session['name'] = new_name
            session['email'] = new_email
            return jsonify({
                "success": True,
                "message": "Profile updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "No changes were made"
            }), 400

    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred while updating profile"
        }), 500
# Privacy Policy page API
@app.route('/privacy_policy')
def privacy_policy():
    user = get_current_user()
    return render_template('privacy_policy.html', user=user)

if __name__=='__main__':
    app.run(debug=True)