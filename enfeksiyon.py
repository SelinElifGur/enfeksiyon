import sys
import sqlite3
import os
import csv
from typing import List, Optional, Tuple

from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtCore import QDate, Qt, QDateTime
from PyQt5.QtGui import QIntValidator, QTextDocument, QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox, QTableWidgetItem,
    QDateEdit, QComboBox, QHeaderView, QTableWidget,
    QScrollArea, QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QRadioButton, QToolBar, QAction, QTextEdit, QFileDialog,
    QAbstractButton
)

from ana_pencere import Ui_MainWindow
from detay_pencere import Ui_MainWindow as Ui_DetayPencere

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hastatakip.db")

# ------------------ Veritabanı ------------------
def _ensure_columns(cur, table, cols: List[Tuple[str, str]]):
    cur.execute(f"PRAGMA table_info({table})")
    mevcut = {r[1] for r in cur.fetchall()}
    for ad, tip in cols:
        if ad not in mevcut:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {ad} {tip}")

def veritabani_olustur():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # hasta
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hasta(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tc TEXT UNIQUE,
            ad TEXT,
            soyad TEXT,
            dogum TEXT,
            servis TEXT
        )
    """)

    # bakteri
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bakteri(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kultur_ornegi TEXT,
            isim TEXT,
            ureme_tarihi TEXT,
            hasta_id INTEGER,
            FOREIGN KEY(hasta_id) REFERENCES hasta(id)
        )
    """)
    _ensure_columns(cur, "bakteri", [("kultur_ornegi", "TEXT")])

    # antibiyogram
    cur.execute("""
        CREATE TABLE IF NOT EXISTS antibiyogram(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            antibiyotik TEXT,
            sonuc TEXT,
            bakteri_id INTEGER,
            FOREIGN KEY(bakteri_id) REFERENCES bakteri(id)
        )
    """)

    # ilac
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ilac(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ilac TEXT,
            baslangic TEXT,
            bitis TEXT,
            dozaj TEXT,
            hasta_id INTEGER,
            FOREIGN KEY(hasta_id) REFERENCES hasta(id)
        )
    """)

    # laboratuvar
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lab(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hasta_id INTEGER,
            created_at TEXT,
            ppd TEXT,
            crp REAL, lokosit REAL, lenfosit REAL, notrofil REAL, pct REAL,
            glukoz REAL, na REAL, cl REAL, p REAL, mg REAL,
            ast REAL, alt REAL, ggt REAL, alp REAL,
            tbil REAL, dbil REAL, albumin REAL,
            kreatinin REAL, bun REAL, egfrt REAL,
            FOREIGN KEY(hasta_id) REFERENCES hasta(id)
        )
    """)

    # anket
    cur.execute("""
        CREATE TABLE IF NOT EXISTS anket(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hasta_id INTEGER,
            created_at TEXT
        )
    """)

    gerekli = [
        ("ates","TEXT"),("oksuruk","TEXT"),("gece_terleme","TEXT"),("kilo_kaybi","TEXT"),
        ("aile_tb","TEXT"),("usye_asye","TEXT"),("agzi_acik","TEXT"),("inhaler","TEXT"),
        ("evneb","TEXT"),("yasam_yeri","TEXT"),("evde_kisi","INTEGER"),
        ("hayvan","TEXT"),("hayvan_not","TEXT"),("cigsut","TEXT"),("oral_aft","TEXT"),
        ("genital_ulser","TEXT"),("tekrarlayan","TEXT"),("eklem","TEXT"),("eklem_not","TEXT"),
        ("romatizma","TEXT"),
        ("hafta","TEXT"),("nsvy_cs","TEXT"),("gr","TEXT"),("kuvoz","TEXT"),("anne_sutu","TEXT"),
        ("asilari","TEXT"),("anne_yas","TEXT"),("anne_ss","TEXT"),("baba_yas","TEXT"),
        ("baba_ss","TEXT"),("akrabalik","TEXT"),("akrabalik_not","TEXT"),
        ("cocuk1","TEXT"),("cocuk2","TEXT"),("cocuk3","TEXT"),("cocuk4","TEXT"),
        ("aile_hastalik","TEXT"),("aile_hastalik_not","TEXT"),
        ("ta","TEXT"),("n","TEXT"),("t","TEXT"),("ss","TEXT"),("boy","TEXT"),
        ("genel_durum","TEXT"),("alerji","TEXT"),("alerji_not","TEXT"),
        ("diyabet","TEXT"),("diyabet_not","TEXT"),("orofarenks","TEXT"),
        ("postnazal","TEXT"),("servikal","TEXT"),("solunum","TEXT"),
        ("ral","TEXT"),("ral_not","TEXT"),("ronkus","TEXT"),("ronkus_not","TEXT"),
        ("kalp_ritim","TEXT"),("kalp_not","TEXT"),("ufurum","TEXT"),("batin","TEXT"),
        ("batin_not","TEXT"),("hsm","TEXT"),("ense","TEXT"),("mib","TEXT"),("dokuntu","TEXT"),
        ("klinik_gozlem","TEXT")
    ]
    _ensure_columns(cur, "anket", gerekli)

    conn.commit()
    conn.close()

# ------------------ Yardımcılar ------------------
def try_get_int(item: Optional[QTableWidgetItem]) -> Optional[int]:
    if not item:
        return None
    try:
        return int(item.text())
    except Exception:
        return None

# ------------------ Dialoglar ------------------
class HastaEkleDialog(QDialog):
    def __init__(self, baslik="Yeni Hasta Ekle", parent=None):
        super().__init__(parent)
        self.setWindowTitle(baslik)
        layout = QFormLayout(self)

        self.tc_input = QLineEdit()
        self.ad_input = QLineEdit()
        self.soyad_input = QLineEdit()
        self.dogum_input = QDateEdit(); self.dogum_input.setCalendarPopup(True)
        self.dogum_input.setDate(QDate.currentDate())
        self.servis_input = QLineEdit()

        layout.addRow("TC Kimlik:", self.tc_input)
        layout.addRow("Ad:", self.ad_input)
        layout.addRow("Soyad:", self.soyad_input)
        layout.addRow("Doğum Tarihi:", self.dogum_input)
        layout.addRow("Servis:", self.servis_input)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return (self.tc_input.text().strip(),
                self.ad_input.text().strip(),
                self.soyad_input.text().strip(),
                self.dogum_input.date().toString("dd-MM-yyyy"),
                self.servis_input.text().strip())

class BakteriEkleDialog(QDialog):
    def __init__(self, baslik="Bakteri Bilgisi", parent=None):
        super().__init__(parent)
        self.setWindowTitle(baslik)
        layout = QFormLayout(self)

        self.kultur_input = QComboBox(); self.kultur_input.setEditable(True)
        self.kultur_input.addItems([
            "İdrar","Kan","Balgam","Yara","BOS","Gaita",
            "Trakeal Aspirat","Nazofaringeal Sürüntü","Diğer"
        ])
        self.bakteri_input = QLineEdit()
        self.tarih_input = QDateEdit(); self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDate(QDate.currentDate())

        layout.addRow("Kültür Örneği:", self.kultur_input)
        layout.addRow("Bakteri Adı:", self.bakteri_input)
        layout.addRow("Üreme Tarihi:", self.tarih_input)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return (self.kultur_input.currentText().strip(),
                self.bakteri_input.text().strip(),
                self.tarih_input.date().toString("dd-MM-yyyy"))

class AntibiyogramEkleDialog(QDialog):
    def __init__(self, baslik="Antibiyogram Bilgisi", parent=None):
        super().__init__(parent)
        self.setWindowTitle(baslik)
        layout = QFormLayout(self)
        self.antibiyotik_input = QLineEdit()
        self.sonuc_input = QComboBox(); self.sonuc_input.addItems(["Duyarlı","Orta Duyarlı","Dirençli"])
        layout.addRow("Antibiyotik:", self.antibiyotik_input)
        layout.addRow("Sonuç:", self.sonuc_input)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return (self.antibiyotik_input.text().strip(), self.sonuc_input.currentText())

