import sys
import sqlite3
from PyQt5 import QtWidgets          
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QDateEdit, QComboBox
from PyQt5.QtCore import QDate
from ana_pencere import Ui_MainWindow 

DB_PATH = "mikrobiyoloji.db"

# ------------------ Dialoglar ------------------
class HastaDialog(QDialog):
    def __init__(self, tc="", ad="", soyad="", servis=""):
        super().__init__()
        self.setWindowTitle("Hasta Ekle / Güncelle")
        layout = QFormLayout(self)

        self.tc_input = QLineEdit(tc)
        self.ad_input = QLineEdit(ad)
        self.soyad_input = QLineEdit(soyad)
        self.servis_input = QLineEdit(servis)

        layout.addRow("TC Kimlik:", self.tc_input)
        layout.addRow("Ad:", self.ad_input)
        layout.addRow("Soyad:", self.soyad_input)
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
            self.servis_input.text()
        )

class BakteriDialog(QDialog):
    def __init__(self, isim="", ureme_tarihi=""):
        super().__init__()
        self.setWindowTitle("Bakteri Ekle / Güncelle")
        layout = QFormLayout(self)

        self.bakteri_input = QLineEdit(isim)
        self.tarih_input = QDateEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDate(QDate.currentDate() if not ureme_tarihi else QDate.fromString(ureme_tarihi, "yyyy-MM-dd"))

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

class AntibiyogramDialog(QDialog):
    def __init__(self, antibiyotik="", sonuc=""):
        super().__init__()
        self.setWindowTitle("Antibiyogram Ekle / Güncelle")
        layout = QFormLayout(self)

        self.antibiyotik_input = QLineEdit(antibiyotik)
        self.sonuc_input = QComboBox()
        self.sonuc_input.addItems(["Duyarlı", "Dirençli", "Orta Duyarlı"])
        if sonuc:
            idx = self.sonuc_input.findText(sonuc)
            if idx >= 0:
                self.sonuc_input.setCurrentIndex(idx)

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

class KullanilanAntibiyotikDialog(QDialog):
    def __init__(self, antibiyotik="", baslangic="", bitis="", dozaj=""):
        super().__init__()
        self.setWindowTitle("Kullanılan Antibiyotik Ekle / Güncelle")
        layout = QFormLayout(self)

        self.antibiyotik_input = QLineEdit(antibiyotik)
        self.baslangic_input = QDateEdit()
        self.baslangic_input.setCalendarPopup(True)
        self.baslangic_input.setDate(QDate.currentDate() if not baslangic else QDate.fromString(baslangic, "yyyy-MM-dd"))

        self.bitis_input = QDateEdit()
        self.bitis_input.setCalendarPopup(True)
        self.bitis_input.setDate(QDate.currentDate() if not bitis else QDate.fromString(bitis, "yyyy-MM-dd"))

        self.dozaj_input = QLineEdit(dozaj)

        layout.addRow("Antibiyotik:", self.antibiyotik_input)
        layout.addRow("Başlangıç:", self.baslangic_input)
        layout.addRow("Bitiş:", self.bitis_input)
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

