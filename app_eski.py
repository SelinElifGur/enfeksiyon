from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mikrobiyoloji.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---- MODELLER ----
class Hasta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50))
    soyad = db.Column(db.String(50))
    servis = db.Column(db.String(50))
    bakteriler = db.relationship('Bakteri', backref='hasta', lazy=True)

class Bakteri(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(50))  # Örn: E. coli
    hasta_id = db.Column(db.Integer, db.ForeignKey('hasta.id'), nullable=False)
    antibiyogramlar = db.relationship('Antibiyogram', backref='bakteri', lazy=True)

class Antibiyogram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    antibiyotik = db.Column(db.String(50))  # Örn: Ampisilin
    sonuc = db.Column(db.String(20))  # Örn: Duyarlı / Dirençli
    bakteri_id = db.Column(db.Integer, db.ForeignKey('bakteri.id'), nullable=False)

# ---- ROUTES ----
@app.route('/')
def ana_sayfa():
    hastalar = Hasta.query.all()
    return render_template('index.html', hastalar=hastalar)

@app.route('/hasta/<int:id>')
def hasta_detay(id):
    hasta = Hasta.query.get_or_404(id)
    return render_template('detay.html', hasta=hasta)

if __name__ == '__main__':
    app.run(debug=True)
