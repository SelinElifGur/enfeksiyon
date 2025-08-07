from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mikrobiyoloji.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELLER
class Hasta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tc_kimlik = db.Column(db.String(11), unique=True, nullable=False)  # 🔹 yeni alan
    ad = db.Column(db.String(50))
    soyad = db.Column(db.String(50))
    servis = db.Column(db.String(50))
    

    bakteriler = db.relationship('Bakteri', backref='hasta', lazy=True)
    tedaviler = db.relationship('Tedavi', backref='hasta', lazy=True)
    
    
from datetime import date

class Bakteri(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(50))
    ureme_tarihi = db.Column(db.Date, default=date.today)  # 🔹 yeni alan
    hasta_id = db.Column(db.Integer, db.ForeignKey('hasta.id'), nullable=False)
    antibiyogramlar = db.relationship('Antibiyogram', backref='bakteri', lazy=True)

class Antibiyogram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    antibiyotik = db.Column(db.String(50))
    sonuc = db.Column(db.String(20))  # Duyarlı / Dirençli
    bakteri_id = db.Column(db.Integer, db.ForeignKey('bakteri.id'), nullable=False)

class Tedavi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    antibiyotik = db.Column(db.String(50))
    baslangic_tarihi = db.Column(db.Date, default=date.today)
    bitis_tarihi = db.Column(db.Date, nullable=True)
    dozaj = db.Column(db.String(50))  # Örn: 1g/8saat
    hasta_id = db.Column(db.Integer, db.ForeignKey('hasta.id'), nullable=False)

class KullanilanAntibiyotik(db.Model):
    __tablename__ = 'kullanilan_antibiyotik'
    id = db.Column(db.Integer, primary_key=True)
    antibiyotik = db.Column(db.String(50))
    baslangic = db.Column(db.Date)
    bitis = db.Column(db.Date)
    dozaj = db.Column(db.String(50))
    hasta_id = db.Column(db.Integer, db.ForeignKey('hasta.id'))

    hasta = db.relationship('Hasta', backref='kullanilan_antibiyotikler')



# ROUTES
@app.route('/')
def ana_sayfa():
    hastalar = Hasta.query.all()
    return render_template('index.html', hastalar=hastalar)

@app.route('/hasta/<int:id>')
def hasta_detay(id):
    hasta = Hasta.query.get_or_404(id)
    return render_template('detay.html', hasta=hasta)

@app.route('/hasta_ekle', methods=['GET', 'POST'])
def hasta_ekle():
    if request.method == 'POST':
        tc_kimlik = request.form['tc_kimlik']
        ad = request.form['ad']
        soyad = request.form['soyad']
        servis = request.form['servis']

        # 🔹 Aynı TC ile hasta var mı kontrol et
        mevcut_hasta = Hasta.query.filter_by(tc_kimlik=tc_kimlik).first()
        if mevcut_hasta:
            return "Bu TC ile kayıtlı hasta zaten var!", 400


        yeni_hasta = Hasta(tc_kimlik=tc_kimlik, ad=ad, soyad=soyad, servis=servis)
        db.session.add(yeni_hasta)
        db.session.commit()
        return redirect(url_for('ana_sayfa'))

    return render_template('hasta_ekle.html')

@app.route('/bakteri_ekle/<int:hasta_id>', methods=['GET', 'POST'])
def bakteri_ekle(hasta_id):
    if request.method == 'POST':
        isim = request.form['isim']
        ureme_tarihi_str = request.form['ureme_tarihi']

        # Tarihi stringten date objesine çevir
        ureme_tarihi = date.fromisoformat(ureme_tarihi_str) if ureme_tarihi_str else date.today()

        yeni_bakteri = Bakteri(isim=isim, ureme_tarihi=ureme_tarihi, hasta_id=hasta_id)
        db.session.add(yeni_bakteri)
        db.session.commit()

        return redirect(url_for('hasta_detay', id=hasta_id))

    hasta = Hasta.query.get_or_404(hasta_id)
    return render_template('bakteri_ekle.html', hasta=hasta)


@app.route('/antibiyogram_ekle/<int:bakteri_id>', methods=['GET', 'POST'])
def antibiyogram_ekle(bakteri_id):
    if request.method == 'POST':
        antibiyotik = request.form['antibiyotik']
        sonuc = request.form['sonuc']

        yeni_antibiyogram = Antibiyogram(antibiyotik=antibiyotik, sonuc=sonuc, bakteri_id=bakteri_id)
        db.session.add(yeni_antibiyogram)
        db.session.commit()
        return redirect(url_for('hasta_detay', id=Bakteri.query.get(bakteri_id).hasta_id))

    bakteri = Bakteri.query.get_or_404(bakteri_id)
    return render_template('antibiyogram_ekle.html', bakteri=bakteri)

from datetime import date

@app.route('/antibiyotik_ekle/<int:hasta_id>', methods=['GET', 'POST'])
def antibiyotik_ekle(hasta_id):
    if request.method == 'POST':
        antibiyotik = request.form['antibiyotik']
        baslangic = request.form['baslangic']
        bitis = request.form['bitis']
        dozaj = request.form['dozaj']

        # Tarihleri date objesine çeviriyoruz
        baslangic_date = date.fromisoformat(baslangic)
        bitis_date = date.fromisoformat(bitis) if bitis else None

        yeni_antibiyotik = KullanilanAntibiyotik(
            antibiyotik=antibiyotik,
            baslangic=baslangic_date,
            bitis=bitis_date,
            dozaj=dozaj,
            hasta_id=hasta_id
        )
        db.session.add(yeni_antibiyotik)
        db.session.commit()
        return redirect(url_for('hasta_detay', id=hasta_id))

    hasta = Hasta.query.get_or_404(hasta_id)
    return render_template('antibiyotik_ekle.html', hasta=hasta)

@app.route('/hasta_sil/<int:hasta_id>', methods=['POST'])
def hasta_sil(hasta_id):
    hasta = Hasta.query.get_or_404(hasta_id)

    # Önce ilişkili verileri de sil
    for bakteri in hasta.bakteriler:
        for ab in bakteri.antibiyogramlar:
            db.session.delete(ab)
        db.session.delete(bakteri)

    for ka in hasta.kullanilan_antibiyotikler:
        db.session.delete(ka)

    db.session.delete(hasta)
    db.session.commit()
    return redirect(url_for('ana_sayfa'))

@app.route('/bakteri_sil/<int:bakteri_id>', methods=['POST'])
def bakteri_sil(bakteri_id):
    bakteri = Bakteri.query.get_or_404(bakteri_id)
    
    # İlgili antibiyogramları sil
    for ab in bakteri.antibiyogramlar:
        db.session.delete(ab)
    
    db.session.delete(bakteri)
    db.session.commit()
    return redirect(url_for('hasta_detay', id=bakteri.hasta_id))

@app.route('/antibiyogram_sil/<int:ab_id>', methods=['POST'])
def antibiyogram_sil(ab_id):
    ab = Antibiyogram.query.get_or_404(ab_id)
    bakteri_id = ab.bakteri_id
    hasta_id = ab.bakteri.hasta_id
    
    db.session.delete(ab)
    db.session.commit()
    return redirect(url_for('hasta_detay', id=hasta_id))

@app.route('/antibiyotik_sil/<int:ka_id>', methods=['POST'])
def antibiyotik_sil(ka_id):
    ka = KullanilanAntibiyotik.query.get_or_404(ka_id)
    hasta_id = ka.hasta_id
    
    db.session.delete(ka)
    db.session.commit()
    return redirect(url_for('hasta_detay', id=hasta_id))




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
