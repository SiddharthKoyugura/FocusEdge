from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from send_notify import *
from datetime import datetime


app = Flask(__name__)
app.config["SECRET_KEY"] = "SDC12345"

# Database Employees
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employee.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Employee(UserMixin, db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    ename = db.Column(db.Integer, nullable=False, unique=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    company = db.Column(db.Text, nullable=False)
    designation = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Integer, nullable=False)

class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key = True)
    company = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable = False)
    mobile = db.Column(db.Integer, nullable = False)
    email = db.Column(db.Text, nullable= False)
    can_email= db.Column(db.Integer, nullable=False)
    can_mobile= db.Column(db.Integer, nullable=False)

class Activity(db.Model):
    __tablename__ = "activities"
    id = db.Column(db.Integer, primary_key = True)
    company = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

# Mail Config
app.config['MAIL_SERVER']='smtp.mail.yahoo.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'koyugurasiddhardha@yahoo.com'
app.config['MAIL_PASSWORD'] = 'qmekhjvrpzxylryn'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# User-defined functions
def send_mail(email, header, message):
    msg = Message(header, 
                            sender='koyugurasiddhardha@yahoo.com', 
                            recipients=[email])
    # set the body of the email
    msg.body = message
    # send the email
    mail.send(msg)

def add_activity(title):
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d %B")
    new_activity = Activity(
        company = current_user.company,
        title=title,
        date=formatted_date
    )
    db.session.add(new_activity)
    db.session.commit()


# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

def is_admin():
    if current_user.is_admin == 0:
        return False
    else:
        return True

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not is_admin():
                return abort(403)
            return f(*args, **kwargs)      
        except:
              return abort(403)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(user_id)
 
@app.route("/home")
@login_required
def home():
    company = current_user.company
    activities = Activity.query.filter_by(company=company).all()[::-1][:6]
    customers = Customer.query.filter_by(company=company).all()
    employees = Employee.query.filter_by(company=company).all()
    customercount, admincount, employeescount, emailcount, phonecount = len(customers), 0, len(employees), 0, 0
    email_list, mobile_list = [], []
    for customer in customers:
        if customer.can_email == 1:
            emailcount += 1
            email_list.append(customer)
        if customer.can_mobile == 1:
            phonecount += 1
            mobile_list.append(customer)

    for employee in employees:
        if employee.is_admin == 1: admincount += 1

    return render_template("index.html",
                            activities=activities,
                            customercount=customercount, 
                            emailcount=emailcount,
                            phonecount=phonecount,
                            employeescount=employeescount, 
                            admincount=admincount, 
                            email_list=email_list,
                            mobile_list=mobile_list,
                            current_user=current_user, 
                            is_admin=is_admin()
                        )

@app.route("/create-member", methods=["GET", "POST"])
@login_required
def create_member():
    if request.method == "POST":
        ename = request.form.get("ename")
        email = request.form.get("email")
        password = request.form.get("password")
        company = current_user.company
        isAdmin = request.form.get("isAdmin")
        new_employee = Employee(
            ename=ename, 
            password=password, 
            company=company, 
            designation=request.form.get("designation"),
            email=email,
            is_admin=int(isAdmin)
        )
        try:
            db.session.add(new_employee)
            db.session.commit()
            add_activity(f"created {ename} employee")
        except:
            flash("Employee is already working for this or another organization")
        return redirect(url_for('create_member'))
    return render_template("create-member.html", current_user=current_user, is_admin=is_admin())

@app.route("/read-members")
@login_required
def read_members():
    company = current_user.company
    employees = Employee.query.filter_by(company=company).all()
    employees_size = len(employees)
    return render_template("view-members.html", employees_size = employees_size, current_user=current_user, is_admin=is_admin(), employees=employees)

@app.route("/edit-member/<int:id>", methods=["GET", "POST"])
@login_required
def edit_member(id):
    employee = db.session.get(Employee, id)
    if request.method=="POST":
        employee.name = request.form.get("ename")
        employee.email = request.form.get("email")
        employee.is_admin = request.form.get("isAdmin")
        employee.designation = request.form.get("designation")
        db.session.commit()
        add_activity(f"Updated {request.form.get('name')} data")
        return redirect(url_for('read_members'))

    return render_template("edit-members.html", employee=employee, is_admin=is_admin())