class IlacEkleDialog(QDialog):
    def __init__(self, baslik="İlaç Bilgisi", parent=None):
        super().__init__(parent)
        self.setWindowTitle(baslik)
        layout = QFormLayout(self)
        self.ilac_input = QLineEdit()
        self.baslangic_input = QDateEdit(); self.baslangic_input.setCalendarPopup(True); self.baslangic_input.setDate(QDate.currentDate())
        self.bitis_input = QDateEdit(); self.bitis_input.setCalendarPopup(True); self.bitis_input.setDate(QDate.currentDate())
        self.dozaj_input = QLineEdit()
        layout.addRow("İlaç Adı:", self.ilac_input)
        layout.addRow("Başlangıç Tarihi:", self.baslangic_input)
        layout.addRow("Bitiş Tarihi:", self.bitis_input)
        layout.addRow("Dozaj:", self.dozaj_input)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return (self.ilac_input.text().strip(),
                self.baslangic_input.date().toString("dd-MM-yyyy"),
                self.bitis_input.date().toString("dd-MM-yyyy"),
                self.dozaj_input.text().strip())

# ------------------ ANKET ------------------
class AnketPenceresi(QDialog):
    def __init__(self, hasta_id: int, parent=None):
        super().__init__(parent)
        self.hasta_id = hasta_id
        self.setWindowTitle("Hasta Anketi (Detaylı)")
        self.setMinimumSize(880, 640)
        self._v = lambda pair: "Var" if pair[0].isChecked() else ("Yok" if pair[1].isChecked() else None)
        self._e = lambda pair: "Evet" if pair[0].isChecked() else ("Hayır" if pair[1].isChecked() else None)

        root = QVBoxLayout(self)
        root.addWidget(QLabel("HASTA ANKETİ", self))
        scroll = QScrollArea(self); scroll.setWidgetResizable(True); root.addWidget(scroll)
        content = QWidget(); scroll.setWidget(content); self.form = QFormLayout(content)

        def add_header(text: str):
            lbl = QLabel(text, self); f = lbl.font(); f.setBold(True); f.setPointSize(max(11, f.pointSize()+1)); lbl.setFont(f)
            self.form.addRow(lbl)

        def add_vy(label: str):
            row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0,0,0,0)
            rb1, rb2 = QRadioButton("Var"), QRadioButton("Yok")
            h.addWidget(rb1); h.addWidget(rb2); h.addStretch(1)
            self.form.addRow(QLabel(label), row); return rb1, rb2

        def add_eh(label: str):
            row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0,0,0,0)
            rb1, rb2 = QRadioButton("Evet"), QRadioButton("Hayır")
            h.addWidget(rb1); h.addWidget(rb2); h.addStretch(1)
            self.form.addRow(QLabel(label), row); return rb1, rb2

        def add_vy_note(label: str, ph="Not…"):
            row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0,0,0,0)
            rb1, rb2, le = QRadioButton("Var"), QRadioButton("Yok"), QLineEdit(); le.setPlaceholderText(ph); le.setMinimumWidth(220)
            def toggle():
                le.setEnabled(rb1.isChecked())
            rb1.toggled.connect(toggle); rb2.toggled.connect(toggle); rb2.setChecked(True); toggle()
            h.addWidget(rb1); h.addWidget(rb2); h.addWidget(le); h.addStretch(1)
            self.form.addRow(QLabel(label), row); return rb1, rb2, le

        def add_text(label: str, ph=""):
            le = QLineEdit(); le.setPlaceholderText(ph); le.setMinimumWidth(220); self.form.addRow(QLabel(label), le); return le

        def add_combo(label: str, items: List[str]):
            cmb = QComboBox(); cmb.addItems(items); self.form.addRow(QLabel(label), cmb); return cmb

        def add_int(label: str, ph="Sayı"):
            le = QLineEdit(); le.setValidator(QIntValidator(0, 999)); le.setPlaceholderText(ph); self.form.addRow(QLabel(label), le); return le

        # --- Ön tanı
        add_header("ÖN TANI")
        self.ates = add_vy("Ateş"); self.oksuruk = add_vy("Öksürük"); self.gece_terleme = add_vy("Gece terlemesi")
        self.kilo_kaybi = add_vy("Kilo kaybı"); self.aile_tb = add_vy("Ailede TB hastalığı")
        self.usye_asye = add_vy("Sık ÜSYE/ASYE öyküsü"); self.agzi_acik = add_vy("Ağzı açık uyuma")
        self.inhaler = add_vy("İnhaler/Nebülizatör kullanım öyküsü"); self.evneb = add_vy("Evde nebülizatör cihazı")
        self.yasam_yeri = add_combo("Yaşam yeri", ["", "Müstakil ev", "Apartman", "Diğer"])
        self.evde_kisi = add_int("Evde yaşayan kişi sayısı")
        self.hayvan = add_vy_note("Hayvan/Böcek teması", "Örn: kedi tırmalaması…")
        self.cigsut = add_vy("Çiğ süt ve ürünleri tüketimi"); self.oral_aft = add_vy("Oral aft"); self.genital_ulser = add_vy("Genital ülser")
        self.tekrarlayan = add_text("Tekrarlayan belirtiler (serbest)", "Örn: Ateş, Eklem ağrısı…")
        self.eklem = add_vy_note("Eklemlerde ağrı/şişlik/kızarıklık", "Örn: sağ diz ağrısı…")
        self.romatizma = add_vy("Ailede bilinen romatizmal hastalık")

        # --- Özgeçmiş
        add_header("ÖZGEÇMİŞ")
        self.hafta = add_text("HAFTA", "Örn: 39+2"); self.nsvy_cs = add_text("NSVY - C/S", "Örn: NSVY"); self.gr = add_text("GR", "Örn: 3200 g")
        self.kuvoz = add_eh("Küvözde kalmış mı?"); self.anne_sutu = add_eh("Anne sütü"); self.asilari = add_text("Aşıları", "Çocukluk dönemi aşı bilgisi…")
        self.anne_yas = add_text("ANNE YAŞ"); self.anne_ss = add_text("ANNE S/S"); self.baba_yas = add_text("BABA YAŞ"); self.baba_ss = add_text("BABA S/S")
        self.akrabalik = add_vy_note("Akrabalık", "Açıklama…")
        self.cocuk1 = add_text("1. Çocuk (Yaş/K-E/SS)"); self.cocuk2 = add_text("2. Çocuk (Yaş/K-E/SS)")
        self.cocuk3 = add_text("3. Çocuk (Yaş/K-E/SS)"); self.cocuk4 = add_text("4. Çocuk (Yaş/K-E/SS)")
        self.aile_hastalik = add_vy_note("Ailede bilinen önemli hastalık", "Örn: talasemi taşıyıcılığı…")

        # --- FM
        add_header("FİZİK MUAYENE (FM)")
        self.ta = add_text("Tansiyon (TA)"); self.n = add_text("Nabız (N)"); self.t = add_text("Vücut ısısı (T)"); self.ss = add_text("Solunum (SS)")
        self.boy = add_text("BOY"); self.genel_durum = add_text("GENEL DURUM", "Serbest tanım…")
        self.alerji = add_vy_note("ALERJİ", "Alerjen / açıklama…"); self.diyabet = add_vy_note("DİYABET", "Açıklama…")
        self.orofarenks = add_text("OROFARENKS-TONSİLLER", "Bulgu…"); self.postnazal = add_vy("POSTNAZAL AKINTI")
        self.servikal = add_text("SERVİKAL LAP", "Bulgu…"); self.solunum = add_text("SOLUNUM SESLERİ", "Doğal / açıklama…")
        self.ral = add_vy_note("RAL","Açıklama…"); self.ronkus = add_vy_note("RONKÜS","Açıklama…")
        self.kalp_ritim = add_eh("KALP SESLERİ RİTMİK"); self.kalp_not = add_text("KALP NOTU","Ek açıklama…")
        self.ufurum = add_vy("ÜFÜRÜM"); self.batin = add_eh("BATIN RAHAT"); self.batin_not = add_text("BATIN NOTU","Ek açıklama…")
        self.hsm = add_vy("HSM"); self.ense = add_vy("ENSE SERTLİĞİ"); self.mib = add_vy("MENİNGEAL İRRİTASYON BULGUSU (MİB)")
        self.dokuntu = add_vy("DÖKÜNTÜ")

        # ---------- KLİNİK GÖZLEM ----------
        add_header("KLİNİK GÖZLEM")
        self.klinik_gozlem = QTextEdit()
        self.klinik_gozlem.setPlaceholderText("Klinik gözlem / notlar…")
        self.klinik_gozlem.setMinimumHeight(140)
        self.form.addRow(QLabel("Klinik gözlem"), self.klinik_gozlem)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.kaydet); btns.rejected.connect(self.reject); root.addWidget(btns)
        self._son_anketi_yukle()

    def _son_anketi_yukle(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT * FROM anket WHERE hasta_id=? ORDER BY id DESC LIMIT 1", (self.hasta_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return
        colnames = [d[1] for d in cur.execute("PRAGMA table_info(anket)")]
        data = dict(zip(colnames, row)); conn.close()

        def set_vy(pair, key):
            v = data.get(key)
            if v == "Var": pair[0].setChecked(True)
            elif v == "Yok": pair[1].setChecked(True)

        def set_eh(pair, key):
            v = data.get(key)
            if v == "Evet": pair[0].setChecked(True)
            elif v == "Hayır": pair[1].setChecked(True)

        def set_txt(widget, key):
            val = data.get(key)
            if isinstance(widget, tuple):  # (rb1, rb2, le)
                set_vy((widget[0], widget[1]), key)
                nk = key + "_not" if key + "_not" in data else None
                if nk:
                    widget[2].setText(data.get(nk) or "")
            else:
                if hasattr(widget, "setPlainText"):
                    widget.setPlainText("" if val is None else str(val))
                else:
                    widget.setText("" if val is None else str(val))

        # Ön tanı
        for pair,key in [(self.ates,"ates"),(self.oksuruk,"oksuruk"),(self.gece_terleme,"gece_terleme"),
                         (self.kilo_kaybi,"kilo_kaybi"),(self.aile_tb,"aile_tb"),(self.usye_asye,"usye_asye"),
                         (self.agzi_acik,"agzi_acik"),(self.inhaler,"inhaler"),(self.evneb,"evneb"),
                         (self.cigsut,"cigsut"),(self.oral_aft,"oral_aft"),(self.genital_ulser,"genital_ulser"),
                         (self.romatizma,"romatizma")]:
            set_vy(pair, key)

        self.yasam_yeri.setCurrentText(data.get("yasam_yeri") or "")
        self.evde_kisi.setText("" if data.get("evde_kisi") in (None,"") else str(data.get("evde_kisi")))
        set_vy(self.hayvan[:2], "hayvan"); self.hayvan[2].setText(data.get("hayvan_not") or "")
        self.tekrarlayan.setText(data.get("tekrarlayan") or "")
        set_vy(self.eklem[:2], "eklem"); self.eklem[2].setText(data.get("eklem_not") or "")

        # Özgeçmiş
        for w,k in [(self.hafta,"hafta"),(self.nsvy_cs,"nsvy_cs"),(self.gr,"gr"),(self.asilari,"asilari"),
                    (self.anne_yas,"anne_yas"),(self.anne_ss,"anne_ss"),(self.baba_yas,"baba_yas"),(self.baba_ss,"baba_ss"),
                    (self.cocuk1,"cocuk1"),(self.cocuk2,"cocuk2"),(self.cocuk3,"cocuk3"),(self.cocuk4,"cocuk4")]:
            set_txt(w,k)
        set_eh(self.kuvoz,"kuvoz"); set_eh(self.anne_sutu,"anne_sutu")
        set_vy(self.akrabalik[:2],"akrabalik"); self.akrabalik[2].setText(data.get("akrabalik_not") or "")
        set_vy(self.aile_hastalik[:2],"aile_hastalik"); self.aile_hastalik[2].setText(data.get("aile_hastalik_not") or "")

        # FM
        for w,k in [(self.ta,"ta"),(self.n,"n"),(self.t,"t"),(self.ss,"ss"),(self.boy,"boy"),
                    (self.genel_durum,"genel_durum"),(self.orofarenks,"orofarenks"),(self.servikal,"servikal"),
                    (self.solunum,"solunum"),(self.kalp_not,"kalp_not"),(self.batin_not,"batin_not"),
                    (self.hsm,"hsm"),(self.ense,"ense"),(self.mib,"mib"),(self.dokuntu,"dokuntu")]:
            set_txt(w,k)
        for pair,key in [(self.postnazal,"postnazal"),(self.ufurum,"ufurum")]: set_vy(pair,key)
        set_vy(self.alerji[:2], "alerji"); self.alerji[2].setText(data.get("alerji_not") or "")
        set_vy(self.diyabet[:2], "diyabet"); self.diyabet[2].setText(data.get("diyabet_not") or "")
        set_vy(self.ral[:2], "ral"); self.ral[2].setText(data.get("ral_not") or "")
        set_vy(self.ronkus[:2], "ronkus"); self.ronkus[2].setText(data.get("ronkus_not") or "")
        set_eh(self.kalp_ritim, "kalp_ritim"); set_eh(self.batin, "batin")
        set_txt(self.klinik_gozlem, "klinik_gozlem")

    def kaydet(self):
        V, E = self._v, self._e
        def txt(w):
            if isinstance(w, tuple):
                return (V((w[0],w[1])), w[2].text().strip() or None)
            if hasattr(w, "toPlainText"):
                return w.toPlainText().strip() or None
            return w.text().strip() or None

        # Ön tanı
        ates, oksuruk, gece, kilo = V(self.ates), V(self.oksuruk), V(self.gece_terleme), V(self.kilo_kaybi)
        aile_tb, usye, agzi, inhaler = V(self.aile_tb), V(self.usye_asye), V(self.agzi_acik), V(self.inhaler)
        evneb = V(self.evneb); yasam = self.yasam_yeri.currentText() or None
        evde_kisi = int(self.evde_kisi.text()) if self.evde_kisi.text() else None
        hayvan, hayvan_not = txt(self.hayvan); cigsut, oral, genital = V(self.cigsut), V(self.oral_aft), V(self.genital_ulser)
        tekrarlayan = self.tekrarlayan.text().strip() or None; eklem, eklem_not = txt(self.eklem); rom = V(self.romatizma)

        # Özgeçmiş
        hafta, nsvy_cs, gr = txt(self.hafta), txt(self.nsvy_cs), txt(self.gr)
        kuvoz, anne_sutu = E(self.kuvoz), E(self.anne_sutu)
        asilari = txt(self.asilari); anne_yas, anne_ss = txt(self.anne_yas), txt(self.anne_ss)
        baba_yas, baba_ss = txt(self.baba_yas), txt(self.baba_ss)
        akrabalik, akrabalik_not = txt(self.akrabalik)
        cocuk1, cocuk2, cocuk3, cocuk4 = txt(self.cocuk1), txt(self.cocuk2), txt(self.cocuk3), txt(self.cocuk4)
        aile_hastalik, aile_hastalik_not = txt(self.aile_hastalik)

        # FM
        ta, n, t, ss, boy = txt(self.ta), txt(self.n), txt(self.t), txt(self.ss), txt(self.boy)
        genel = txt(self.genel_durum)
        alerji, alerji_not = txt(self.alerji); diyabet, diyabet_not = txt(self.diyabet)
        orofarenks, postnazal, servikal, solunum = txt(self.orofarenks), V(self.postnazal), txt(self.servikal), txt(self.solunum)
        ral, ral_not = txt(self.ral); ronkus, ronkus_not = txt(self.ronkus)
        kalp_ritim, kalp_not = E(self.kalp_ritim), txt(self.kalp_not)
        ufurum, batin, batin_not = V(self.ufurum), E(self.batin), txt(self.batin_not)
        hsm, ense, mib, dokuntu = V(self.hsm), V(self.ense), V(self.mib), V(self.dokuntu)
        klinik_gozlem = txt(self.klinik_gozlem)

        row = {
            "hasta_id": self.hasta_id, "created_at": QDateTime.currentDateTime().toString(Qt.ISODate),
            "ates":ates,"oksuruk":oksuruk,"gece_terleme":gece,"kilo_kaybi":kilo,"aile_tb":aile_tb,"usye_asye":usye,
            "agzi_acik":agzi,"inhaler":inhaler,"evneb":evneb,"yasam_yeri":yasam,"evde_kisi":evde_kisi,
            "hayvan":hayvan,"hayvan_not":hayvan_not,"cigsut":cigsut,"oral_aft":oral,"genital_ulser":genital,
            "tekrarlayan":tekrarlayan,"eklem":eklem,"eklem_not":eklem_not,"romatizma":rom,
            "hafta":hafta,"nsvy_cs":nsvy_cs,"gr":gr,"kuvoz":kuvoz,"anne_sutu":anne_sutu,"asilari":asilari,
            "anne_yas":anne_yas,"anne_ss":anne_ss,"baba_yas":baba_yas,"baba_ss":baba_ss,
            "akrabalik":akrabalik,"akrabalik_not":akrabalik_not,
            "cocuk1":cocuk1,"cocuk2":cocuk2,"cocuk3":cocuk3,"cocuk4":cocuk4,
            "aile_hastalik":aile_hastalik,"aile_hastalik_not":aile_hastalik_not,
            "ta":ta,"n":n,"t":t,"ss":ss,"boy":boy,"genel_durum":genel,
            "alerji":alerji,"alerji_not":alerji_not,"diyabet":diyabet,"diyabet_not":diyabet_not,
            "orofarenks":orofarenks,"postnazal":postnazal,"servikal":servikal,"solunum":solunum,
            "ral":ral,"ral_not":ral_not,"ronkus":ronkus,"ronkus_not":ronkus_not,
            "kalp_ritim":kalp_ritim,"kalp_not":kalp_not,"ufurum":ufurum,
            "batin":batin,"batin_not":batin_not,"hsm":hsm,"ense":ense,"mib":mib,"dokuntu":dokuntu,
            "klinik_gozlem": klinik_gozlem,
        }
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cols = ",".join(row.keys()); qs = ",".join("?" for _ in row)
        cur.execute(f"INSERT INTO anket({cols}) VALUES ({qs})", list(row.values()))
        conn.commit(); conn.close()
        QMessageBox.information(self, "Kaydedildi", "Anket başarıyla kaydedildi."); self.accept()

# ------------------ Ana Pencere ------------------
class AnaPencere(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Hasta Takip Sistemi - Ana Pencere")

        # Arama toolbar
        self.search_bar = QToolBar("Arama", self); self.addToolBar(Qt.TopToolBarArea, self.search_bar)
        self.search_edit = QLineEdit(self); self.search_edit.setPlaceholderText("TC, ad veya soyad…")
        self.search_edit.returnPressed.connect(self.hasta_ara)
        act_ara = QAction("Ara", self); act_ara.triggered.connect(self.hasta_ara)
        act_tumu = QAction("Tümü", self); act_tumu.triggered.connect(self.hasta_listele)
        self.search_bar.addWidget(self.search_edit); self.search_bar.addAction(act_ara); self.search_bar.addAction(act_tumu)

        # Tablo
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableWidget.setSelectionMode(QTableWidget.SingleSelection)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget.setAlternatingRowColors(True)

        # Butonlar
        if hasattr(self, "btnHastaEkle"): self.btnHastaEkle.clicked.connect(self.hasta_ekle)
        if hasattr(self, "btnHastaSil"): self.btnHastaSil.clicked.connect(self.hasta_sil)
        if hasattr(self, "btnHastaGuncelle"): self.btnHastaGuncelle.clicked.connect(self.hasta_guncelle)
        if hasattr(self, "btnDetayGoster"): self.btnDetayGoster.clicked.connect(self.detay_ac)
        if hasattr(self, "btnAnket"): self.btnAnket.clicked.connect(self.anket_ac)

        self.hasta_listele()

    def _secili_hasta_id(self) -> Optional[int]:
        r = self.tableWidget.currentRow()
        if r < 0:
            return None
        return try_get_int(self.tableWidget.item(r, 0))

    def anket_ac(self):
        hid = self._secili_hasta_id()
        if hid is None:
            QMessageBox.warning(self, "Uyarı", "Anket için hasta seçin!")
            return
        dlg = AnketPenceresi(hid, self)
        dlg.exec_()

    def detay_ac(self):
        hid = self._secili_hasta_id()
        if hid is None:
            QMessageBox.warning(self, "Uyarı", "Detay için hasta seçin!")
            return
        self.detay = DetayPencere(hasta_id=hid)
        self.detay.show()

    def _hasta_tabloyu_doldur(self, rows):
        tw = self.tableWidget
        tw.clear(); tw.setColumnCount(6)
        tw.setHorizontalHeaderLabels(["ID", "TC", "Ad", "Soyad", "Doğum", "Servis"])
        tw.setRowCount(0)
        for row in rows:
            r = tw.rowCount(); tw.insertRow(r)
            for c, val in enumerate(row):
                tw.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
        tw.setColumnHidden(0, True)
        hdr = tw.horizontalHeader(); hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for c in range(1, 6): hdr.setSectionResizeMode(c, QHeaderView.Stretch)

    def hasta_listele(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, tc, ad, soyad, dogum, servis FROM hasta ORDER BY id")
        rows = cur.fetchall(); conn.close(); self._hasta_tabloyu_doldur(rows)

    def hasta_ara(self):
        q = (self.search_edit.text() or "").strip()
        if not q:
            self.hasta_listele(); return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""
            SELECT id, tc, ad, soyad, dogum, servis
            FROM hasta
            WHERE tc LIKE ? OR LOWER(ad) LIKE LOWER(?) OR LOWER(soyad) LIKE LOWER(?)
            ORDER BY id
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
        rows = cur.fetchall(); conn.close(); self._hasta_tabloyu_doldur(rows)

    def hasta_ekle(self):
        dlg = HastaEkleDialog("Yeni Hasta Ekle", self)
        if dlg.exec_() != QDialog.Accepted: return
        tc, ad, soyad, dogum, servis = dlg.get_data()
        if not tc or not ad or not soyad:
            QMessageBox.warning(self, "Uyarı", "TC, Ad ve Soyad boş olamaz!"); return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id FROM hasta WHERE tc=?", (tc,))
        if cur.fetchone():
            conn.close(); QMessageBox.warning(self, "Hata", f"Bu TC ({tc}) ile kayıtlı hasta zaten var!"); return
        cur.execute("INSERT INTO hasta(tc, ad, soyad, dogum, servis) VALUES (?,?,?,?,?)",
                    (tc, ad, soyad, dogum, servis))
        conn.commit(); conn.close(); self.hasta_listele()

    def hasta_sil(self):
        hid = self._secili_hasta_id()
        if hid is None:
            QMessageBox.warning(self, "Uyarı", "Silmek için hasta seçin!"); return
        if QMessageBox.question(self, "Onay", "Seçili hastayı silmek istiyor musunuz?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("DELETE FROM antibiyogram WHERE bakteri_id IN (SELECT id FROM bakteri WHERE hasta_id=?)", (hid,))
        cur.execute("DELETE FROM bakteri WHERE hasta_id=?", (hid,))
        cur.execute("DELETE FROM ilac WHERE hasta_id=?", (hid,))
        cur.execute("DELETE FROM anket WHERE hasta_id=?", (hid,))
        cur.execute("DELETE FROM lab WHERE hasta_id=?", (hid,))
        cur.execute("DELETE FROM hasta WHERE id=?", (hid,))
        conn.commit(); conn.close(); self.hasta_listele()

    def hasta_guncelle(self):
        r = self.tableWidget.currentRow()
        if r < 0: QMessageBox.warning(self, "Uyarı", "Güncellemek için hasta seçin!"); return
        hid = self._secili_hasta_id()
        if hid is None: QMessageBox.warning(self, "Uyarı", "Geçersiz hasta ID!"); return

        tc = self.tableWidget.item(r,1).text() if self.tableWidget.item(r,1) else ""
        ad = self.tableWidget.item(r,2).text() if self.tableWidget.item(r,2) else ""
        soyad = self.tableWidget.item(r,3).text() if self.tableWidget.item(r,3) else ""
        dogum = self.tableWidget.item(r,4).text() if self.tableWidget.item(r,4) else ""
        servis = self.tableWidget.item(r,5).text() if self.tableWidget.item(r,5) else ""

        dlg = HastaEkleDialog("Hasta Güncelle", self)
        dlg.tc_input.setText(tc); dlg.ad_input.setText(ad); dlg.soyad_input.setText(soyad)
        if dogum:
            d = QDate.fromString(dogum, "dd-MM-yyyy")
            if d.isValid(): dlg.dogum_input.setDate(d)
        dlg.servis_input.setText(servis)

        if dlg.exec_() != QDialog.Accepted: return
        yeni_tc, yeni_ad, yeni_soyad, yeni_dogum, yeni_servis = dlg.get_data()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id FROM hasta WHERE tc=? AND id<>?", (yeni_tc, hid))
        if cur.fetchone():
            conn.close(); QMessageBox.warning(self, "Hata", f"Bu TC ({yeni_tc}) başka bir hastada kayıtlı!"); return
        cur.execute("""UPDATE hasta SET tc=?, ad=?, soyad=?, dogum=?, servis=? WHERE id=?""",
                    (yeni_tc, yeni_ad, yeni_soyad, yeni_dogum, yeni_servis, hid))
        conn.commit(); conn.close(); self.hasta_listele(); self.tableWidget.selectRow(r)
        QMessageBox.information(self, "Başarılı", "Hasta bilgileri güncellendi.")

# ------------------ Detay Penceresi ------------------
class DetayPencere(QMainWindow, Ui_DetayPencere):
    BAK_SIRA, BAK_ID, BAK_KULTUR, BAK_AD, BAK_TARIH = 0, 1, 2, 3, 4
    ABG_SIRA, ABG_ID, ABG_AB, ABG_SONUC = 0, 1, 2, 3
    ABX_SIRA, ABX_ID, ABX_ILAC, ABX_BAS, ABX_BIT, ABX_DOZ = 0, 1, 2, 3, 4, 5

    def __init__(self, hasta_id: int):
        super().__init__()
        self.setupUi(self)
        self.hasta_id = int(hasta_id)

        # ----- CASE-INSENSITIVE ALIAS -----
        def _pick_ci(*names):
            all_attrs = dir(self)
            for want in names:
                lw = want.lower()
                for a in all_attrs:
                    if a.lower() == lw:
                        return getattr(self, a)
            return None

        self.tableAntibiyogram = _pick_ci(
            "tableAntibiyogram","tableAntibiyogram_","tableAntibiyogram_2",
            "tableantibiyogram","tableantibiyogram_","tableantibiyogram_2"
        )
        self.cmbAntibiyotik = _pick_ci("cmbAntibiyotik","cmbAntibiyotik_","cmbAntibiyotik_2",
                                       "cmbantibiyotik","cmbantibiyotik_","cmbantibiyotik_2")
        self.cmbSonuc = _pick_ci("cmbSonuc","cmbSonuc_","cmbSonuc_2","cmbsonuc","cmbsonuc_","cmbsonuc_2")
        self.btnAntibiyogramEkle = _pick_ci("btnAntibiyogramEkle","btnAntibiyogramEkle_","btnAntibiyogramEkle_2")
        self.btnAntibiyogramSil = _pick_ci("btnAntibiyogramSil","btnAntibiyogramSil_","btnAntibiyogramSil_2")
        self.btnAntibiyogramGuncelle = _pick_ci("btnAntibiyogramGuncelle","btnAntibiyogramGuncelle","btnAntibiyogramGuncelle_2")

        # Başlık
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT ad, soyad FROM hasta WHERE id=?", (self.hasta_id,))
        h = cur.fetchone(); conn.close()
        self.setWindowTitle(f"Hasta Detayları - ID {self.hasta_id} - {h[0]} {h[1]}" if h else f"Hasta Detayları - ID {self.hasta_id}")

        # Bakteri tablosu
        t = self.tableBakteri
        if t.columnCount() < 5: t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["", "ID", "Kültür Örneği", "Bakteri Adı", "Üreme Tarihi"])
        t.verticalHeader().setVisible(False); t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QTableWidget.SelectRows); t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setColumnHidden(self.BAK_ID, True)
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(self.BAK_SIRA, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.BAK_KULTUR, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.BAK_AD, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.BAK_TARIH, QHeaderView.ResizeToContents)

        # Antibiyogram tablosu
        if self.tableAntibiyogram:
            t = self.tableAntibiyogram
            if t.columnCount() < 4: t.setColumnCount(4)
            t.setHorizontalHeaderLabels(["", "ID", "Antibiyotik", "Sonuç"])
            t.verticalHeader().setVisible(False); t.setAlternatingRowColors(True)
            t.setSelectionBehavior(QTableWidget.SelectRows); t.setEditTriggers(QTableWidget.NoEditTriggers)
            t.setColumnHidden(self.ABG_ID, True)
            hdr = t.horizontalHeader()
            hdr.setSectionResizeMode(self.ABG_SIRA, QHeaderView.ResizeToContents)
            hdr.setSectionResizeMode(self.ABG_AB, QHeaderView.Stretch)
            hdr.setSectionResizeMode(self.ABG_SONUC, QHeaderView.Stretch)

        # İlaç tablosu
        t = self.tableilac
        if t.columnCount() < 6: t.setColumnCount(6)
        t.setHorizontalHeaderLabels(["", "ID", "İlaç", "Başlangıç", "Bitiş", "Dozaj"])
        t.verticalHeader().setVisible(False); t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QTableWidget.SelectRows); t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setColumnHidden(self.ABX_ID, True)
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(self.ABX_SIRA, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.ABX_ILAC, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.ABX_BAS, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.ABX_BIT, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.ABX_DOZ, QHeaderView.Stretch)

        # Butonlar
        if hasattr(self, "btnBakteriEkle"): self.btnBakteriEkle.clicked.connect(self.bakteri_ekle)
        if hasattr(self, "btnBakteriSil"): self.btnBakteriSil.clicked.connect(self.bakteri_sil)
        if hasattr(self, "btnBakteriGuncelle"): self.btnBakteriGuncelle.clicked.connect(self.bakteri_guncelle)
        if self.btnAntibiyogramEkle: self.btnAntibiyogramEkle.clicked.connect(self.antibiyogram_ekle)
        if self.btnAntibiyogramSil: self.btnAntibiyogramSil.clicked.connect(self.antibiyogram_sil)
        if self.btnAntibiyogramGuncelle: self.btnAntibiyogramGuncelle.clicked.connect(self.antibiyogram_guncelle)
        if hasattr(self, "btnilac_ekle"): self.btnilac_ekle.clicked.connect(self.ilac_ekle)
        if hasattr(self, "btnilac_sil"): self.btnilac_sil.clicked.connect(self.ilac_sil)
        if hasattr(self, "btnilac_guncelle"): self.btnilac_guncelle.clicked.connect(self.ilac_guncelle)

        # Yazdır butonu + Ctrl+P aynı işlev
        self._wire_print_controls()

        self.tableBakteri.cellClicked.connect(self.bakteri_secildi)
        self.listele_bakteri()
        self.listele_ilac()

        # Laboratuvar
        self.btnLabKaydet = getattr(self, "btnLabKaydet", None)
        self.btnLabYukle  = getattr(self, "btnLabYukle", None)
        if self.btnLabKaydet: self.btnLabKaydet.clicked.connect(self.lab_kaydet)
        if self.btnLabYukle:  self.btnLabYukle.clicked.connect(self.lab_son_kaydi_yukle)

        from PyQt5.QtGui import QDoubleValidator
        def _val(*names):
            for n in names:
                w = getattr(self, n, None)
                if w: w.setValidator(QDoubleValidator(-1e6, 1e6, 3))
        _val("le_crp","le_lokosit","le_lenfosit","le_notrofil","le_pct",
             "le_glukoz","le_na","le_cl","le_p","le_mg",
             "le_ast","le_alt","le_ggt","le_alp","le_tbil","le_dbil","le_albumin",
             "le_kreatinin","le_bun","le_egfrt")

        # --- ÖNEMLİ: açılışta son lab kaydını yükle
        self._lab_loading = False
        self.lab_son_kaydi_yukle(show_message=False)

    # --- Yazdır bağlama ---
    def _wire_print_controls(self):
        # Global QAction (Ctrl+P)
        if not hasattr(self, "_printAction"):
            self._printAction = QAction("Yazdır", self)
            self._printAction.setShortcut(QKeySequence.Print)
            self._printAction.triggered.connect(self.yazdir_rapor)
            self.addAction(self._printAction)

        candidate_names = {
            "btnExportCSV", "btnYazdir", "pushButtonYazdir", "pushButtonPrint", "btnPrint"
        }
        candidate_text_tokens = ("yazdır", "yazdir", "print")

        def is_print_button(btn: QAbstractButton) -> bool:
            name = (btn.objectName() or "").lower()
            text = (btn.text() or "").lower()
            if name in {n.lower() for n in candidate_names}:
                return True
            return any(tok in text for tok in candidate_text_tokens)

        for btn in self.findChildren(QAbstractButton):
            if is_print_button(btn):
                try:
                    btn.clicked.disconnect()  # eski bağlantıları kes
                except Exception:
                    pass
                btn.clicked.connect(self.yazdir_rapor)
                btn.setShortcut(QKeySequence.Print)
                if (btn.text() or "").strip() == "" or "csv" in (btn.text() or "").lower():
                    btn.setText("Yazdır")
                if not (btn.toolTip() or ""):
                    btn.setToolTip("Raporu yazdır (Ctrl+P)")

    # --- Yardımcı metodlar ---
    def _table_exists(self, cur, name: str) -> bool:
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    def _q(self, cur, sql, params=()):
        cur.execute(sql, params)
        return cur.fetchall()

    # --- Olaylar / Listeleme ---
    def bakteri_secildi(self, row: int, _col: int):
        it = self.tableBakteri.item(row, self.BAK_ID)
        if it: self.listele_antibiyogram(it.text())

    def listele_bakteri(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""SELECT id, kultur_ornegi, isim, ureme_tarihi FROM bakteri WHERE hasta_id=?""", (self.hasta_id,))
        rows = cur.fetchall(); conn.close()
        t = self.tableBakteri; t.setRowCount(0)
        for sira, (bid, kultur, ad, tarih) in enumerate(rows, start=1):
            r = t.rowCount(); t.insertRow(r)
            t.setItem(r, self.BAK_SIRA, QTableWidgetItem(str(sira))); t.item(r, self.BAK_SIRA).setTextAlignment(Qt.AlignCenter)
            t.setItem(r, self.BAK_ID, QTableWidgetItem(str(bid)))
            t.setItem(r, self.BAK_KULTUR, QTableWidgetItem(kultur or ""))
            t.setItem(r, self.BAK_AD, QTableWidgetItem(ad or ""))
            t.setItem(r, self.BAK_TARIH, QTableWidgetItem(tarih or "")); t.item(r, self.BAK_TARIH).setTextAlignment(Qt.AlignCenter)
        if rows:
            t.selectRow(0); self.listele_antibiyogram(str(rows[0][0]))
        else:
            if self.tableAntibiyogram: self.tableAntibiyogram.setRowCount(0)

    def listele_antibiyogram(self, bakteri_id: str):
        if not self.tableAntibiyogram: return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, antibiyotik, sonuc FROM antibiyogram WHERE bakteri_id=? ORDER BY id", (bakteri_id,))
        rows = cur.fetchall(); conn.close()
        t = self.tableAntibiyogram; t.setRowCount(0)
        for sira, (aid, ab, sonuc) in enumerate(rows, start=1):
            r = t.rowCount(); t.insertRow(r)
            t.setItem(r, self.ABG_SIRA, QTableWidgetItem(str(sira)))
            t.setItem(r, self.ABG_ID, QTableWidgetItem(str(aid)))
            t.setItem(r, self.ABG_AB, QTableWidgetItem(ab or ""))
            t.setItem(r, self.ABG_SONUC, QTableWidgetItem(sonuc or ""))
            t.item(r, self.ABG_SIRA).setTextAlignment(Qt.AlignCenter)
            t.item(r, self.ABG_SONUC).setTextAlignment(Qt.AlignCenter)

    def listele_ilac(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""SELECT id, ilac, baslangic, bitis, dozaj FROM ilac
                       WHERE hasta_id=? ORDER BY id""", (self.hasta_id,))
        rows = cur.fetchall(); conn.close()
        t = self.tableilac; t.setRowCount(0)
        for sira, (kid, ad, bas, bit, doz) in enumerate(rows, start=1):
            r = t.rowCount(); t.insertRow(r)
            t.setItem(r, self.ABX_SIRA, QTableWidgetItem(str(sira)))
            t.setItem(r, self.ABX_ID, QTableWidgetItem(str(kid)))
            t.setItem(r, self.ABX_ILAC, QTableWidgetItem(ad or ""))
            t.setItem(r, self.ABX_BAS, QTableWidgetItem(bas or ""))
            t.setItem(r, self.ABX_BIT, QTableWidgetItem(bit or ""))
            t.setItem(r, self.ABX_DOZ, QTableWidgetItem(doz or ""))
            t.item(r, self.ABX_SIRA).setTextAlignment(Qt.AlignCenter)
            t.item(r, self.ABX_BAS).setTextAlignment(Qt.AlignCenter)
            t.item(r, self.ABX_BIT).setTextAlignment(Qt.AlignCenter)

    # --- Ekle / Sil / Güncelle ---
    def bakteri_ekle(self):
        dlg = BakteriEkleDialog("Bakteri Ekle")
        if dlg.exec_() != QDialog.Accepted: return
        kultur, ad, tarih = dlg.get_data()
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Bakteri adı boş olamaz!"); return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("INSERT INTO bakteri(kultur_ornegi, isim, ureme_tarihi, hasta_id) VALUES (?,?,?,?)",
                    (kultur, ad, tarih, self.hasta_id))
        conn.commit(); conn.close(); self.listele_bakteri()

    def bakteri_sil(self):
        r = self.tableBakteri.currentRow()
        if r < 0: QMessageBox.warning(self, "Uyarı", "Silmek için bakteri seçin!"); return
        bid = self.tableBakteri.item(r, self.BAK_ID).text()
        if QMessageBox.question(self, "Onay", "Seçili bakteriyi silmek istiyor musunuz?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes: return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("DELETE FROM antibiyogram WHERE bakteri_id=?", (bid,))
        cur.execute("DELETE FROM bakteri WHERE id=?", (bid,))
        conn.commit(); conn.close(); self.listele_bakteri()
        if self.tableAntibiyogram: self.tableAntibiyogram.setRowCount(0)

    def bakteri_guncelle(self):
        r = self.tableBakteri.currentRow()
        if r < 0: QMessageBox.warning(self, "Uyarı", "Güncellemek için bakteri seçin!"); return
        bid = self.tableBakteri.item(r, self.BAK_ID).text()
        kultur = self.tableBakteri.item(r, self.BAK_KULTUR).text()
        isim = self.tableBakteri.item(r, self.BAK_AD).text()
        tarih = self.tableBakteri.item(r, self.BAK_TARIH).text()
        dlg = BakteriEkleDialog("Bakteri Güncelle")
        dlg.kultur_input.setCurrentText(kultur); dlg.bakteri_input.setText(isim)
        if tarih:
            d = QDate.fromString(tarih, "dd-MM-yyyy")
            if not d.isValid(): d = QDate.fromString(tarih, "yyyy-MM-dd")
            if d.isValid(): dlg.tarih_input.setDate(d)
        if dlg.exec_() != QDialog.Accepted: return
        yeni_kultur, yeni_isim, yeni_tarih = dlg.get_data()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE bakteri SET kultur_ornegi=?, isim=?, ureme_tarihi=? WHERE id=?",
                    (yeni_kultur, yeni_isim, yeni_tarih, bid))
        conn.commit(); conn.close(); self.listele_bakteri()

    def antibiyogram_ekle(self):
        row = self.tableBakteri.currentRow()
        if row < 0: QMessageBox.warning(self, "Uyarı", "Önce bir bakteri seçin!"); return
        bid = self.tableBakteri.item(row, self.BAK_ID).text()
        if self.cmbAntibiyotik and self.cmbSonuc:
            ab = self.cmbAntibiyotik.currentText()
            sonuc = self.cmbSonuc.currentText()
        else:
            d = AntibiyogramEkleDialog("Antibiyogram Ekle")
            if d.exec_() != QDialog.Accepted: return
            ab, sonuc = d.get_data()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("INSERT INTO antibiyogram (bakteri_id, antibiyotik, sonuc) VALUES (?,?,?)", (bid, ab, sonuc))
        conn.commit(); conn.close(); self.listele_antibiyogram(bid)

    def antibiyogram_sil(self):
        if not self.tableAntibiyogram: return
        r = self.tableAntibiyogram.currentRow()
        if r < 0: QMessageBox.warning(self, "Uyarı", "Silmek için antibiyogram seçin!"); return
        abid = self.tableAntibiyogram.item(r, self.ABG_ID).text()
        br = self.tableBakteri.currentRow()
        if br < 0: return
        bid = self.tableBakteri.item(br, self.BAK_ID).text()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("DELETE FROM antibiyogram WHERE id=?", (abid,))
        conn.commit(); conn.close(); self.listele_antibiyogram(bid)

    def antibiyogram_guncelle(self):
        if not self.tableAntibiyogram: return
        r = self.tableAntibiyogram.currentRow()
        if r < 0: QMessageBox.warning(self, "Uyarı", "Güncellemek için antibiyogram seçin!"); return
        abid = self.tableAntibiyogram.item(r, self.ABG_ID).text()
        ab = self.tableAntibiyogram.item(r, self.ABG_AB).text()
        sonuc = self.tableAntibiyogram.item(r, self.ABG_SONUC).text()
        dlg = AntibiyogramEkleDialog("Antibiyogram Güncelle"); dlg.antibiyotik_input.setText(ab)
        idx = dlg.sonuc_input.findText(sonuc)
        if idx >= 0: dlg.sonuc_input.setCurrentIndex(idx)
        if dlg.exec_() != QDialog.Accepted: return
        yeni_ab, yeni_sonuc = dlg.get_data()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE antibiyogram SET antibiyotik=?, sonuc=? WHERE id=?", (yeni_ab, yeni_sonuc, abid))
        conn.commit(); conn.close()
        br = self.tableBakteri.currentRow()
        if br >= 0:
            bid = self.tableBakteri.item(br, self.BAK_ID).text()
            self.listele_antibiyogram(bid)

    def ilac_ekle(self):
        dlg = IlacEkleDialog("İlaç Ekle")
        if dlg.exec_() != QDialog.Accepted: return
        ilac, bas, bit, doz = dlg.get_data()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""INSERT INTO ilac(ilac, baslangic, bitis, dozaj, hasta_id)
                       VALUES (?,?,?,?,?)""", (ilac, bas, bit, doz, self.hasta_id))
        conn.commit(); conn.close(); self.listele_ilac()

    def ilac_sil(self):
        r = self.tableilac.currentRow()
        if r < 0: QMessageBox.warning(self, "Uyarı", "Silmek için ilaç seçin!"); return
        ilac_id = self.tableilac.item(r, self.ABX_ID).text()
        if QMessageBox.question(self, "Onay", "Seçili kaydı silmek istiyor musunuz?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes: return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("DELETE FROM ilac WHERE id=?", (ilac_id,))
        conn.commit(); conn.close(); self.listele_ilac()

    def ilac_guncelle(self):
        r = self.tableilac.currentRow()
        if r < 0: QMessageBox.warning(self, "Uyarı", "Güncellemek için bir kayıt seçin!"); return
        ilac_id = self.tableilac.item(r, self.ABX_ID).text()
        ilac = self.tableilac.item(r, self.ABX_ILAC).text()
        bas = self.tableilac.item(r, self.ABX_BAS).text()
        bit = self.tableilac.item(r, self.ABX_BIT).text()
        doz = self.tableilac.item(r, self.ABX_DOZ).text()
        dlg = IlacEkleDialog("İlaç Güncelle"); dlg.ilac_input.setText(ilac)
        if bas:
            d = QDate.fromString(bas, "dd-MM-yyyy")
            if not d.isValid(): d = QDate.fromString(bas, "yyyy-MM-dd")
            if d.isValid(): dlg.baslangic_input.setDate(d)
        if bit:
            d = QDate.fromString(bit, "dd-MM-yyyy")
            if not d.isValid(): d = QDate.fromString(bit, "yyyy-MM-dd")
            if d.isValid(): dlg.bitis_input.setDate(d)
        dlg.dozaj_input.setText(doz)
        if dlg.exec_() != QDialog.Accepted: return
        yeni_ilac, yeni_bas, yeni_bit, yeni_doz = dlg.get_data()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""UPDATE ilac
                       SET ilac=?, baslangic=?, bitis=?, dozaj=? WHERE id=?""",
                    (yeni_ilac, yeni_bas, yeni_bit, yeni_doz, ilac_id))
        conn.commit(); conn.close(); self.listele_ilac()

    # --------- Laboratuvar yardımcı/kaydet/yükle ---------
    def lab_kaydet(self):
        G = lambda name: getattr(self, name, None)
        def num(w):
            if not w:
                return None
            try:
                t = w.text().strip().replace(",", ".")
                return None if t == "" else float(t)
            except Exception:
                return None

        row = {
            "hasta_id": self.hasta_id,
            "created_at": QDateTime.currentDateTime().toString(Qt.ISODate),
            "ppd": (G("le_ppd").text().strip() if G("le_ppd") else None),
            "crp":       num(G("le_crp")),
            "lokosit":   num(G("le_lokosit")),
            "lenfosit":  num(G("le_lenfosit")),
            "notrofil":  num(G("le_notrofil")),
            "pct":       num(G("le_pct")),
            "glukoz":    num(G("le_glukoz")),
            "na":        num(G("le_na")),
            "cl":        num(G("le_cl")),
            "p":         num(G("le_p")),
            "mg":        num(G("le_mg")),
            "ast":       num(G("le_ast")),
            "alt":       num(G("le_alt")),
            "ggt":       num(G("le_ggt")),
            "alp":       num(G("le_alp")),
            "tbil":      num(G("le_tbil")),
            "dbil":      num(G("le_dbil")),
            "albumin":   num(G("le_albumin")),
            "kreatinin": num(G("le_kreatinin")),
            "bun":       num(G("le_bun")),
            "egfrt":     num(G("le_egfrt")),
        }

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cols = ",".join(row.keys())
            qs = ",".join("?" for _ in row)
            cur.execute(f"INSERT INTO lab({cols}) VALUES({qs})", list(row.values()))
            conn.commit()
        except Exception as e:
            if conn:
                try: conn.rollback()
                except: pass
            QMessageBox.critical(self, "Hata", f"Kayıt başarısız:\n{e}")
            return
        finally:
            if conn:
                try: conn.close()
                except: pass
        self.lab_son_kaydi_yukle(show_message=False)
        QMessageBox.information(self, "Kaydedildi", "Laboratuvar verileri kaydedildi.")

    def lab_son_kaydi_yukle(self, show_message=True):
        # re-entrancy guard
        if getattr(self, "_lab_loading", False):
            return
        self._lab_loading = True
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT * FROM lab WHERE hasta_id=? ORDER BY id DESC LIMIT 1", (self.hasta_id,))
            row = cur.fetchone()
            cols = [d[1] for d in cur.execute("PRAGMA table_info(lab)")]
            conn.close()

            if not row:
                if show_message:
                    QMessageBox.information(self, "Bilgi", "Bu hasta için laboratuvar kaydı bulunamadı.")
                return

            data = dict(zip(cols, row))

            def setv(obj, key):
                w = getattr(self, obj, None)
                if w is not None:
                    v = data.get(key)
                    w.setText("" if v is None else str(v))

            setv("le_ppd", "ppd")
            for obj, key in [
                ("le_crp","crp"),("le_lokosit","lokosit"),("le_lenfosit","lenfosit"),
                ("le_notrofil","notrofil"),("le_pct","pct"),
                ("le_glukoz","glukoz"),("le_na","na"),("le_cl","cl"),("le_p","p"),("le_mg","mg"),
                ("le_ast","ast"),("le_alt","alt"),("le_ggt","ggt"),("le_alp","alp"),
                ("le_tbil","tbil"),("le_dbil","dbil"),("le_albumin","albumin"),
                ("le_kreatinin","kreatinin"),("le_bun","bun"),("le_egfrt","egfrt"),
            ]:
                setv(obj, key)
        finally:
            self._lab_loading = False

    # --------- CSV ve YAZDIR ---------
    def yazdir_rapor(self):
        import html
        hid = int(self.hasta_id)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Hasta
        cur.execute("SELECT id, tc, ad, soyad, dogum, servis FROM hasta WHERE id=?", (hid,))
        h = cur.fetchone()
        if not h:
            QMessageBox.warning(self, "Uyarı", "Hasta bulunamadı!")
            conn.close()
            return
        h_id, tc, ad, soyad, dogum, servis = h

        # Son Anket (varsa)
        last_anket = None; anket_cols = []
        if self._table_exists(cur, "anket"):
            cur.execute("SELECT * FROM anket WHERE hasta_id=? ORDER BY id DESC LIMIT 1", (hid,))
            last_anket = cur.fetchone()
            anket_cols = [d[1] for d in cur.execute("PRAGMA table_info(anket)")]

        # Son Lab (varsa)
        last_lab = None; lab_cols = []
        if self._table_exists(cur, "lab"):
            cur.execute("SELECT * FROM lab WHERE hasta_id=? ORDER BY id DESC LIMIT 1", (hid,))
            last_lab = cur.fetchone()
            lab_cols = [d[1] for d in cur.execute("PRAGMA table_info(lab)")]

        # Bakteriler
        cur.execute("SELECT id, isim, ureme_tarihi FROM bakteri WHERE hasta_id=? ORDER BY id", (hid,))
        bakteriler = cur.fetchall()

        # İlaçlar
        cur.execute("""SELECT ilac, baslangic, bitis, dozaj
                       FROM ilac
                       WHERE hasta_id=?
                       ORDER BY id""", (hid,))
        ilaclar = cur.fetchall()

        # HTML
        esc = html.escape
        html_parts = []
        html_parts.append(f"""
        <h2>Hasta Raporu</h2>
        <p><b>ID:</b> {h_id} &nbsp; <b>TC:</b> {esc(tc or '')}</p>
        <p><b>Ad Soyad:</b> {esc(ad or '')} {esc(soyad or '')}</p>
        <p><b>Doğum:</b> {esc(dogum or '')} &nbsp; <b>Servis:</b> {esc(servis or '')}</p>
        <hr/>
        """)

        if last_anket:
            html_parts.append("<h3>Son Anket</h3><table border='1' cellspacing='0' cellpadding='4'>")
            for col, val in zip(anket_cols, last_anket):
                html_parts.append(f"<tr><td><b>{esc(col)}</b></td><td>{esc(str(val) if val is not None else '')}</td></tr>")
            html_parts.append("</table><br/>")

        if last_lab:
            html_parts.append("<h3>Son Laboratuvar</h3><table border='1' cellspacing='0' cellpadding='4'>")
            for col, val in zip(lab_cols, last_lab):
                html_parts.append(f"<tr><td><b>{esc(col)}</b></td><td>{esc(str(val) if val is not None else '')}</td></tr>")
            html_parts.append("</table><br/>")

        html_parts.append("<h3>Bakteriler &amp; Antibiyogram</h3>")
        if not bakteriler:
            html_parts.append("<p>Kayıt yok.</p>")
        else:
            for bid, b_ad, b_tarih in bakteriler:
                html_parts.append(
                    f"<p><b>Bakteri:</b> {esc(b_ad or '')} &nbsp; "
                    f"<b>Üreme Tarihi:</b> {esc(b_tarih or '')} &nbsp; "
                    f"<b>ID:</b> {bid}</p>"
                )
                cur.execute(
                    "SELECT antibiyotik, sonuc FROM antibiyogram WHERE bakteri_id=? ORDER BY id",
                    (bid,)
                )
                abgs = cur.fetchall()
                if abgs:
                    html_parts.append(
                        "<table border='1' cellspacing='0' cellpadding='4'>"
                        "<tr><th>Antibiyotik</th><th>Sonuç</th></tr>"
                    )
                    for ab, snc in abgs:
                        html_parts.append(f"<tr><td>{esc(ab or '')}</td><td>{esc(snc or '')}</td></tr>")
                    html_parts.append("</table><br/>")
                else:
                    html_parts.append("<p style='margin-left:12px;'>Antibiyogram yok.</p>")

        html_parts.append("<h3>Kullanılan İlaçlar</h3>")
        if ilaclar:
            html_parts.append(
                "<table border='1' cellspacing='0' cellpadding='4'>"
                "<tr><th>İlaç</th><th>Başlangıç</th><th>Bitiş</th><th>Dozaj</th></tr>"
            )
            for ilac, bas, bit, doz in ilaclar:
                html_parts.append(
                    f"<tr><td>{esc(ilac or '')}</td>"
                    f"<td>{esc(bas or '')}</td>"
                    f"<td>{esc(bit or '')}</td>"
                    f"<td>{esc(doz or '')}</td></tr>"
                )
            html_parts.append("</table>")
        else:
            html_parts.append("<p>İlaç kaydı yok.</p>")

        html_str = "".join(html_parts)

        # Varsayılan dosya adı: AD_SOYAD_rapor.pdf
        def safe(s):
            s = (s or "").strip()
            if not s:
                return ""
            keep = []
            for ch in s:
                if ch.isalnum() or ch in (" ", "_", "-"):
                    keep.append(ch)
            return "".join(keep).strip().replace(" ", "_")

        default_name = f"{safe(ad)}_{safe(soyad)}_rapor.pdf".strip("_")
        if not default_name or default_name == "_rapor.pdf":
            default_name = f"hasta_{h_id}_rapor.pdf"

        btn = QMessageBox.question(
            self, "Yazdır",
            "PDF olarak kaydetmek ister misin?\n(No: Yazıcı açılır.)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if btn == QMessageBox.Yes:
            path, _ = QFileDialog.getSaveFileName(self, "PDF kaydet", default_name, "PDF (*.pdf)")
            if not path:
                conn.close()
                return
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            doc = QTextDocument(); doc.setHtml(html_str); doc.print_(printer)
            QMessageBox.information(self, "Tamam", f"PDF kaydedildi:\n{path}")
        else:
            printer = QPrinter(QPrinter.HighResolution)
            dlg = QPrintDialog(printer, self)
            if dlg.exec_() == QPrintDialog.Accepted:
                doc = QTextDocument(); doc.setHtml(html_str); doc.print_(printer)

        conn.close()

# ------------------ Main ------------------
if __name__ == "__main__":
    veritabani_olustur()
    app = QApplication(sys.argv)
    w = AnaPencere()
    w.show()
    sys.exit(app.exec_())
