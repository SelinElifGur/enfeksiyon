# main.py
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox, QTableWidgetItem,
    QDateEdit, QComboBox, QHeaderView, QTableWidget, QAction, QToolBar
)
from PyQt5.QtCore import QDate, Qt

from ana_pencere import Ui_MainWindow
from detay_pencere import Ui_MainWindow as Ui_DetayPencere

DB_PATH = "hastatakip.db"


# ------------------ Veritabanı Başlat ------------------
def veritabani_olustur():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bakteri(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT,
            ureme_tarihi TEXT,
            hasta_id INTEGER,
            FOREIGN KEY(hasta_id) REFERENCES hasta(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS antibiyogram(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            antibiyotik TEXT,
            sonuc TEXT,
            bakteri_id INTEGER,
            FOREIGN KEY(bakteri_id) REFERENCES bakteri(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS kullanilan_antibiyotik(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            antibiyotik TEXT,
            baslangic TEXT,
            bitis TEXT,
            dozaj TEXT,
            hasta_id INTEGER,
            FOREIGN KEY(hasta_id) REFERENCES hasta(id)
        )
    """)

    conn.commit()
    conn.close()


# ------------------ Ortak: kolonları eşitle ------------------
def esitle_gorunur_kolonlar(table: QTableWidget, sira_kolonu: int, esit_kolonlar: list[int]):
    """
    sira_kolonu: içeriğe göre (ResizeToContents)
    esit_kolonlar: listedeki tüm kolonlar eşit genişlik alır (Fixed)
    Gizli kolonlar hesaplamaya dahil edilmez.
    """
    header = table.horizontalHeader()
    # Sıra kolonu içeriğe göre
    header.setSectionResizeMode(sira_kolonu, QHeaderView.ResizeToContents)
    table.resizeColumnToContents(sira_kolonu)
    sira_w = header.sectionSize(sira_kolonu)

    # Eşitlenecek kolonlar Fixed
    for c in esit_kolonlar:
        header.setSectionResizeMode(c, QHeaderView.Fixed)

    # Kullanılabilir alan (scrollbar hesaba katılarak viewport üzerinden)
    viewport_w = table.viewport().width()
    if viewport_w <= 0:
        return
    # Gizli kolonlar zaten genişlik kaplamaz
    kalan = max(0, viewport_w - sira_w - 2)  # 2 px tampon
    adet = len(esit_kolonlar) if esit_kolonlar else 1
    gen = max(60, kalan // adet)

    for idx, c in enumerate(esit_kolonlar):
        # Son kolonda minik farkları absorbe etmesi için kalan alanı bırak
        if idx == adet - 1:
            gen_son = max(60, viewport_w - sira_w - 2 - gen * (adet - 1))
            table.setColumnWidth(c, gen_son)
        else:
            table.setColumnWidth(c, gen)


# ------------------ Dialoglar ------------------
class HastaEkleDialog(QDialog):
    def __init__(self, baslik="Yeni Hasta Ekle"):
        super().__init__()
        self.setWindowTitle(baslik)
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
            self.tc_input.text().strip(),
            self.ad_input.text().strip(),
            self.soyad_input.text().strip(),
            self.dogum_input.date().toString("dd-MM-yyyy"),
            self.servis_input.text().strip()
        )


class BakteriEkleDialog(QDialog):
    def __init__(self, baslik="Bakteri Bilgisi"):
        super().__init__()
        self.setWindowTitle(baslik)
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
            self.bakteri_input.text().strip(),
            self.tarih_input.date().toString("dd-MM-yyyy")
        )


class AntibiyogramEkleDialog(QDialog):
    def __init__(self, baslik="Antibiyogram Bilgisi"):
        super().__init__()
        self.setWindowTitle(baslik)
        layout = QFormLayout(self)

        self.antibiyotik_input = QLineEdit()
        self.sonuc_input = QComboBox()
        self.sonuc_input.addItems(["Duyarlı", "Orta Duyarlı", "Dirençli"])

        layout.addRow("Antibiyotik:", self.antibiyotik_input)
        layout.addRow("Sonuç:", self.sonuc_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return (
            self.antibiyotik_input.text().strip(),
            self.sonuc_input.currentText()
        )


class AntibiyotikEkleDialog(QDialog):
    def __init__(self, baslik="Kullanılan Antibiyotik Bilgisi"):
        super().__init__()
        self.setWindowTitle(baslik)
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
            self.antibiyotik_input.text().strip(),
            self.baslangic_input.date().toString("dd-MM-yyyy"),
            self.bitis_input.date().toString("dd-MM-yyyy"),
            self.dozaj_input.text().strip()
        )


# ------------------ Ana Pencere ------------------
class AnaPencere(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Hasta Takip Sistemi - Ana Pencere")
        self.tableWidget.verticalHeader().setVisible(False)

        # Ana tablo
        self.tableWidget.clear()
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels(["", "ID", "TC", "Ad", "Soyad", "Doğum Tarihi", "Servis"])
        self.tableWidget.setColumnHidden(1, True)  # ID gizli
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableWidget.setSelectionMode(QTableWidget.SingleSelection)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget.horizontalHeader().setStretchLastSection(False)

        # Butonlar
        self.btnHastaEkle.clicked.connect(self.hasta_ekle)
        self.btnHastaSil.clicked.connect(self.hasta_sil)
        self.btnHastaGuncelle.clicked.connect(self.hasta_guncelle)
        self.btnDetayGoster.clicked.connect(self.detay_ac)

        self.hasta_listele()

          # --- Arama araç çubuğu ---
        self.search_bar = QToolBar("Arama", self)
        self.addToolBar(Qt.TopToolBarArea, self.search_bar)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("TC, ad veya soyada göre ara…")
        self.search_edit.returnPressed.connect(self.hasta_ara)

        act_ara = QAction("Ara", self)
        act_ara.triggered.connect(self.hasta_ara)

        act_tumu = QAction("Tümü", self)
        act_tumu.triggered.connect(self.hasta_listele)

        self.search_bar.addWidget(self.search_edit)
        self.search_bar.addAction(act_ara)
        self.search_bar.addAction(act_tumu)

    # --- responsive kolon eşitleme ---
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # # kolonu: 0, eşitlenecek: 2..6
        esitle_gorunur_kolonlar(self.tableWidget, 0, [2, 3, 4, 5, 6])

    # --- Listeleme ---
    def hasta_listele(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, tc, ad, soyad, dogum, servis FROM hasta ORDER BY id")
        rows = cur.fetchall(); conn.close()

        tw = self.tableWidget
        tw.setRowCount(0)
        for sira, (hid, tc, ad, soyad, dogum, servis) in enumerate(rows, start=1):
            r = tw.rowCount()
            tw.insertRow(r)
            tw.setItem(r, 0, QTableWidgetItem(str(sira)))   # numara
            tw.setItem(r, 1, QTableWidgetItem(str(hid)))    # id (gizli)
            tw.setItem(r, 2, QTableWidgetItem(tc or ""))
            tw.setItem(r, 3, QTableWidgetItem(ad or ""))
            tw.setItem(r, 4, QTableWidgetItem(soyad or ""))
            tw.setItem(r, 5, QTableWidgetItem(dogum or ""))
            tw.setItem(r, 6, QTableWidgetItem(servis or ""))
            tw.item(r, 0).setTextAlignment(Qt.AlignCenter)

        esitle_gorunur_kolonlar(self.tableWidget, 0, [2, 3, 4, 5, 6])

    # --- CRUD ---
    def hasta_ekle(self):
        dialog = HastaEkleDialog()
        if dialog.exec_() != QDialog.Accepted:
            return
        tc, ad, soyad, dogum, servis = dialog.get_data()

        if not tc or not ad or not soyad:
            QMessageBox.warning(self, "Uyarı", "TC, Ad ve Soyad boş olamaz!")
            return

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id FROM hasta WHERE tc=?", (tc,))
        if cur.fetchone():
            conn.close()
            QMessageBox.warning(self, "Hata", f"Bu TC ({tc}) ile kayıtlı hasta zaten var!")
            return

        cur.execute(
            "INSERT INTO hasta(tc, ad, soyad, dogum, servis) VALUES (?, ?, ?, ?, ?)",
            (tc, ad, soyad, dogum, servis)
        )
        conn.commit(); conn.close()
        self.hasta_listele()

    def hasta_sil(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için hasta seçin!")
            return
        hasta_id = self.tableWidget.item(secili, 1).text()

        if QMessageBox.question(self, "Onay",
                                "Seçili hastayı silmek istiyor musunuz?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("DELETE FROM hasta WHERE id=?", (hasta_id,))
        cur.execute("DELETE FROM bakteri WHERE hasta_id=?", (hasta_id,))
        cur.execute("""DELETE FROM antibiyogram 
                       WHERE bakteri_id IN (SELECT id FROM bakteri WHERE hasta_id=?)""", (hasta_id,))
        cur.execute("DELETE FROM kullanilan_antibiyotik WHERE hasta_id=?", (hasta_id,))
        conn.commit(); conn.close()
        self.hasta_listele()

    def hasta_guncelle(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için bir hasta seçin!")
            return

        try:
            hasta_id = int(self.tableWidget.item(secili, 1).text())
        except Exception:
            QMessageBox.warning(self, "Uyarı", "Geçersiz hasta ID!")
            return

        tc     = self.tableWidget.item(secili, 2).text() if self.tableWidget.item(secili, 2) else ""
        ad     = self.tableWidget.item(secili, 3).text() if self.tableWidget.item(secili, 3) else ""
        soyad  = self.tableWidget.item(secili, 4).text() if self.tableWidget.item(secili, 4) else ""
        dogum  = self.tableWidget.item(secili, 5).text() if self.tableWidget.item(secili, 5) else ""
        servis = self.tableWidget.item(secili, 6).text() if self.tableWidget.item(secili, 6) else ""

        dlg = HastaEkleDialog("Hasta Güncelle")
        dlg.tc_input.setText(tc)
        dlg.ad_input.setText(ad)
        dlg.soyad_input.setText(soyad)
        if dogum:
            dlg.dogum_input.setDate(QDate.fromString(dogum, "dd-MM-yyyy"))
        dlg.servis_input.setText(servis)

        if dlg.exec_() != QDialog.Accepted:
            return
        yeni_tc, yeni_ad, yeni_soyad, yeni_dogum, yeni_servis = dlg.get_data()

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id FROM hasta WHERE tc=? AND id<>?", (yeni_tc, hasta_id))
        if cur.fetchone():
            conn.close()
            QMessageBox.warning(self, "Hata", f"Bu TC ({yeni_tc}) başka bir hastada kayıtlı!")
            return

        cur.execute("""
            UPDATE hasta SET tc=?, ad=?, soyad=?, dogum=?, servis=? WHERE id=?
        """, (yeni_tc, yeni_ad, yeni_soyad, yeni_dogum, yeni_servis, hasta_id))
        conn.commit(); conn.close()

        self.hasta_listele()
        self.tableWidget.selectRow(secili)
        QMessageBox.information(self, "Başarılı", "Hasta bilgileri güncellendi.")

    def detay_ac(self):
        secili = self.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Detay için hasta seçin!")
            return
        hasta_id = self.tableWidget.item(secili, 1).text()
        self.detay_pencere = DetayPencere(hasta_id)
        self.detay_pencere.show()

    def _hasta_tablosunu_doldur(self, rows):
        tw = self.tableWidget
        tw.setColumnCount(7)
        tw.setHorizontalHeaderLabels(["", "ID", "TC", "Ad", "Soyad", "Doğum Tarihi", "Servis"])
        tw.setColumnHidden(1, True)  # ID gizli
        tw.setRowCount(0)

        for sira, (hid, tc, ad, soyad, dogum, servis) in enumerate(rows, start=1):
            r = tw.rowCount()
            tw.insertRow(r)
            tw.setItem(r, 0, QTableWidgetItem(str(sira)))     # №
            tw.setItem(r, 1, QTableWidgetItem(str(hid)))      # gizli ID
            tw.setItem(r, 2, QTableWidgetItem(tc or ""))
            tw.setItem(r, 3, QTableWidgetItem(ad or ""))
            tw.setItem(r, 4, QTableWidgetItem(soyad or ""))
            tw.setItem(r, 5, QTableWidgetItem(dogum or ""))
            tw.setItem(r, 6, QTableWidgetItem(servis or ""))
            tw.item(r, 0).setTextAlignment(Qt.AlignCenter)

        esitle_gorunur_kolonlar(self.tableWidget, 0, [2, 3, 4, 5, 6])

    def hasta_listele(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, tc, ad, soyad, dogum, servis FROM hasta ORDER BY id")
        rows = cur.fetchall(); conn.close()
        self._hasta_tablosunu_doldur(rows)

    def hasta_ara(self):
        q = (self.search_edit.text() or "").strip()
        if not q:
            self.hasta_listele(); return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""
            SELECT id, tc, ad, soyad, dogum, servis
              FROM hasta
             WHERE tc LIKE ?
                OR LOWER(ad) LIKE LOWER(?)
                OR LOWER(soyad) LIKE LOWER(?)
             ORDER BY id
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
        rows = cur.fetchall(); conn.close()
        self._hasta_tablosunu_doldur(rows)


    


# ------------------ Detay Penceresi ------------------
class DetayPencere(QMainWindow, Ui_DetayPencere):
    def __init__(self, hasta_id):
        super().__init__()
        self.setupUi(self)
        self.hasta_id = int(hasta_id)
        self.tableBakteri.verticalHeader().setVisible(False)
        self.tableAntibiyogram.verticalHeader().setVisible(False)
        self.tableKullanilanAntibiyotik.verticalHeader().setVisible(True)
        self._abx_kolonlari_esitle()


        # Antibiyogram tablosu
        self.tableAntibiyogram.clear()
        self.tableAntibiyogram.setColumnCount(4)
        self.tableAntibiyogram.setHorizontalHeaderLabels(["", "ID", "Antibiyotik", "Sonuç"])
        self.tableAntibiyogram.setColumnHidden(1, True)
        self.tableAntibiyogram.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableAntibiyogram.setSelectionMode(QTableWidget.SingleSelection)
        self.tableAntibiyogram.setAlternatingRowColors(True)
        self.tableAntibiyogram.setEditTriggers(QTableWidget.NoEditTriggers)

        # Bakteri tablosu
        self.tableBakteri.clear()
        self.tableBakteri.setColumnCount(4)
        self.tableBakteri.setHorizontalHeaderLabels(["", "ID", "Bakteri", "Üreme Tarihi"])
        self.tableBakteri.setColumnHidden(1, True)
        self.tableBakteri.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableBakteri.setSelectionMode(QTableWidget.SingleSelection)
        self.tableBakteri.setAlternatingRowColors(True)
        self.tableBakteri.setEditTriggers(QTableWidget.NoEditTriggers)

        # Kullanılan antibiyotik tablosu
        self.tableKullanilanAntibiyotik.clear()
        self.tableKullanilanAntibiyotik.setColumnCount(5)
        self.tableKullanilanAntibiyotik.setHorizontalHeaderLabels(["ID", "Antibiyotik", "Başlangıç", "Bitiş", "Dozaj"])
        self.tableKullanilanAntibiyotik.setColumnHidden(0, True)
        self.tableKullanilanAntibiyotik.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableKullanilanAntibiyotik.setSelectionMode(QTableWidget.SingleSelection)
        self.tableKullanilanAntibiyotik.setAlternatingRowColors(True)
        self.tableKullanilanAntibiyotik.setEditTriggers(QTableWidget.NoEditTriggers)
        
        hdr = self.tableKullanilanAntibiyotik.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)  # gizli ID; sabit kalsın
        for c in range(1, self.tableKullanilanAntibiyotik.columnCount()):
            hdr.setSectionResizeMode(c, QHeaderView.Stretch)

        # Combobox'lar
        self.cmbAntibiyotik.clear()
        self.cmbAntibiyotik.addItems([
            "Penisilin", "Amikasin", "Amoksisilin/Klavulonikasit", "Ampisilin",
            "Ampisilin/Sulbaktam", "Azitromisin", "Aztreonam", "Eritromisin",
            "Fosfomisin/Trometamol", "Fusidikasit", "Gentamisin", "İmipenem",
            "Klaritromisin", "Klindamisin", "Kloramfenikol", "Levofloksasin",
            "Meropenem", "Netilmisin", "Nitrofurantoin",
            "Norfloksasin", "Piperasilin", "Piperasilin/Tazobaktam", "Sefalotin",
            "Sefoperazon", "Sefepim", "Sefiksim", "Sefotaksim", "Seftazidim",
            "Sefuroksim", "Siprofloksasin", "Teikoplanin", "Tetrasiklin",
            "Tobramisin", "Trimetoprim/Sülfametaksazol", "Vankomisin"
        ])
        self.cmbSonuc.clear()
        self.cmbSonuc.addItems(["Duyarlı", "Orta Duyarlı", "Dirençli"])

        # Başlık
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT ad, soyad FROM hasta WHERE id=?", (self.hasta_id,))
        h = cur.fetchone(); conn.close()
        self.setWindowTitle(f"Hasta Detayları - ID {self.hasta_id} - {h[0]} {h[1]}" if h else f"Hasta Detayları - ID {self.hasta_id}")

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

    # responsive kolon eşitleme
    def resizeEvent(self, event):
        super().resizeEvent(event)
        esitle_gorunur_kolonlar(self.tableBakteri, 0, [2, 3])
        esitle_gorunur_kolonlar(self.tableAntibiyogram, 0, [2, 3])
        esitle_gorunur_kolonlar(self.tableKullanilanAntibiyotik, 1, [1, 2, 3, 4])  # 0 gizli, dağılım 1..4

    # --- Event'ler ---
    def bakteri_secildi(self, row: int, col: int):
        item = self.tableBakteri.item(row, 1)  # gizli ID
        if not item:
            return
        self.listele_antibiyogram(item.text())

    # -------- Listeleme Fonksiyonları --------
    def listele_bakteri(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, isim, ureme_tarihi FROM bakteri WHERE hasta_id=? ORDER BY id", (self.hasta_id,))
        rows = cur.fetchall(); conn.close()

        t = self.tableBakteri
        t.setRowCount(0)
        for sira, (bid, isim, tarih) in enumerate(rows, start=1):
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(str(sira)))
            t.setItem(r, 1, QTableWidgetItem(str(bid)))   # gizli id
            t.setItem(r, 2, QTableWidgetItem(isim or ""))
            t.setItem(r, 3, QTableWidgetItem(tarih or ""))
            t.item(r, 0).setTextAlignment(Qt.AlignCenter)
            t.item(r, 3).setTextAlignment(Qt.AlignCenter)

        # İlk satırı seç ve antibiyogramı yükle
        if rows:
            self.tableBakteri.selectRow(0)
            self.listele_antibiyogram(rows[0][0])
        else:
            self.tableAntibiyogram.setRowCount(0)

        esitle_gorunur_kolonlar(self.tableBakteri, 0, [2, 3])

    def listele_antibiyogram(self, bakteri_id):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT id, antibiyotik, sonuc FROM antibiyogram WHERE bakteri_id=? ORDER BY id", (bakteri_id,))
        rows = cur.fetchall(); conn.close()

        t = self.tableAntibiyogram
        t.setRowCount(0)
        for sira, (aid, ab, sonuc) in enumerate(rows, start=1):
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(str(sira)))
            t.setItem(r, 1, QTableWidgetItem(str(aid)))      # gizli id
            t.setItem(r, 2, QTableWidgetItem(ab or ""))
            t.setItem(r, 3, QTableWidgetItem(sonuc or ""))
            t.item(r, 0).setTextAlignment(Qt.AlignCenter)
            t.item(r, 3).setTextAlignment(Qt.AlignCenter)

        esitle_gorunur_kolonlar(self.tableAntibiyogram, 0, [2, 3])

    def listele_antibiyotik(self):
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""
            SELECT id, antibiyotik, baslangic, bitis, dozaj 
            FROM kullanilan_antibiyotik WHERE hasta_id=? ORDER BY id
        """, (self.hasta_id,))
        rows = cur.fetchall(); conn.close()

        t = self.tableKullanilanAntibiyotik
        t.setRowCount(0)
        for (kid, ad, bas, bit, doz) in rows:
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(str(kid)))
            t.setItem(r, 1, QTableWidgetItem(ad or ""))
            t.setItem(r, 2, QTableWidgetItem(bas or ""))
            t.setItem(r, 3, QTableWidgetItem(bit or ""))
            t.setItem(r, 4, QTableWidgetItem(doz or ""))

    def _abx_kolonlari_esitle(self):
        t = self.tableKullanilanAntibiyotik
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)   # 4 görünür sütunu eşit böler
        t.setColumnHidden(0, True)                      # ID sütunu gizli kalsın
        t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._abx_kolonlari_esitle()



    # -------- Ekleme Fonksiyonları --------
    def bakteri_ekle(self):
        dialog = BakteriEkleDialog("Bakteri Ekle")
        if dialog.exec_() != QDialog.Accepted:
            return
        isim, tarih = dialog.get_data()
        if not isim:
            QMessageBox.warning(self, "Uyarı", "Bakteri adı boş olamaz!")
            return
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("INSERT INTO bakteri(isim, ureme_tarihi, hasta_id) VALUES (?, ?, ?)",
                    (isim, tarih, self.hasta_id))
        conn.commit(); conn.close()
        self.listele_bakteri()

    def antibiyogram_ekle(self):
        secili_bakteri = self.tableBakteri.currentRow()
        if secili_bakteri < 0:
            QMessageBox.warning(self, "Uyarı", "Önce bir bakteri seçin!")
            return
        bakteri_id = self.tableBakteri.item(secili_bakteri, 1).text()
        antibiyotik = self.cmbAntibiyotik.currentText()
        sonuc = self.cmbSonuc.currentText()

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("INSERT INTO antibiyogram (bakteri_id, antibiyotik, sonuc) VALUES (?, ?, ?)",
                    (bakteri_id, antibiyotik, sonuc))
        conn.commit(); conn.close()
        self.listele_antibiyogram(bakteri_id)

    def kullanilan_antibiyotik_ekle(self):
        dlg = AntibiyotikEkleDialog("Kullanılan Antibiyotik Ekle")
        if dlg.exec_() != QDialog.Accepted:
            return
        ad, bas, bit, doz = dlg.get_data()

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""
            INSERT INTO kullanilan_antibiyotik(antibiyotik, baslangic, bitis, dozaj, hasta_id)
            VALUES (?,?,?,?,?)
        """, (ad, bas, bit, doz, self.hasta_id))
        conn.commit(); conn.close()
        self.listele_antibiyotik()

    # -------- Silme Fonksiyonları --------
    def bakteri_sil(self):
        row = self.tableBakteri.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için bakteri seçin!")
            return
        bakteri_id = self.tableBakteri.item(row, 1).text()

        if QMessageBox.question(self, "Onay", "Seçili bakteriyi silmek istiyor musunuz?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("DELETE FROM bakteri WHERE id=?", (bakteri_id,))
        cur.execute("DELETE FROM antibiyogram WHERE bakteri_id=?", (bakteri_id,))
        conn.commit(); conn.close()
        self.listele_bakteri()
        self.tableAntibiyogram.setRowCount(0)

    def antibiyogram_sil(self):
        row = self.tableAntibiyogram.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için antibiyogram seçin!")
            return
        ab_id = self.tableAntibiyogram.item(row, 1).text()

        b_row = self.tableBakteri.currentRow()
        if b_row < 0:
            return
        bakteri_id = self.tableBakteri.item(b_row, 1).text()

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("DELETE FROM antibiyogram WHERE id=?", (ab_id,))
        conn.commit(); conn.close()
        self.listele_antibiyogram(bakteri_id)

    def kullanilan_antibiyotik_sil(self):
        row = self.tableKullanilanAntibiyotik.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için antibiyotik seçin!")
            return

        abx_id = self.tableKullanilanAntibiyotik.item(row, 0).text()

        if QMessageBox.question(self, "Onay",
                                "Seçili kullanılan antibiyotiği silmek istiyor musunuz?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("DELETE FROM kullanilan_antibiyotik WHERE id=?", (abx_id,))
        conn.commit(); conn.close()
        self.listele_antibiyotik()
        self.tableKullanilanAntibiyotik.clearSelection()

    # -------- Güncelleme Fonksiyonları --------
    def bakteri_guncelle(self):
        row = self.tableBakteri.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için bakteri seçin!")
            return

        bakteri_id = self.tableBakteri.item(row, 1).text()
        isim = self.tableBakteri.item(row, 2).text()
        tarih = self.tableBakteri.item(row, 3).text()

        dialog = BakteriEkleDialog("Bakteri Güncelle")
        dialog.bakteri_input.setText(isim)
        if tarih:
            dialog.tarih_input.setDate(QDate.fromString(tarih, "dd-MM-yyyy"))

        if dialog.exec_() != QDialog.Accepted:
            return
        yeni_isim, yeni_tarih = dialog.get_data()

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE bakteri SET isim=?, ureme_tarihi=? WHERE id=?",
                    (yeni_isim, yeni_tarih, bakteri_id))
        conn.commit(); conn.close()
        self.listele_bakteri()

    def antibiyogram_guncelle(self):
        row = self.tableAntibiyogram.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için antibiyogram seçin!")
            return

        ab_id = self.tableAntibiyogram.item(row, 1).text()
        antibiyotik = self.tableAntibiyogram.item(row, 2).text()
        sonuc = self.tableAntibiyogram.item(row, 3).text()

        dialog = AntibiyogramEkleDialog("Antibiyogram Güncelle")
        dialog.antibiyotik_input.setText(antibiyotik)
        idx = dialog.sonuc_input.findText(sonuc)
        if idx >= 0:
            dialog.sonuc_input.setCurrentIndex(idx)

        if dialog.exec_() != QDialog.Accepted:
            return
        yeni_ab, yeni_sonuc = dialog.get_data()

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("UPDATE antibiyogram SET antibiyotik=?, sonuc=? WHERE id=?",
                    (yeni_ab, yeni_sonuc, ab_id))
        conn.commit(); conn.close()

        sel_bakteri = self.tableBakteri.currentRow()
        if sel_bakteri >= 0:
            bakteri_id = self.tableBakteri.item(sel_bakteri, 1).text()
            self.listele_antibiyogram(bakteri_id)

    def kullanilan_antibiyotik_guncelle(self):
        row = self.tableKullanilanAntibiyotik.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Güncellemek için bir kayıt seçin!")
            return

        abx_id = self.tableKullanilanAntibiyotik.item(row, 0).text()
        ad     = self.tableKullanilanAntibiyotik.item(row, 1).text()
        bas    = self.tableKullanilanAntibiyotik.item(row, 2).text()
        bit    = self.tableKullanilanAntibiyotik.item(row, 3).text()
        doz    = self.tableKullanilanAntibiyotik.item(row, 4).text()

        dlg = AntibiyotikEkleDialog("Kullanılan Antibiyotik Güncelle")
        dlg.antibiyotik_input.setText(ad)
        if bas:
            dlg.baslangic_input.setDate(QDate.fromString(bas, "dd-MM-yyyy"))
        if bit:
            dlg.bitis_input.setDate(QDate.fromString(bit, "dd-MM-yyyy"))
        dlg.dozaj_input.setText(doz)

        if dlg.exec_() != QDialog.Accepted:
            return

        yeni_ad, yeni_bas, yeni_bit, yeni_doz = dlg.get_data()

        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""
            UPDATE kullanilan_antibiyotik
               SET antibiyotik=?, baslangic=?, bitis=?, dozaj=?
             WHERE id=?
        """, (yeni_ad, yeni_bas, yeni_bit, yeni_doz, abx_id))
        conn.commit(); conn.close()
        self.listele_antibiyotik()


# ------------------ Main ------------------
if __name__ == "__main__":
    veritabani_olustur()
    app = QApplication(sys.argv)
    window = AnaPencere()
    window.show()
    sys.exit(app.exec_())