@app.route("/delete-member/<int:id>", methods=["GET", "POST"])
@login_required
def delete_member(id):
    employee = db.session.get(Employee, id)
    db.session.delete(employee)
    db.session.commit()
    add_activity(f"deleted employee {employee.ename}")
    return redirect(url_for('read_members'))

@app.route("/add-customer", methods=["GET", "POST"])
@login_required
def add_customer():
    if request.method=="POST":
        company = current_user.company
        name = request.form.get("name")
        mobile = request.form.get("mobile")
        email = request.form.get("email")
        can_email = request.form.get("canEmail")
        can_mobile = request.form.get("canMobile")
        new_customer = Customer(
            company=company,
            name=name,
            mobile=mobile,
            email=email,
            can_email = int(can_email),
            can_mobile = int(can_mobile)
        )
        db.session.add(new_customer)
        db.session.commit()
        add_activity(f"created {name} customer")
        return redirect(url_for('add_customer'))
    return render_template("create-customers.html", current_user=current_user, is_admin=is_admin())

@app.route("/edit-customer/<int:id>", methods=["GET", "POST"])
@login_required
def edit_customer(id):
    customer = db.session.get(Customer, id)
    if request.method=="POST":
        customer.name = request.form.get("name")
        customer.email = request.form.get("email")
        customer.mobile = request.form.get("mobile")
        email, mobile = request.form.get("canMail"), request.form.get("canMobile")
        customer.can_email = int(email)
        customer.can_mobile = int(mobile)
        db.session.commit()
        add_activity(f"Updated {request.form.get('name')} data")
        return redirect(url_for('read_customers'))

    return render_template("edit-customers.html", customer=customer, is_admin=is_admin())

@app.route("/read-customers", methods=["GET", "POST"])
@login_required
def read_customers():
    company = current_user.company
    customers = Customer.query.filter_by(company=company).all()
    customer_size = len(customers)
    if request.method == "POST":
        all_checked = request.form.get("all")
        if all_checked:
            for customer in customers:
                message = request.form.get("message")
                if customer.can_email == 1:
                    try:
                        send_mail(email=customer.email, header=f'From {customer.company}', message=message)
                    except:
                        pass
                if customer.can_mobile == 1:
                    send_sms(6305461499, message)
                    send_whatsapp(6305461499, message)
        else:
            for customer in customers:
                is_checked = request.form.get(str(customer.id))
                if is_checked:
                    message = request.form.get("message")
                    if customer.can_email == 1:
                        try:
                            send_mail(email=customer.email, header=f'From {customer.company}', message=message)
                        except:
                            pass

                    if customer.can_mobile == 1:
                        send_sms(6305461499, message)
                        send_whatsapp(6305461499, message)
        return redirect(url_for('read_customers'))
    return render_template("view-customer.html",customer_size = customer_size, current_user=current_user, is_admin=is_admin(), customers=customers)

@app.route("/delete-customer/<int:id>", methods=["GET", "POST"])
@login_required
def delete_customer(id):
    customer = db.session.get(Customer, id)
    db.session.delete(customer)
    db.session.commit()
    add_activity(f"deleted customer {customer.name}")
    return redirect(url_for('read_customers'))

# Login Manager
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        employee = Employee.query.filter_by(email=email).first()
        if employee:
            password = request.form.get("password")
            if employee.password == password:
                login_user(employee)
                return redirect(url_for("home"))

            flash("Invalid password")
            return redirect(url_for("login"))

        flash("User not registered with email!")
        return redirect(url_for("login"))

    return render_template("login.html")
 
@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        ename = request.form.get("ename")
        email = request.form.get("email")
        password = request.form.get("password")
        company = request.form.get("company")
        designation = request.form.get("designation")
        is_admin = 1
        new_employee = Employee(
            ename=ename, 
            password=password, 
            company=company, 
            designation=designation,
            email=email,
            is_admin=is_admin
        )
        try:
            db.session.add(new_employee)
            db.session.commit()
        except:
            flash("User already registered")
            return redirect(url_for("register"))
        login_user(new_employee)
        return redirect(url_for('home'))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=3000)