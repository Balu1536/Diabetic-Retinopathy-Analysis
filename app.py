# noinspection PyUnresolvedReferences
from flask import Flask, render_template, request, redirect, url_for, session
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os

from cloudant.client import Cloudant

app = Flask(__name__)

# ✅ REQUIRED for sessions
app.secret_key = ""

# ✅ Load Model
model = load_model("model/Updated-Xception-diabetic-retinopathy.h5")

UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

classes = ['No_DR', 'Mild', 'Moderate', 'Severe', 'Proliferate_DR']

# ✅ Cloudant Credentials
USERNAME = ""
APIKEY   = ""
URL      = ""

client = Cloudant.iam(USERNAME, APIKEY, connect=True, url=URL)

DB_NAME = "my_database"

if DB_NAME not in client.all_dbs():
    db = client.create_database(DB_NAME)
else:
    db = client[DB_NAME]

print("Cloudant connected successfully ✅")


# ✅ HOME PAGE (Project Details Page)
@app.route("/")
def home():
    return render_template("index.html")


# ✅ REGISTER PAGE
@app.route("/register")
def register():
    return render_template("register.html")


# ✅ HANDLE REGISTRATION
@app.route("/afterreg", methods=["POST"])
def afterreg():
    username = request.form['id']
    password = request.form['psw']

    query = {'_id': {'$eq': username}}
    docs = db.get_query_result(query)

    if len(list(docs)) == 0:
        data = {
            "_id": username,
            "password": password
        }
        db.create_document(data)
        return render_template("login.html", pred="Registration Successful ✅ Please Login")
    else:
        return render_template("register.html", pred="User already exists ❌")


# ✅ LOGIN PAGE
@app.route("/login")
def login():
    return render_template("login.html")


# ✅ HANDLE LOGIN
@app.route("/afterlogin", methods=["POST"])
def afterlogin():
    username = request.form['id']
    password = request.form['psw']

    try:
        user_doc = db[username]

        if user_doc['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for("prediction_page"))
        else:
            return render_template("login.html", pred="Invalid Password ❌")

    except KeyError:
        return render_template("login.html", pred="User Not Found ❌")


# ✅ PREDICTION PAGE (Protected)
@app.route("/prediction")
def prediction_page():

    if not session.get('logged_in'):
        return redirect(url_for("login"))

    return render_template("prediction.html")


# ✅ IMAGE PREDICTION (Protected)
@app.route("/result", methods=["POST"])
def result():

    if not session.get('logged_in'):
        return redirect(url_for("login"))

    file = request.files['image']

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    img = image.load_img(filepath, target_size=(299, 299))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = img / 255.0

    pred = model.predict(img)
    result_label = classes[np.argmax(pred)]

    doc = {
        "user": session.get('username'),
        "image": file.filename,
        "prediction": result_label
    }
    db.create_document(doc)

    return render_template(
        "prediction.html",
        prediction=result_label,
        img_path=filepath
    )


# ✅ LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return render_template("logout.html")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


# ✅ RUN SERVER
if __name__ == "__main__":
    app.run(debug=True)
