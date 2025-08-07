import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox, QTableWidgetItem,
    QDateEdit, QComboBox
)
from PyQt5.QtCore import QDate
from ana_pencere import Ui_MainWindow
from detay_pencere import Ui_MainWindow as Ui_DetayPencere

DB_PATH = "hastatakip.db"


# ------------------ Veritabanı Başlat ------------------
def veritabani_olustur():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS hasta(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tc TEXT UNIQUE,
        ad TEXT,
        soyad TEXT,
        dogum TEXT,
        servis TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS bakteri(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isim TEXT,
        ureme_tarihi TEXT,
        hasta_id INTEGER,
        FOREIGN KEY(hasta_id) REFERENCES hasta(id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS antibiyogram(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        antibiyotik TEXT,
        sonuc TEXT,
        bakteri_id INTEGER,
        FOREIGN KEY(bakteri_id) REFERENCES bakteri(id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS kullanilan_antibiyotik(
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
        self.setWindowTitle("Yeni Hasta Ekle")
        layout = QFormLayout(self)

        self.tc_input = QLineEdit()
        self.ad_input = QLineEdit()
        self.soyad_input = QLineEdit()
        self.dogum_input = QDateEdit()
        self.dogum_input.setCalendarPopup(True)
        self.dogum_input.setDate(QDate.currentDate())
        self.servis_input = QLineEdit()

        layout.addRow("TC Kimlik:", self.tc_input)
        layout.addRow("Ad:", self.ad_input)
        layout.addRow("Soyad:", self.soyad_input)
        layout.addRow("Doğum Tarihi:", self.dogum_input)
        layout.addRow("Servis:", self.servis_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return (
            self.tc_input.text(),
            self.ad_input.text(),
            self.soyad_input.text(),
            self.dogum_input.date().toString("yyyy-MM-dd"),
            self.servis_input.text()
        )


class BakteriEkleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bakteri Bilgisi")
        layout = QFormLayout(self)

        self.bakteri_input = QLineEdit()
        self.tarih_input = QDateEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDate(QDate.currentDate())

        layout.addRow("Bakteri Adı:", self.bakteri_input)
        layout.addRow("Üreme Tarihi:", self.tarih_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return (
            self.bakteri_input.text(),
            self.tarih_input.date().toString("yyyy-MM-dd")
        )


class AntibiyogramEkleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Antibiyogram Bilgisi")
        layout = QFormLayout(self)

        self.antibiyotik_input = QLineEdit()
        self.sonuc_input = QComboBox()
        self.sonuc_input.addItems(["Duyarlı", "Dirençli", "Orta Duyarlı"])

        layout.addRow("Antibiyotik:", self.antibiyotik_input)
        layout.addRow("Sonuç:", self.sonuc_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return (
            self.antibiyotik_input.text(),
            self.sonuc_input.currentText()
        )


class AntibiyotikEkleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kullanılan Antibiyotik Bilgisi")
        layout = QFormLayout(self)

        self.antibiyotik_input = QLineEdit()
        self.baslangic_input = QDateEdit()
        self.baslangic_input.setCalendarPopup(True)
        self.baslangic_input.setDate(QDate.currentDate())
        self.bitis_input = QDateEdit()
        self.bitis_input.setCalendarPopup(True)
        self.bitis_input.setDate(QDate.currentDate())
        self.dozaj_input = QLineEdit()

        layout.addRow("Antibiyotik Adı:", self.antibiyotik_input)
        layout.addRow("Başlangıç Tarihi:", self.baslangic_input)
        layout.addRow("Bitiş Tarihi:", self.bitis_input)
        layout.addRow("Dozaj:", self.dozaj_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return (
            self.antibiyotik_input.text(),
            self.baslangic_input.date().toString("yyyy-MM-dd"),
            self.bitis_input.date().toString("yyyy-MM-dd"),
            self.dozaj_input.text()
        )


# ------------------ Ana Pencere ------------------
class AnaPencere(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Hasta Takip Sistemi - Ana Pencere")
        self.tableWidget.setHorizontalHeaderLabels(
            ["ID", "TC", "Ad", "Soyad", "Doğum Tarihi", "Servis"]
        )

        self.btnHastaEkle.clicked.connect(self.hasta_ekle)
        self.btnHastaSil.clicked.connect(self.hasta_sil)
        self.btnHastaGuncelle.clicked.connect(self.hasta_guncelle)
        self.btnDetayGoster.clicked.connect(self.detay_ac)

        self.hasta_listele()

    def hasta_listele(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hasta")
        rows = cursor.fetchall()
        conn.close()

        self.tableWidget.setRowCount(0)
        for row_data in rows:
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            for col, data in enumerate(row_data):
                self.tableWidget.setItem(row, col, QTableWidgetItem(str(data)))

    def hasta_ekle(self):
        dialog = HastaEkleDialog()
        if dialog.exec_() == QDialog.Accepted:
            tc, ad, soyad, dogum, servis = dialog.get_data()

            # Kullanıcı girişlerini temizle
            tc = tc.strip()
            ad = ad.strip()
            soyad = soyad.strip()
            servis = servis.strip()

            if not tc or not ad or not soyad:
                QMessageBox.warning(self, "Uyarı", "TC, Ad ve Soyad boş olamaz!")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # TC kontrolü (önceden kayıtlı mı?)
            cursor.execute("SELECT id FROM hasta WHERE tc=?", (tc,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Hata", f"Bu TC ({tc}) ile kayıtlı hasta zaten var!")
                conn.close()
                return

            cursor.execute(
                "INSERT INTO hasta(tc, ad, soyad, dogum, servis) VALUES (?, ?, ?, ?, ?)",
                (tc, ad, soyad, dogum, servis)
            )
            conn.commit()
            conn.close()
            self.hasta_listele()


    def hasta_sil(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için hasta seçin!")
            return
        hasta_id = self.tableWidget.item(secili, 0).text()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hasta WHERE id=?", (hasta_id,))
        conn.commit()
        conn.close()
        self.hasta_listele()

    def hasta_guncelle(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için hasta seçin!")
            return
        hasta_id = self.tableWidget.item(secili, 0).text()
        tc = self.tableWidget.item(secili, 1).text()
        ad = self.tableWidget.item(secili, 2).text()
        soyad = self.tableWidget.item(secili, 3).text()
        dogum = self.tableWidget.item(secili, 4).text()
        servis = self.tableWidget.item(secili, 5).text()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE hasta SET tc=?, ad=?, soyad=?, dogum=?, servis=? WHERE id=?
        """, (tc, ad, soyad, dogum, servis, hasta_id))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Bilgi", "Hasta güncellendi!")
        self.hasta_listele()

    def detay_ac(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Detay için hasta seçin!")
            return
        hasta_id = self.tableWidget.item(secili, 0).text()
        self.detay_pencere = DetayPencere(hasta_id)
        self.detay_pencere.show()


# ------------------ Detay Penceresi (Ekle/Sil/Güncelle) ------------------
class DetayPencere(QMainWindow, Ui_DetayPencere):
    def __init__(self, hasta_id):
        super().__init__()
        self.setupUi(self)
        self.hasta_id = hasta_id

        # 🔹 Hasta bilgilerini al ve pencere başlığını güncelle
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ad, soyad FROM hasta WHERE id=?", (hasta_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            ad, soyad = result
            self.setWindowTitle(f"Hasta Detayları - ID {hasta_id} - {ad} {soyad}")
        else:
            self.setWindowTitle(f"Hasta Detayları - ID {hasta_id}")

        # Butonlar
        self.btnBakteriEkle.clicked.connect(self.bakteri_ekle)
        self.btnBakteriSil.clicked.connect(self.bakteri_sil)
        self.btnBakteriGuncelle.clicked.connect(self.bakteri_guncelle)

        self.btnAntibiyogramEkle.clicked.connect(self.antibiyogram_ekle)
        self.btnAntibiyogramSil.clicked.connect(self.antibiyogram_sil)
        self.btnAntibiyogramGuncelle.clicked.connect(self.antibiyogram_guncelle)

        self.btnAntibiyotikEkle.clicked.connect(self.antibiyotik_ekle)
        self.btnAntibiyotikSil.clicked.connect(self.antibiyotik_sil)
        self.btnAntibiyotikGuncelle.clicked.connect(self.antibiyotik_guncelle)

        # Başlangıçta listeler
        self.listele_bakteri()
        self.listele_antibiyotik()
        self.tableBakteri.cellClicked.connect(self.bakteri_secildi)


    # -------- Listeleme Fonksiyonları --------
    def listele_bakteri(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, isim, ureme_tarihi FROM bakteri WHERE hasta_id=?", (self.hasta_id,))
        rows = cursor.fetchall()
        conn.close()

        self.tableBakteri.setRowCount(0)
        for row_data in rows:
            row = self.tableBakteri.rowCount()
            self.tableBakteri.insertRow(row)
            for col, data in enumerate(row_data):
                self.tableBakteri.setItem(row, col, QTableWidgetItem(str(data)))

        # ID sütununu gizle
        self.tableBakteri.setColumnHidden(0, True)

    def listele_antibiyogram(self, bakteri_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, antibiyotik, sonuc FROM antibiyogram WHERE bakteri_id=?", (bakteri_id,))
        rows = cursor.fetchall()
        conn.close()

        self.tableAntibiyogram.setRowCount(0)
        for row_data in rows:
            row = self.tableAntibiyogram.rowCount()
            self.tableAntibiyogram.insertRow(row)
            for col, data in enumerate(row_data):
                self.tableAntibiyogram.setItem(row, col, QTableWidgetItem(str(data)))

        # ID sütununu gizle
        self.tableAntibiyogram.setColumnHidden(0, True)

    def listele_antibiyotik(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, antibiyotik, baslangic, bitis, dozaj FROM kullanilan_antibiyotik WHERE hasta_id=?", (self.hasta_id,))
        rows = cursor.fetchall()
        conn.close()

        self.tableKullanilanAntibiyotik.setRowCount(0)
        for row_data in rows:
            row = self.tableKullanilanAntibiyotik.rowCount()
            self.tableKullanilanAntibiyotik.insertRow(row)
            for col, data in enumerate(row_data):
                self.tableKullanilanAntibiyotik.setItem(row, col, QTableWidgetItem(str(data)))

        # ID sütununu gizle
        self.tableKullanilanAntibiyotik.setColumnHidden(0, True)

    def bakteri_secildi(self, row, col):
        bakteri_id = self.tableBakteri.item(row, 0).text()
        self.listele_antibiyogram(bakteri_id)

    # -------- Ekleme Fonksiyonları --------
    def bakteri_ekle(self):
        dialog = BakteriEkleDialog()
        if dialog.exec_() == QDialog.Accepted:
            isim, tarih = dialog.get_data()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO bakteri(isim, ureme_tarihi, hasta_id) VALUES (?, ?, ?)", 
                           (isim, tarih, self.hasta_id))
            conn.commit()
            conn.close()
            self.listele_bakteri()

    def antibiyogram_ekle(self):
        row = self.tableBakteri.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Önce bakteri seçin!")
            return
        bakteri_id = self.tableBakteri.item(row, 0).text()

        dialog = AntibiyogramEkleDialog()
        if dialog.exec_() == QDialog.Accepted:
            antibiyotik, sonuc = dialog.get_data()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO antibiyogram(antibiyotik, sonuc, bakteri_id) VALUES (?, ?, ?)", 
                           (antibiyotik, sonuc, bakteri_id))
            conn.commit()
            conn.close()
            self.listele_antibiyogram(bakteri_id)

    def antibiyotik_ekle(self):
        dialog = AntibiyotikEkleDialog()
        if dialog.exec_() == QDialog.Accepted:
            ad, bas, bit, doz = dialog.get_data()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO kullanilan_antibiyotik(antibiyotik, baslangic, bitis, dozaj, hasta_id) VALUES (?, ?, ?, ?, ?)",
                           (ad, bas, bit, doz, self.hasta_id))
            conn.commit()
            conn.close()
            self.listele_antibiyotik()

    # -------- Silme Fonksiyonları --------
    def bakteri_sil(self):
        row = self.tableBakteri.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için bakteri seçin!")
            return
        bakteri_id = self.tableBakteri.item(row, 0).text()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bakteri WHERE id=?", (bakteri_id,))
        cursor.execute("DELETE FROM antibiyogram WHERE bakteri_id=?", (bakteri_id,))
        conn.commit()
        conn.close()
        self.listele_bakteri()
        self.tableAntibiyogram.setRowCount(0)

    def antibiyogram_sil(self):
        row = self.tableAntibiyogram.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için antibiyogram seçin!")
            return
        ab_id = self.tableAntibiyogram.item(row, 0).text()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM antibiyogram WHERE id=?", (ab_id,))
        conn.commit()
        conn.close()

        sel_bakteri = self.tableBakteri.currentRow()
        if sel_bakteri >= 0:
            bakteri_id = self.tableBakteri.item(sel_bakteri, 0).text()
            self.listele_antibiyogram(bakteri_id)

    def antibiyotik_sil(self):
        row = self.tableKullanilanAntibiyotik.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için antibiyotik seçin!")
            return
        abx_id = self.tableKullanilanAntibiyotik.item(row, 0).text()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kullanilan_antibiyotik WHERE id=?", (abx_id,))
        conn.commit()
        conn.close()
        self.listele_antibiyotik()

    # -------- Güncelleme Fonksiyonları --------
    def bakteri_guncelle(self):
        row = self.tableBakteri.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için bakteri seçin!")
            return

        bakteri_id = self.tableBakteri.item(row, 0).text()
        isim = self.tableBakteri.item(row, 1).text()
        tarih = self.tableBakteri.item(row, 2).text()

        dialog = BakteriEkleDialog()
        dialog.bakteri_input.setText(isim)
        dialog.tarih_input.setDate(QDate.fromString(tarih, "yyyy-MM-dd"))

        if dialog.exec_() == QDialog.Accepted:
            yeni_isim, yeni_tarih = dialog.get_data()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE bakteri SET isim=?, ureme_tarihi=? WHERE id=?", 
                           (yeni_isim, yeni_tarih, bakteri_id))
            conn.commit()
            conn.close()
            self.listele_bakteri()

    def antibiyogram_guncelle(self):
        row = self.tableAntibiyogram.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için antibiyogram seçin!")
            return

        ab_id = self.tableAntibiyogram.item(row, 0).text()
        antibiyotik = self.tableAntibiyogram.item(row, 1).text()
        sonuc = self.tableAntibiyogram.item(row, 2).text()

        dialog = AntibiyogramEkleDialog()
        dialog.antibiyotik_input.setText(antibiyotik)
        idx = dialog.sonuc_input.findText(sonuc)
        dialog.sonuc_input.setCurrentIndex(idx)

        if dialog.exec_() == QDialog.Accepted:
            yeni_ab, yeni_sonuc = dialog.get_data()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE antibiyogram SET antibiyotik=?, sonuc=? WHERE id=?", 
                           (yeni_ab, yeni_sonuc, ab_id))
            conn.commit()
            conn.close()

            sel_bakteri = self.tableBakteri.currentRow()
            if sel_bakteri >= 0:
                bakteri_id = self.tableBakteri.item(sel_bakteri, 0).text()
                self.listele_antibiyogram(bakteri_id)

    def antibiyotik_guncelle(self):
        row = self.tableKullanilanAntibiyotik.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için antibiyotik seçin!")
            return

        abx_id = self.tableKullanilanAntibiyotik.item(row, 0).text()
        ad = self.tableKullanilanAntibiyotik.item(row, 1).text()
        bas = self.tableKullanilanAntibiyotik.item(row, 2).text()
        bit = self.tableKullanilanAntibiyotik.item(row, 3).text()
        doz = self.tableKullanilanAntibiyotik.item(row, 4).text()

        dialog = AntibiyotikEkleDialog()
        dialog.antibiyotik_input.setText(ad)
        dialog.baslangic_input.setDate(QDate.fromString(bas, "yyyy-MM-dd"))
        dialog.bitis_input.setDate(QDate.fromString(bit, "yyyy-MM-dd"))
        dialog.dozaj_input.setText(doz)

        if dialog.exec_() == QDialog.Accepted:
            yeni_ad, yeni_bas, yeni_bit, yeni_doz = dialog.get_data()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE kullanilan_antibiyotik SET antibiyotik=?, baslangic=?, bitis=?, dozaj=? WHERE id=?", 
                           (yeni_ad, yeni_bas, yeni_bit, yeni_doz, abx_id))
            conn.commit()
            conn.close()
            self.listele_antibiyotik()

# ------------------ Main ------------------
if __name__ == "__main__":
    veritabani_olustur()
    app = QApplication(sys.argv)
    window = AnaPencere()
    window.show()
    sys.exit(app.exec_())