# ------------------ Ana Uygulama ------------------
class HastaApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Hasta Takip Sistemi")

        # Hasta
        self.btnEkle.clicked.connect(self.hasta_ekle)
        self.btnSil.clicked.connect(self.hasta_sil)
        self.btnGuncelle.clicked.connect(self.hasta_guncelle)

        # Bakteri
        self.btnBakteriEkle.clicked.connect(self.bakteri_ekle)
        self.btnBakteriSil.clicked.connect(self.bakteri_sil)
        self.btnBakteriGuncelle.clicked.connect(self.bakteri_guncelle)

        # Antibiyogram
        self.btnAntibiyogramEkle.clicked.connect(self.antibiyogram_ekle)
        self.btnAntibiyogramSil.clicked.connect(self.antibiyogram_sil)
        self.btnAntibiyogramGuncelle.clicked.connect(self.antibiyogram_guncelle)

        # Kullanılan Antibiyotik
        self.btnKullanilanAntibiyotikEkle.clicked.connect(self.kullanilan_antibiyotik_ekle)
        self.btnKullanilanAntibiyotikSil.clicked.connect(self.kullanilan_antibiyotik_sil)
        self.btnKullanilanAntibiyotikGuncelle.clicked.connect(self.kullanilan_antibiyotik_guncelle)

        # Tablo tıklamaları
        self.tableWidget.cellClicked.connect(self.hasta_secildi)
        self.tableBakteri.cellClicked.connect(self.bakteri_secildi)

        self.hasta_listele()

    # ------------------ Hasta İşlemleri ------------------
    def hasta_ekle(self):
        dialog = HastaDialog()
        if dialog.exec_() == QDialog.Accepted:
            tc, ad, soyad, servis = dialog.get_data()
            if not tc or not ad or not soyad or not servis:
                QMessageBox.warning(self, "Uyarı", "Tüm alanları doldurun!")
                return
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS hasta(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tc_kimlik TEXT UNIQUE,
                ad TEXT, soyad TEXT, servis TEXT)""")
            try:
                cursor.execute("INSERT INTO hasta(tc_kimlik,ad,soyad,servis) VALUES(?,?,?,?)",
                               (tc, ad, soyad, servis))
                conn.commit()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Hata", "Bu TC ile hasta zaten var!")
            conn.close()
            self.hasta_listele()

    def hasta_listele(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, tc_kimlik, ad, soyad, servis FROM hasta")
        rows = cursor.fetchall()
        conn.close()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setRowCount(len(rows))
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(["ID", "TC", "Ad", "Soyad", "Servis"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

    def hasta_sil(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Seçim yapın!")
            return
        hasta_id = self.tableWidget.item(secili, 0).text()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM hasta WHERE id=?", (hasta_id,))
        conn.commit()
        conn.close()
        self.hasta_listele()

    def hasta_guncelle(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Seçim yapın!")
            return
        hasta_id = self.tableWidget.item(secili, 0).text()
        tc = self.tableWidget.item(secili, 1).text()
        ad = self.tableWidget.item(secili, 2).text()
        soyad = self.tableWidget.item(secili, 3).text()
        servis = self.tableWidget.item(secili, 4).text()
        dialog = HastaDialog(tc, ad, soyad, servis)
        if dialog.exec_() == QDialog.Accepted:
            yeni_tc, yeni_ad, yeni_soyad, yeni_servis = dialog.get_data()
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""UPDATE hasta SET tc_kimlik=?, ad=?, soyad=?, servis=? WHERE id=?""",
                        (yeni_tc, yeni_ad, yeni_soyad, yeni_servis, hasta_id))
            conn.commit()
            conn.close()
            self.hasta_listele()

    # ------------------ Bakteri İşlemleri (Ekle/Sil/Güncelle) ------------------
    def bakteri_ekle(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Önce hasta seçin!")
            return
        hasta_id = self.tableWidget.item(secili, 0).text()
        dialog = BakteriDialog()
        if dialog.exec_() == QDialog.Accepted:
            isim, tarih = dialog.get_data()
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS bakteri(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT, ureme_tarihi DATE, hasta_id INTEGER)""")
            cur.execute("INSERT INTO bakteri(isim,ureme_tarihi,hasta_id) VALUES(?,?,?)",
                        (isim, tarih, hasta_id))
            conn.commit()
            conn.close()
            self.bakteri_listele(hasta_id)

    def bakteri_listele(self, hasta_id):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id,isim,ureme_tarihi FROM bakteri WHERE hasta_id=?", (hasta_id,))
        rows = cur.fetchall()
        conn.close()
        self.tableBakteri.setRowCount(0)
        self.tableBakteri.setRowCount(len(rows))
        self.tableBakteri.setColumnCount(3)
        self.tableBakteri.setHorizontalHeaderLabels(["ID","Bakteri","Üreme Tarihi"])
        for i,row in enumerate(rows):
            for j,val in enumerate(row):
                self.tableBakteri.setItem(i,j,QTableWidgetItem(str(val)))

    def bakteri_sil(self):
        secili = self.tableBakteri.currentRow()
        if secili<0:
            QMessageBox.warning(self,"Uyarı","Seçim yapın!")
            return
        bakteri_id=self.tableBakteri.item(secili,0).text()
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        cur.execute("DELETE FROM bakteri WHERE id=?",(bakteri_id,))
        conn.commit()
        conn.close()
        self.hasta_secildi()

    def bakteri_guncelle(self):
        secili = self.tableBakteri.currentRow()
        if secili<0:
            QMessageBox.warning(self,"Uyarı","Seçim yapın!")
            return
        bakteri_id=self.tableBakteri.item(secili,0).text()
        isim=self.tableBakteri.item(secili,1).text()
        tarih=self.tableBakteri.item(secili,2).text()
        dialog=BakteriDialog(isim,tarih)
        if dialog.exec_()==QDialog.Accepted:
            yeni_isim,yeni_tarih=dialog.get_data()
            conn=sqlite3.connect(DB_PATH)
            cur=conn.cursor()
            cur.execute("UPDATE bakteri SET isim=?,ureme_tarihi=? WHERE id=?",(yeni_isim,yeni_tarih,bakteri_id))
            conn.commit()
            conn.close()
            self.hasta_secildi()

    # ------------------ Antibiyogram İşlemleri (Ekle/Sil/Güncelle) ------------------
    def antibiyogram_ekle(self):
        secili=self.tableBakteri.currentRow()
        if secili<0:
            QMessageBox.warning(self,"Uyarı","Önce bakteri seçin!")
            return
        bakteri_id=self.tableBakteri.item(secili,0).text()
        dialog=AntibiyogramDialog()
        if dialog.exec_()==QDialog.Accepted:
            antibiyotik,sonuc=dialog.get_data()
            conn=sqlite3.connect(DB_PATH)
            cur=conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS antibiyogram(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                antibiyotik TEXT, sonuc TEXT, bakteri_id INTEGER)""")
            cur.execute("INSERT INTO antibiyogram(antibiyotik,sonuc,bakteri_id) VALUES(?,?,?)",
                        (antibiyotik,sonuc,bakteri_id))
            conn.commit()
            conn.close()
            self.antibiyogram_listele(bakteri_id)

    def antibiyogram_listele(self,bakteri_id):
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        cur.execute("SELECT id,antibiyotik,sonuc FROM antibiyogram WHERE bakteri_id=?",(bakteri_id,))
        rows=cur.fetchall()
        conn.close()
        self.tableAntibiyogram.setRowCount(0)
        self.tableAntibiyogram.setRowCount(len(rows))
        self.tableAntibiyogram.setColumnCount(3)
        self.tableAntibiyogram.setHorizontalHeaderLabels(["ID","Antibiyotik","Sonuç"])
        for i,row in enumerate(rows):
            for j,val in enumerate(row):
                self.tableAntibiyogram.setItem(i,j,QTableWidgetItem(str(val)))
                self.tableAntibiyogram.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def antibiyogram_sil(self):
        secili = self.tableAntibiyogram.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek antibiyogramı seçin!")
            return

        ab_id = self.tableAntibiyogram.item(secili, 0).text()
     
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM antibiyogram WHERE id=?", (ab_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Bilgi", "Antibiyogram kaydı silindi!")

        # Seçili bakteri altındaki listeyi güncelle
        bakteri_id = self.tableBakteri.item(self.tableBakteri.currentRow(), 0).text()
        self.antibiyogram_listele(bakteri_id)
        self.btnAntibiyogramSil.clicked.connect(self.antibiyogram_sil)



    def antibiyogram_guncelle(self):
        secili=self.tableAntibiyogram.currentRow()
        if secili<0:
            QMessageBox.warning(self,"Uyarı","Seçim yapın!")
            return
        ab_id=self.tableAntibiyogram.item(secili,0).text()
        antibiyotik=self.tableAntibiyogram.item(secili,1).text()
        sonuc=self.tableAntibiyogram.item(secili,2).text()
        dialog=AntibiyogramDialog(antibiyotik,sonuc)
        if dialog.exec_()==QDialog.Accepted:
            yeni_ab,yeni_sonuc=dialog.get_data()
            conn=sqlite3.connect(DB_PATH)
            cur=conn.cursor()
            cur.execute("UPDATE antibiyogram SET antibiyotik=?,sonuc=? WHERE id=?",(yeni_ab,yeni_sonuc,ab_id))
            conn.commit()
            conn.close()
            self.bakteri_secildi()

    # ------------------ Kullanılan Antibiyotik İşlemleri (Ekle/Sil/Güncelle) ------------------
    def kullanilan_antibiyotik_ekle(self):
        secili=self.tableWidget.currentRow()
        if secili<0:
            QMessageBox.warning(self,"Uyarı","Hasta seçin!")
            return
        hasta_id=self.tableWidget.item(secili,0).text()
        dialog=KullanilanAntibiyotikDialog()
        if dialog.exec_()==QDialog.Accepted:
            antibiyotik,bas,bit,doz=dialog.get_data()
            conn=sqlite3.connect(DB_PATH)
            cur=conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS kullanilan_antibiyotik(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                antibiyotik TEXT, baslangic DATE, bitis DATE, dozaj TEXT, hasta_id INTEGER)""")
            cur.execute("INSERT INTO kullanilan_antibiyotik(antibiyotik,baslangic,bitis,dozaj,hasta_id) VALUES(?,?,?,?,?)",
                        (antibiyotik,bas,bit,doz,hasta_id))
            conn.commit()
            conn.close()
            self.kullanilan_antibiyotik_listele(hasta_id)

    def kullanilan_antibiyotik_listele(self,hasta_id):
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        cur.execute("SELECT id,antibiyotik,baslangic,bitis,dozaj FROM kullanilan_antibiyotik WHERE hasta_id=?",(hasta_id,))
        rows=cur.fetchall()
        conn.close()
        self.tableKullanilanAntibiyotik.setRowCount(0)
        self.tableKullanilanAntibiyotik.setRowCount(len(rows))
        self.tableKullanilanAntibiyotik.setColumnCount(5)
        self.tableKullanilanAntibiyotik.setHorizontalHeaderLabels(["ID","Antibiyotik","Başlangıç","Bitiş","Dozaj"])
        for i,row in enumerate(rows):
            for j,val in enumerate(row):
                self.tableKullanilanAntibiyotik.setItem(i,j,QTableWidgetItem(str(val)))

    def kullanilan_antibiyotik_sil(self):
        secili=self.tableKullanilanAntibiyotik.currentRow()
        if secili<0:
            QMessageBox.warning(self,"Uyarı","Seçim yapın!")
            return
        ka_id=self.tableKullanilanAntibiyotik.item(secili,0).text()
        conn=sqlite3.connect(DB_PATH)
        cur=conn.cursor()
        cur.execute("DELETE FROM kullanilan_antibiyotik WHERE id=?",(ka_id,))
        conn.commit()
        conn.close()
        self.hasta_secildi()

    def kullanilan_antibiyotik_guncelle(self):
        secili=self.tableKullanilanAntibiyotik.currentRow()
        if secili<0:
            QMessageBox.warning(self,"Uyarı","Seçim yapın!")
            return
        ka_id=self.tableKullanilanAntibiyotik.item(secili,0).text()
        ab=self.tableKullanilanAntibiyotik.item(secili,1).text()
        bas=self.tableKullanilanAntibiyotik.item(secili,2).text()
        bit=self.tableKullanilanAntibiyotik.item(secili,3).text()
        doz=self.tableKullanilanAntibiyotik.item(secili,4).text()
        dialog=KullanilanAntibiyotikDialog(ab,bas,bit,doz)
        if dialog.exec_()==QDialog.Accepted:
            yeni_ab,yeni_bas,yeni_bit,yeni_doz=dialog.get_data()
            conn=sqlite3.connect(DB_PATH)
            cur=conn.cursor()
            cur.execute("UPDATE kullanilan_antibiyotik SET antibiyotik=?,baslangic=?,bitis=?,dozaj=? WHERE id=?",
                        (yeni_ab,yeni_bas,yeni_bit,yeni_doz,ka_id))
            conn.commit()
            conn.close()
            self.hasta_secildi()

    # ------------------ Tablo Tıklamaları ------------------
    def hasta_secildi(self):
        secili=self.tableWidget.currentRow()
        if secili>=0:
            hasta_id=self.tableWidget.item(secili,0).text()
            self.bakteri_listele(hasta_id)
            self.kullanilan_antibiyotik_listele(hasta_id)

    def bakteri_secildi(self):
        secili=self.tableBakteri.currentRow()
        if secili>=0:
            bakteri_id=self.tableBakteri.item(secili,0).text()
            self.antibiyogram_listele(bakteri_id)

if __name__=="__main__":
    app=QApplication(sys.argv)
    w=HastaApp()
    w.show()
    sys.exit(app.exec_())
