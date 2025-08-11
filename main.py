import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox, QTableWidgetItem,
    QDateEdit, QComboBox, QHeaderView, QTableWidget
)
import csv
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from ana_pencere import Ui_MainWindow
from detay_pencere import Ui_MainWindow as Ui_DetayPencere

DB_PATH = "hastatakip.db"

def basliklari_kalin_yap(table):
    font = QFont()
    font.setBold(True)
    for i in range(table.columnCount()):
        item = table.horizontalHeaderItem(i)
        if item:
            item.setFont(font)

# ------------------ Veritabanı ------------------
def veritabani_olustur():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS hasta(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tc TEXT UNIQUE,
        ad TEXT,
        soyad TEXT,
        dogum TEXT,
        servis TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS bakteri(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isim TEXT,
        ureme_tarihi TEXT,
        hasta_id INTEGER,
        FOREIGN KEY(hasta_id) REFERENCES hasta(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS antibiyogram(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        antibiyotik TEXT,
        sonuc TEXT,
        bakteri_id INTEGER,
        FOREIGN KEY(bakteri_id) REFERENCES bakteri(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS kullanilan_antibiyotik(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        antibiyotik TEXT,
        baslangic TEXT,
        bitis TEXT,
        dozaj TEXT,
        hasta_id INTEGER,
        FOREIGN KEY(hasta_id) REFERENCES hasta(id)
    )""")
    conn.commit()
    conn.close()

# ------------------ Dialoglar ------------------
class HastaEkleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hasta")
        f = QFormLayout(self)
        self.tc_input = QLineEdit()
        self.ad_input = QLineEdit()
        self.soyad_input = QLineEdit()
        self.dogum_input = QDateEdit()
        self.dogum_input.setCalendarPopup(True)
        self.dogum_input.setDate(QDate.currentDate())
        self.servis_input = QLineEdit()
        f.addRow("TC Kimlik:", self.tc_input)
        f.addRow("Ad:", self.ad_input)
        f.addRow("Soyad:", self.soyad_input)
        f.addRow("Doğum Tarihi:", self.dogum_input)
        f.addRow("Servis:", self.servis_input)
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self.accept)
        btn.rejected.connect(self.reject)
        f.addWidget(btn)

    def get_data(self):
        return (
            self.tc_input.text().strip(),
            self.ad_input.text().strip(),
            self.soyad_input.text().strip(),
            self.dogum_input.date().toString("dd-MM-yyyy"),
            self.servis_input.text().strip(),
        )

class BakteriEkleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bakteri")
        f = QFormLayout(self)
        self.bakteri_input = QLineEdit()
        self.tarih_input = QDateEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDate(QDate.currentDate())
        f.addRow("Bakteri Adı:", self.bakteri_input)
        f.addRow("Üreme Tarihi:", self.tarih_input)
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self.accept)
        btn.rejected.connect(self.reject)
        f.addWidget(btn)

    def get_data(self):
        return (
            self.bakteri_input.text().strip(),
            self.tarih_input.date().toString("dd-MM-yyyy"),
        )

class AntibiyogramEkleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Antibiyogram")
        f = QFormLayout(self)
        self.antibiyotik_input = QLineEdit()
        self.sonuc_input = QComboBox()
        self.sonuc_input.addItems(["Duyarlı", "Orta Duyarlı", "Dirençli"])
        f.addRow("Antibiyotik:", self.antibiyotik_input)
        f.addRow("Sonuç:", self.sonuc_input)
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self.accept)
        btn.rejected.connect(self.reject)
        f.addWidget(btn)

    def get_data(self):
        return (self.antibiyotik_input.text().strip(), self.sonuc_input.currentText())

class AntibiyotikEkleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kullanılan Antibiyotik")
        f = QFormLayout(self)
        self.antibiyotik_input = QLineEdit()
        self.baslangic_input = QDateEdit()
        self.baslangic_input.setCalendarPopup(True)
        self.baslangic_input.setDate(QDate.currentDate())
        self.bitis_input = QDateEdit()
        self.bitis_input.setCalendarPopup(True)
        self.bitis_input.setDate(QDate.currentDate())
        self.dozaj_input = QLineEdit()
        f.addRow("Ad:", self.antibiyotik_input)
        f.addRow("Başlangıç:", self.baslangic_input)
        f.addRow("Bitiş:", self.bitis_input)
        f.addRow("Dozaj:", self.dozaj_input)
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self.accept)
        btn.rejected.connect(self.reject)
        f.addWidget(btn)

    def get_data(self):
        return (
            self.antibiyotik_input.text().strip(),
            self.baslangic_input.date().toString("dd-MM-yyyy"),
            self.bitis_input.date().toString("dd-MM-yyyy"),
            self.dozaj_input.text().strip(),
        )

# ------------------ Ana Pencere ------------------
class AnaPencere(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Hasta Takip Sistemi - Ana Pencere")
        basliklari_kalin_yap(self.tableWidget)
        self.tableWidget.setAlternatingRowColors(True)

        
        # Başlıklar
        self.tableWidget.setHorizontalHeaderLabels(
            ["ID", "TC", "Ad", "Soyad", "Doğum Tarihi", "Servis"]
        )
        self.tableWidget.verticalHeader().setVisible(False)

        # TÜM sütunları eşit paylaştır
        hdr = self.tableWidget.horizontalHeader()
        for i in range(6):
            hdr.setSectionResizeMode(i, QHeaderView.Stretch)

        # Butonlar
        self.btnHastaEkle.clicked.connect(self.hasta_ekle)
        self.btnHastaSil.clicked.connect(self.hasta_sil)
        self.btnHastaGuncelle.clicked.connect(self.hasta_guncelle)
        self.btnDetayGoster.clicked.connect(self.detay_ac)

        self.hasta_listele()

    def hasta_listele(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, tc, ad, soyad, dogum, servis FROM hasta")
        rows = cur.fetchall()
        conn.close()

        self.tableWidget.setRowCount(0)
        for row_data in rows:
            r = self.tableWidget.rowCount()
            self.tableWidget.insertRow(r)
            for c, val in enumerate(row_data):
                self.tableWidget.setItem(r, c, QTableWidgetItem(str(val)))

    def hasta_ekle(self):
        dlg = HastaEkleDialog()
        if dlg.exec_() != QDialog.Accepted:
            return
        tc, ad, soyad, dogum, servis = dlg.get_data()
        if not tc or not ad or not soyad:
            QMessageBox.warning(self, "Uyarı", "TC, Ad ve Soyad boş olamaz!")
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT 1 FROM hasta WHERE tc=?", (tc,))
        if c.fetchone():
            conn.close()
            QMessageBox.warning(self, "Hata", f"Bu TC ({tc}) zaten kayıtlı!")
            return
        c.execute("INSERT INTO hasta(tc, ad, soyad, dogum, servis) VALUES(?,?,?,?,?)",
                  (tc, ad, soyad, dogum, servis))
        conn.commit()
        conn.close()
        self.hasta_listele()

    def hasta_sil(self):
        row = self.tableWidget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için hasta seçin!")
            return
        hasta_id = self.tableWidget.item(row, 0).text()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM hasta WHERE id=?", (hasta_id,))
        conn.commit()
        conn.close()
        self.hasta_listele()

    def hasta_guncelle(self):
        row = self.tableWidget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için hasta seçin!")
            return
        hasta_id = int(self.tableWidget.item(row, 0).text())
        tc     = self.tableWidget.item(row, 1).text()
        ad     = self.tableWidget.item(row, 2).text()
        soyad  = self.tableWidget.item(row, 3).text()
        dogum  = self.tableWidget.item(row, 4).text()
        servis = self.tableWidget.item(row, 5).text()

        dlg = HastaEkleDialog()
        dlg.setWindowTitle("Hasta Güncelle")
        dlg.tc_input.setText(tc)
        dlg.ad_input.setText(ad)
        dlg.soyad_input.setText(soyad)
        if dogum:
            dlg.dogum_input.setDate(QDate.fromString(dogum, "dd-MM-yyyy"))
        dlg.servis_input.setText(servis)
        if dlg.exec_() != QDialog.Accepted:
            return
        yeni_tc, yeni_ad, yeni_soyad, yeni_dogum, yeni_servis = dlg.get_data()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT 1 FROM hasta WHERE tc=? AND id<>?", (yeni_tc, hasta_id))
        if c.fetchone():
            conn.close()
            QMessageBox.warning(self, "Hata", f"Bu TC ({yeni_tc}) başka bir hastada kayıtlı!")
            return
        c.execute("""UPDATE hasta SET tc=?, ad=?, soyad=?, dogum=?, servis=? WHERE id=?""",
                  (yeni_tc, yeni_ad, yeni_soyad, yeni_dogum, yeni_servis, hasta_id))
        conn.commit()
        conn.close()
        self.hasta_listele()
        self.tableWidget.selectRow(row)

    def detay_ac(self):
        row = self.tableWidget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Detay için hasta seçin!")
            return
        hasta_id = self.tableWidget.item(row, 0).text()
        self.detay = DetayPencere(hasta_id)
        self.detay.show()

# ------------------ Detay Penceresi ------------------
class DetayPencere(QMainWindow, Ui_DetayPencere):
    def __init__(self, hasta_id):
        super().__init__()
        self.setupUi(self)
        basliklari_kalin_yap(self.tableBakteri)
        basliklari_kalin_yap(self.tableAntibiyogram)
        basliklari_kalin_yap(self.tableKullanilanAntibiyotik)
        self.hasta_id = hasta_id
        # Zebra stili
        self.tableBakteri.setAlternatingRowColors(True)
        self.tableAntibiyogram.setAlternatingRowColors(True)
        self.tableKullanilanAntibiyotik.setAlternatingRowColors(True)

        header = self.tableKullanilanAntibiyotik.horizontalHeader()
        for i in range(self.tableKullanilanAntibiyotik.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
  


        # Bakteri tablosu: [Ad, Tarih, id(gizli)]
        self.tableBakteri.setColumnCount(3)
        self.tableBakteri.setHorizontalHeaderLabels(["Bakteri Adı", "Üreme Tarihi", "id"])
        self.tableBakteri.setColumnHidden(2, True)
        self.tableBakteri.verticalHeader().setVisible(False)
        hb = self.tableBakteri.horizontalHeader()
        hb.setSectionResizeMode(0, QHeaderView.Stretch)
        hb.setSectionResizeMode(1, QHeaderView.Stretch)

        # Antibiyogram tablosu: [Antibiyotik, Sonuç, id(gizli)]
        self.tableAntibiyogram.setColumnCount(3)
        self.tableAntibiyogram.setHorizontalHeaderLabels(["Antibiyotik", "Sonuç", "id"])
        self.tableAntibiyogram.setColumnHidden(2, True)
        self.tableAntibiyogram.verticalHeader().setVisible(False)
        ha = self.tableAntibiyogram.horizontalHeader()
        ha.setSectionResizeMode(0, QHeaderView.Stretch)
        ha.setSectionResizeMode(1, QHeaderView.Stretch)

        # Kullanılan antibiyotik: [id(gizli), Ad, Başlangıç, Bitiş, Dozaj]
        self.tableKullanilanAntibiyotik.verticalHeader().setVisible(False)
        self.tableKullanilanAntibiyotik.setColumnHidden(0, True)

        # Combobox içerikleri
        self.cmbAntibiyotik.clear()
        self.cmbAntibiyotik.addItems([
            "Penisilin","Amikasin","Amoksisilin/Klavulonikasit","Ampisilin",
            "Ampisilin/Sulbaktam","Azitromisin","Aztreonam","Eritromisin",
            "Fosfomisin/Trometamol","Fusidikasit","Gentamisin","İmipenem",
            "Klaritromisin","Klindamisin","Kloramfenikol","Levofloksasin",
            "Meropenem","Netilmisin","Nitrofurantoin","Piperasilin",
            "Piperasilin/Tazobaktam","Sefalotin","Sefepim","Sefotaksim",
            "Seftazidim","Sefuroksim","Siprofloksasin","Teikoplanin",
            "Tetrasiklin","Tobramisin","Trimetoprim/Sülfametaksasol","Vankomisin"
        ])
        self.cmbSonuc.clear()
        self.cmbSonuc.addItems(["Duyarlı", "Orta Duyarlı", "Dirençli"])

        # Başlık: hasta adı
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT ad, soyad FROM hasta WHERE id=?", (hasta_id,))
        row = c.fetchone()
        conn.close()
        if row:
            self.setWindowTitle(f"Hasta Detayları - ID {hasta_id} - {row[0]} {row[1]}")

        # Butonlar
        self.btnBakteriEkle.clicked.connect(self.bakteri_ekle)
        self.btnBakteriSil.clicked.connect(self.bakteri_sil)
        self.btnBakteriGuncelle.clicked.connect(self.bakteri_guncelle)
        self.btnAntibiyogramEkle.clicked.connect(self.antibiyogram_ekle)
        self.btnAntibiyogramSil.clicked.connect(self.antibiyogram_sil)
        self.btnAntibiyogramGuncelle.clicked.connect(self.antibiyogram_guncelle)
        self.btnkullanilan_antibiyotik_ekle.clicked.connect(self.kullanilan_antibiyotik_ekle)
        self.btnkullanilan_antibiyotik_sil.clicked.connect(self.kullanilan_antibiyotik_sil)
        self.btnkullanilan_antibiyotik_guncelle.clicked.connect(self.kullanilan_antibiyotik_guncelle)

        # Listelemeler
        self.listele_bakteri()
        self.listele_antibiyotik()
        self.tableBakteri.cellClicked.connect(self.bakteri_secildi)

    # -------- Listeleme ----------
    def listele_bakteri(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, isim, ureme_tarihi FROM bakteri WHERE hasta_id=?", (self.hasta_id,))
        rows = c.fetchall()
        conn.close()

        self.tableBakteri.setRowCount(0)
        for bid, isim, tarih in rows:
            r = self.tableBakteri.rowCount()
            self.tableBakteri.insertRow(r)
            self.tableBakteri.setItem(r, 0, QTableWidgetItem(isim))
            self.tableBakteri.setItem(r, 1, QTableWidgetItem(tarih))
            self.tableBakteri.setItem(r, 2, QTableWidgetItem(str(bid)))
            for col in (0, 1):
                it = self.tableBakteri.item(r, col)
                if it: it.setTextAlignment(Qt.AlignCenter)

    def listele_antibiyogram(self, bakteri_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, antibiyotik, sonuc FROM antibiyogram WHERE bakteri_id=?", (bakteri_id,))
        rows = c.fetchall()
        conn.close()

        self.tableAntibiyogram.setRowCount(0)
        for aid, ab, sonuc in rows:
            r = self.tableAntibiyogram.rowCount()
            self.tableAntibiyogram.insertRow(r)
            self.tableAntibiyogram.setItem(r, 0, QTableWidgetItem(ab))
            self.tableAntibiyogram.setItem(r, 1, QTableWidgetItem(sonuc))
            self.tableAntibiyogram.setItem(r, 2, QTableWidgetItem(str(aid)))
            for col in (0, 1):
                it = self.tableAntibiyogram.item(r, col)
                if it: it.setTextAlignment(Qt.AlignCenter)

    def listele_antibiyotik(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""SELECT id, antibiyotik, baslangic, bitis, dozaj
                     FROM kullanilan_antibiyotik WHERE hasta_id=?""", (self.hasta_id,))
        rows = c.fetchall()
        conn.close()

        self.tableKullanilanAntibiyotik.setRowCount(0)
        for row in rows:
            r = self.tableKullanilanAntibiyotik.rowCount()
            self.tableKullanilanAntibiyotik.insertRow(r)
            for col, val in enumerate(row):
                self.tableKullanilanAntibiyotik.setItem(r, col, QTableWidgetItem(str(val)))
        self.tableKullanilanAntibiyotik.setColumnHidden(0, True)

    # -------- Seçim ----------
    def bakteri_secildi(self, row, _col):
        id_item = self.tableBakteri.item(row, 2)  # gizli id
        if not id_item: return
        self.listele_antibiyogram(id_item.text())

    # -------- Ekle ----------
    def bakteri_ekle(self):
        dlg = BakteriEkleDialog()
        if dlg.exec_() != QDialog.Accepted: return
        isim, tarih = dlg.get_data()
        if not isim:
            QMessageBox.warning(self, "Uyarı", "Bakteri adı boş olamaz!")
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO bakteri(isim, ureme_tarihi, hasta_id) VALUES(?,?,?)",
                  (isim, tarih, self.hasta_id))
        conn.commit(); conn.close()
        self.listele_bakteri()

    def antibiyogram_ekle(self):
        ab = self.cmbAntibiyotik.currentText()
        sonuc = self.cmbSonuc.currentText()
        r = self.tableBakteri.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Uyarı", "Önce bir bakteri seçin!")
            return
        bakteri_id = self.tableBakteri.item(r, 2).text()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO antibiyogram(bakteri_id, antibiyotik, sonuc) VALUES(?,?,?)",
                  (bakteri_id, ab, sonuc))
        conn.commit(); conn.close()
        self.listele_antibiyogram(bakteri_id)

    def kullanilan_antibiyotik_ekle(self):
        dlg = AntibiyotikEkleDialog()
        if dlg.exec_() != QDialog.Accepted: return
        ad, bas, bit, doz = dlg.get_data()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO kullanilan_antibiyotik(antibiyotik, baslangic, bitis, dozaj, hasta_id)
                     VALUES(?,?,?,?,?)""", (ad, bas, bit, doz, self.hasta_id))
        conn.commit(); conn.close()
        self.listele_antibiyotik()

    # -------- Sil ----------
    def bakteri_sil(self):
        r = self.tableBakteri.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için bakteri seçin!"); return
        bakteri_id = self.tableBakteri.item(r, 2).text()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM antibiyogram WHERE bakteri_id=?", (bakteri_id,))
        c.execute("DELETE FROM bakteri WHERE id=?", (bakteri_id,))
        conn.commit(); conn.close()
        self.listele_bakteri()
        self.tableAntibiyogram.setRowCount(0)

    def antibiyogram_sil(self):
        r = self.tableAntibiyogram.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için antibiyogram seçin!"); return
        ab_id = self.tableAntibiyogram.item(r, 2).text()
        b_row = self.tableBakteri.currentRow()
        if b_row < 0: return
        bakteri_id = self.tableBakteri.item(b_row, 2).text()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM antibiyogram WHERE id=?", (ab_id,))
        conn.commit(); conn.close()
        self.listele_antibiyogram(bakteri_id)

    def kullanilan_antibiyotik_sil(self):
        r = self.tableKullanilanAntibiyotik.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için kayıt seçin!"); return
        id_item = self.tableKullanilanAntibiyotik.item(r, 0)
        if not id_item or not id_item.text().strip():
            QMessageBox.warning(self, "Uyarı", "ID bulunamadı!"); return
        abx_id = id_item.text().strip()
        if QMessageBox.question(self, "Onay", "Silinsin mi?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM kullanilan_antibiyotik WHERE id=?", (abx_id,))
        conn.commit(); conn.close()
        self.listele_antibiyotik()

    # -------- Güncelle ----------
    def bakteri_guncelle(self):
        r = self.tableBakteri.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için bakteri seçin!"); return
        bakteri_id = self.tableBakteri.item(r, 2).text()
        isim = self.tableBakteri.item(r, 0).text()
        tarih = self.tableBakteri.item(r, 1).text()
        dlg = BakteriEkleDialog()
        dlg.bakteri_input.setText(isim)
        dlg.tarih_input.setDate(QDate.fromString(tarih, "dd-MM-yyyy"))
        if dlg.exec_() != QDialog.Accepted: return
        yeni_isim, yeni_tarih = dlg.get_data()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE bakteri SET isim=?, ureme_tarihi=? WHERE id=?",
                  (yeni_isim, yeni_tarih, bakteri_id))
        conn.commit(); conn.close()
        self.listele_bakteri()

    def antibiyogram_guncelle(self):
        r = self.tableAntibiyogram.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için antibiyogram seçin!"); return
        ab_id = self.tableAntibiyogram.item(r, 2).text()
        antibiyotik = self.tableAntibiyogram.item(r, 0).text()
        sonuc = self.tableAntibiyogram.item(r, 1).text()
        dlg = AntibiyogramEkleDialog()
        dlg.antibiyotik_input.setText(antibiyotik)
        idx = dlg.sonuc_input.findText(sonuc)
        if idx >= 0: dlg.sonuc_input.setCurrentIndex(idx)
        if dlg.exec_() != QDialog.Accepted: return
        yeni_ab, yeni_sonuc = dlg.get_data()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE antibiyogram SET antibiyotik=?, sonuc=? WHERE id=?",
                  (yeni_ab, yeni_sonuc, ab_id))
        conn.commit(); conn.close()
        b_row = self.tableBakteri.currentRow()
        if b_row >= 0:
            bakteri_id = self.tableBakteri.item(b_row, 2).text()
            self.listele_antibiyogram(bakteri_id)

    def kullanilan_antibiyotik_guncelle(self):
        r = self.tableKullanilanAntibiyotik.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Uyarı", "Kayıt seçin!"); return
        abx_id = self.tableKullanilanAntibiyotik.item(r, 0).text()
        ad  = self.tableKullanilanAntibiyotik.item(r, 1).text()
        bas = self.tableKullanilanAntibiyotik.item(r, 2).text()
        bit = self.tableKullanilanAntibiyotik.item(r, 3).text()
        doz = self.tableKullanilanAntibiyotik.item(r, 4).text()
        dlg = AntibiyotikEkleDialog()
        dlg.antibiyotik_input.setText(ad)
        dlg.baslangic_input.setDate(QDate.fromString(bas, "dd-MM-yyyy"))
        dlg.bitis_input.setDate(QDate.fromString(bit, "dd-MM-yyyy"))
        dlg.dozaj_input.setText(doz)
        if dlg.exec_() != QDialog.Accepted: return
        yeni_ad, yeni_bas, yeni_bit, yeni_doz = dlg.get_data()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""UPDATE kullanilan_antibiyotik
                        SET antibiyotik=?, baslangic=?, bitis=?, dozaj=?
                      WHERE id=?""",
                  (yeni_ad, yeni_bas, yeni_bit, yeni_doz, abx_id))
        conn.commit(); conn.close()
        self.listele_antibiyotik()

# ------------------ Main ------------------
if __name__ == "__main__":
    veritabani_olustur()
    app = QApplication(sys.argv)
    win = AnaPencere()
    win.show()
    sys.exit(app.exec_())
