# ui_components.py - ÇOKLU PDF DESTEĞİ İLE MODERN ARAYÜZ
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pdf_processor import PDFProcessor
from export_manager import ExportManager
import threading
from datetime import datetime
import logging
import pdfplumber
import os

# Eski class ismi korundu ama modern arayüz eklendi
class PriceCalculatorUI:
    """Eski uyumluluk için - yeni ModernPriceCalculatorUI'a yönlendirir"""
    def __init__(self, root):
        return ModernPriceCalculatorUI(root)

class ModernPriceCalculatorUI:
    def __init__(self, root):
        self.root = root
        self.export_manager = ExportManager()
        
        # Çoklu PDF desteği için değişiklikler
        self.pdf_processors = []  # Her PDF için ayrı processor
        self.pdf_files = []  # Yüklenen PDF dosyalarının bilgileri
        self.current_data_all = {}  # Tüm PDF'lerin işlenmiş verileri
        self.max_pdf_count = 3  # Maksimum PDF sayısı
        
        self.current_data = {}
        self.current_pdf_type = "normal"
        self.pdf_loaded = False
        
        # Renkler
        self.colors = {
            'primary': '#6c5ce7',
            'primary_dark': '#5b4bd5',
            'secondary': '#74b9ff',
            'success': '#00b894',
            'danger': '#e17055',
            'warning': '#fdcb6e',
            'bg': '#f8f9fa',
            'card_bg': '#ffffff',
            'text': '#2d3436',
            'text_light': '#636e72',
            'border': '#e9ecef',
            'hover': '#f1f0ff'
        }
        
        self.setup_styles()
        self.setup_ui()
        
    def setup_styles(self):
        """Modern stil ayarları"""
        self.root.configure(bg=self.colors['bg'])
        
        # TTK stil ayarları
        style = ttk.Style()
        style.theme_use('clam')
        
        # Genel stiller
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 24, 'bold'),
                       background=self.colors['bg'],
                       foreground=self.colors['text'])
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 11),
                       background=self.colors['bg'],
                       foreground=self.colors['text_light'])
        
        style.configure('Card.TFrame',
                       background=self.colors['card_bg'],
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focusthickness=0,
                       focuscolor='none')
        
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_dark']),
                           ('!active', self.colors['primary'])],
                 foreground=[('active', 'white'),
                           ('!active', 'white')])
        
    def setup_ui(self):
        """Ana arayüzü oluştur"""
        # Ana container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Başlık
        self.create_header(main_container)
        
        # İçerik alanı
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Tab sistemi
        self.create_tabs(content_frame)
        
        # Alt kontrol paneli
        self.create_control_panel(main_container)
        
        # İlerleme çubuğu
        self.create_progress_bar(main_container)
        
    def create_header(self, parent):
        """Başlık alanı"""
        header_frame = tk.Frame(parent, bg=self.colors['bg'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Başlık metni
        title_container = tk.Frame(header_frame, bg=self.colors['bg'])
        title_container.pack(expand=True)
        
        title = tk.Label(title_container, 
                        text="🚀 Bupiliç İskontolu Fiyat Hesaplayıcı",
                        font=('Segoe UI', 28, 'bold'),
                        bg=self.colors['bg'],
                        fg=self.colors['primary'])
        title.pack()
        
        subtitle = tk.Label(title_container,
                           text="PDF fiyat listelerinizi kolayca işleyin ve iskonto uygulayın (Maksimum 3 PDF)",
                           font=('Segoe UI', 12),
                           bg=self.colors['bg'],
                           fg=self.colors['text_light'])
        subtitle.pack(pady=(5, 0))
        
    def create_tabs(self, parent):
        """Tab sistemi"""
        # Tab başlıkları container
        tab_header = tk.Frame(parent, bg=self.colors['bg'])
        tab_header.pack(fill=tk.X, pady=(0, 10))
        
        self.tabs = {}
        self.tab_buttons = {}
        self.current_tab = None
        
        tab_names = [
            ("📄 PDF Yükle", "pdf"),
            ("💰 İskonto Ayarla", "discount"),
            ("📊 Önizleme", "preview"),
            ("📈 İstatistikler", "stats")
        ]
        
        for i, (name, key) in enumerate(tab_names):
            btn = tk.Button(tab_header,
                          text=name,
                          font=('Segoe UI', 11),
                          bg=self.colors['border'],
                          fg=self.colors['text'],
                          bd=0,
                          padx=30,
                          pady=12,
                          cursor='hand2',
                          command=lambda k=key: self.show_tab(k))
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.tab_buttons[key] = btn
        
        # Tab içerikleri container
        self.tab_container = tk.Frame(parent, bg=self.colors['card_bg'])
        self.tab_container.pack(fill=tk.BOTH, expand=True)
        
        # Tabları oluştur
        self.create_pdf_tab()
        self.create_discount_tab()
        self.create_preview_tab()
        self.create_stats_tab()
        
        # İlk tabı göster
        self.show_tab('pdf')
        
    def show_tab(self, key):
        """Tab değiştir"""
        # Tüm tabları gizle
        for tab_key, tab_frame in self.tabs.items():
            tab_frame.pack_forget()
            self.tab_buttons[tab_key].configure(
                bg=self.colors['border'],
                fg=self.colors['text']
            )
        
        # Seçili tabı göster
        self.tabs[key].pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.tab_buttons[key].configure(
            bg=self.colors['primary'],
            fg='white'
        )
        self.current_tab = key
        
    def create_pdf_tab(self):
        """PDF yükleme tabı - ÇOKLU PDF DESTEĞİ"""
        tab = tk.Frame(self.tab_container, bg=self.colors['card_bg'])
        self.tabs['pdf'] = tab
        
        # Başlık
        title = tk.Label(tab,
                        text="PDF Dosyalarını Seçin",
                        font=('Segoe UI', 16, 'bold'),
                        bg=self.colors['card_bg'],
                        fg=self.colors['text'])
        title.pack(pady=(0, 20))
        
        # PDF listesi frame
        pdf_list_frame = tk.Frame(tab, bg=self.colors['card_bg'])
        pdf_list_frame.pack(fill=tk.BOTH, expand=True, padx=40)
        
        # Yüklenen PDF'ler listesi
        list_label = tk.Label(pdf_list_frame,
                            text="Yüklenen PDF Dosyaları:",
                            font=('Segoe UI', 12, 'bold'),
                            bg=self.colors['card_bg'],
                            fg=self.colors['text'])
        list_label.pack(anchor='w', pady=(0, 10))
        
        # PDF listesi için frame
        self.pdf_list_container = tk.Frame(pdf_list_frame, bg=self.colors['hover'])
        self.pdf_list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Boş liste mesajı
        self.empty_list_label = tk.Label(self.pdf_list_container,
                                        text="Henüz PDF yüklenmedi",
                                        font=('Segoe UI', 11),
                                        bg=self.colors['hover'],
                                        fg=self.colors['text_light'],
                                        pady=30)
        self.empty_list_label.pack()
        
        # Butonlar frame
        button_frame = tk.Frame(pdf_list_frame, bg=self.colors['card_bg'])
        button_frame.pack()
        
        # PDF Seç butonu
        select_btn = tk.Button(button_frame,
                             text="📁 PDF Seç (Maks. 3)",
                             font=('Segoe UI', 12, 'bold'),
                             bg=self.colors['primary'],
                             fg='white',
                             bd=0,
                             padx=40,
                             pady=12,
                             cursor='hand2',
                             command=self.select_pdfs)
        select_btn.pack(side=tk.LEFT, padx=5)
        
        # Temizle butonu
        self.clear_btn = tk.Button(button_frame,
                                  text="🗑️ Temizle",
                                  font=('Segoe UI', 12),
                                  bg=self.colors['danger'],
                                  fg='white',
                                  bd=0,
                                  padx=30,
                                  pady=12,
                                  cursor='hand2',
                                  state=tk.DISABLED,
                                  command=self.clear_pdfs)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Desteklenen formatlar
        info_frame = tk.Frame(tab, bg=self.colors['card_bg'])
        info_frame.pack(pady=(20, 0))
        
        tk.Label(info_frame,
                text="Desteklenen PDF Tipleri:",
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.colors['text']).pack()
        
        types = [
            "✓ Normal Fiyat Listesi",
            "✓ Gramajlı/Soslu Ürünler Listesi",
            "✓ Dondurulmuş Ürünler Listesi"
        ]
        
        for type_text in types:
            tk.Label(info_frame,
                    text=type_text,
                    font=('Segoe UI', 10),
                    bg=self.colors['card_bg'],
                    fg=self.colors['success']).pack()
    
    def create_discount_tab(self):
        """İskonto ayarları tabı"""
        tab = tk.Frame(self.tab_container, bg=self.colors['card_bg'])
        self.tabs['discount'] = tab
        
        # Başlık
        title = tk.Label(tab,
                        text="İskonto Oranlarını Ayarlayın",
                        font=('Segoe UI', 16, 'bold'),
                        bg=self.colors['card_bg'],
                        fg=self.colors['text'])
        title.pack(pady=(0, 20))
        
        # Not
        note_label = tk.Label(tab,
                            text="Not: Belirlenen iskonto oranları tüm yüklenen PDF dosyalarına uygulanacaktır.",
                            font=('Segoe UI', 10, 'italic'),
                            bg=self.colors['card_bg'],
                            fg=self.colors['warning'])
        note_label.pack(pady=(0, 10))
        
        # Hızlı ayar butonları
        quick_frame = tk.Frame(tab, bg=self.colors['card_bg'])
        quick_frame.pack(pady=(0, 20))
        
        tk.Label(quick_frame,
                text="Hızlı Ayar:",
                font=('Segoe UI', 11),
                bg=self.colors['card_bg'],
                fg=self.colors['text']).pack(side=tk.LEFT, padx=(0, 10))
        
        for value in [5, 10, 15, 20]:
            btn = tk.Button(quick_frame,
                          text=f"Tümü %{value}",
                          font=('Segoe UI', 10),
                          bg=self.colors['border'],
                          fg=self.colors['text'],
                          bd=0,
                          padx=20,
                          pady=8,
                          cursor='hand2',
                          command=lambda v=value: self.set_all_discounts(v))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Sıfırla butonu
        reset_btn = tk.Button(quick_frame,
                            text="Sıfırla",
                            font=('Segoe UI', 10),
                            bg=self.colors['danger'],
                            fg='white',
                            bd=0,
                            padx=20,
                            pady=8,
                            cursor='hand2',
                            command=lambda: self.set_all_discounts(0))
        reset_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Kategori kartları grid
        categories_frame = tk.Frame(tab, bg=self.colors['card_bg'])
        categories_frame.pack(fill=tk.BOTH, expand=True, padx=40)
        
        categories = [
            ('Bütün Piliç Ürünleri', '🐔'),
            ('Kanat Ürünleri', '🍗'),
            ('But Ürünleri', '🍖'),
            ('Göğüs Ürünleri', '🥩'),
            ('Sakatat Ürünleri', '🫀'),
            ('Yan Ürünler', '📦')
        ]
        
        self.discount_vars = {}
        self.category_cards = {}
        
        for i, (category, icon) in enumerate(categories):
            row = i // 2
            col = i % 2
            
            # Kart
            card = tk.Frame(categories_frame,
                          bg=self.colors['hover'],
                          bd=1,
                          relief='solid')
            card.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            # İkon ve başlık
            header = tk.Frame(card, bg=self.colors['hover'])
            header.pack(fill=tk.X, padx=15, pady=(15, 10))
            
            tk.Label(header,
                    text=icon,
                    font=('Segoe UI', 20),
                    bg=self.colors['hover']).pack(side=tk.LEFT, padx=(0, 10))
            
            tk.Label(header,
                    text=category,
                    font=('Segoe UI', 11, 'bold'),
                    bg=self.colors['hover'],
                    fg=self.colors['text']).pack(side=tk.LEFT)
            
            # Ürün sayısı etiketi
            count_label = tk.Label(header,
                                 text="(0 ürün)",
                                 font=('Segoe UI', 9),
                                 bg=self.colors['hover'],
                                 fg=self.colors['text_light'])
            count_label.pack(side=tk.LEFT, padx=(5, 0))
            
            # İskonto girişi
            input_frame = tk.Frame(card, bg=self.colors['hover'])
            input_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
            
            tk.Label(input_frame,
                    text="İskonto %:",
                    font=('Segoe UI', 10),
                    bg=self.colors['hover'],
                    fg=self.colors['text_light']).pack(side=tk.LEFT)
            
            var = tk.DoubleVar(value=0.0)
            entry = tk.Entry(input_frame,
                           textvariable=var,
                           font=('Segoe UI', 11),
                           width=10,
                           bd=1,
                           relief='solid')
            entry.pack(side=tk.RIGHT)
            
            self.discount_vars[category] = var
            self.category_cards[category] = {
                'card': card,
                'count_label': count_label,
                'entry': entry
            }
        
        # Grid ayarları
        categories_frame.columnconfigure(0, weight=1)
        categories_frame.columnconfigure(1, weight=1)
    
    def create_preview_tab(self):
        """Önizleme tabı"""
        tab = tk.Frame(self.tab_container, bg=self.colors['card_bg'])
        self.tabs['preview'] = tab
        
        # Başlık ve butonlar
        header = tk.Frame(tab, bg=self.colors['card_bg'])
        header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header,
                text="Fiyat Listesi Önizleme",
                font=('Segoe UI', 16, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        # Önizleme butonu
        preview_btn = tk.Button(header,
                              text="🔄 Yenile",
                              font=('Segoe UI', 10),
                              bg=self.colors['primary'],
                              fg='white',
                              bd=0,
                              padx=20,
                              pady=8,
                              cursor='hand2',
                              command=self.preview_data)
        preview_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Önizleme alanı
        preview_frame = tk.Frame(tab, bg='white', bd=1, relief='solid')
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(preview_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preview_text = tk.Text(preview_frame,
                                   wrap=tk.WORD,
                                   font=('Consolas', 10),
                                   bg='white',
                                   fg=self.colors['text'],
                                   yscrollcommand=scrollbar.set)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.config(command=self.preview_text.yview)
        
        # Başlangıç mesajı
        self.show_welcome_message()
    
    def create_stats_tab(self):
        """İstatistikler tabı"""
        tab = tk.Frame(self.tab_container, bg=self.colors['card_bg'])
        self.tabs['stats'] = tab
        
        # Başlık
        tk.Label(tab,
                text="İstatistikler ve Özet",
                font=('Segoe UI', 16, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.colors['text']).pack(pady=(0, 20))
        
        # İstatistik kartları
        stats_container = tk.Frame(tab, bg=self.colors['card_bg'])
        stats_container.pack(fill=tk.BOTH, expand=True, padx=40)
        
        self.stat_cards = {}
        
        stats_info = [
            ('Yüklenen PDF', '📄', '0'),
            ('Toplam Ürün', '📦', '0'),
            ('İşlenen Kategori', '📊', '0'),
            ('Ortalama İskonto', '💰', '%0'),
            ('Toplam İskonto', '💵', '0 TL'),
            ('Toplam Kayıt', '💾', '0')
        ]
        
        for i, (title, icon, value) in enumerate(stats_info):
            card = tk.Frame(stats_container,
                          bg=self.colors['hover'],
                          bd=1,
                          relief='solid')
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky='ew')
            
            # İçerik
            content = tk.Frame(card, bg=self.colors['hover'])
            content.pack(padx=20, pady=20)
            
            tk.Label(content,
                    text=icon,
                    font=('Segoe UI', 32),
                    bg=self.colors['hover']).pack()
            
            value_label = tk.Label(content,
                                 text=value,
                                 font=('Segoe UI', 20, 'bold'),
                                 bg=self.colors['hover'],
                                 fg=self.colors['primary'])
            value_label.pack(pady=(5, 0))
            
            tk.Label(content,
                    text=title,
                    font=('Segoe UI', 11),
                    bg=self.colors['hover'],
                    fg=self.colors['text_light']).pack()
            
            self.stat_cards[title] = value_label
        
        stats_container.columnconfigure(0, weight=1)
        stats_container.columnconfigure(1, weight=1)
        stats_container.columnconfigure(2, weight=1)
    
    def create_control_panel(self, parent):
        """Alt kontrol paneli"""
        control_frame = tk.Frame(parent, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Sol taraf - durum
        self.status_label = tk.Label(control_frame,
                                    text="PDF dosyalarını seçerek başlayın",
                                    font=('Segoe UI', 11),
                                    bg=self.colors['bg'],
                                    fg=self.colors['text_light'])
        self.status_label.pack(side=tk.LEFT)
        
        # Sağ taraf - dışa aktarma butonları
        export_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        export_frame.pack(side=tk.RIGHT)
        
        # Excel butonu
        self.excel_btn = tk.Button(export_frame,
                                  text="📊 Excel'e Aktar",
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['success'],
                                  fg='white',
                                  bd=0,
                                  padx=25,
                                  pady=10,
                                  cursor='hand2',
                                  state=tk.DISABLED,
                                  command=lambda: self.export_data('excel'))
        self.excel_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # PDF butonu - Çoklu PDF kaydetme
        self.pdf_btn = tk.Button(export_frame,
                                text="📄 PDF'lere Aktar",
                                font=('Segoe UI', 11, 'bold'),
                                bg=self.colors['danger'],
                                fg='white',
                                bd=0,
                                padx=25,
                                pady=10,
                                cursor='hand2',
                                state=tk.DISABLED,
                                command=lambda: self.export_data('pdf'))
        self.pdf_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Her ikisi butonu
        self.both_btn = tk.Button(export_frame,
                                 text="📊📄 Her İkisi",
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=self.colors['primary'],
                                 fg='white',
                                 bd=0,
                                 padx=25,
                                 pady=10,
                                 cursor='hand2',
                                 state=tk.DISABLED,
                                 command=lambda: self.export_data('both'))
        self.both_btn.pack(side=tk.LEFT)
    
    def create_progress_bar(self, parent):
        """İlerleme çubuğu"""
        self.progress_frame = tk.Frame(parent, bg=self.colors['bg'])
        self.progress_frame.pack(fill=tk.X, pady=(10, 0))
        self.progress_frame.pack_forget()  # Başlangıçta gizli
        
        # Progress bar container
        progress_bg = tk.Frame(self.progress_frame,
                             bg=self.colors['border'],
                             height=8)
        progress_bg.pack(fill=tk.X)
        
        self.progress_fill = tk.Frame(progress_bg,
                                     bg=self.colors['primary'],
                                     height=8)
        self.progress_fill.place(x=0, y=0, relheight=1, relwidth=0)
        
        # Progress text
        self.progress_text = tk.Label(self.progress_frame,
                                     text="İşlem yapılıyor...",
                                     font=('Segoe UI', 10),
                                     bg=self.colors['bg'],
                                     fg=self.colors['primary'])
        self.progress_text.pack(pady=(5, 0))
    
    def show_welcome_message(self):
        """Hoşgeldin mesajı"""
        self.preview_text.delete(1.0, tk.END)
        welcome = """
╔════════════════════════════════════════════════════════════════╗
║           BUPİLİÇ İSKONTOLU FİYAT HESAPLAYICI v3.0           ║
╚════════════════════════════════════════════════════════════════╝

KULLANIM ADIMLARI:
─────────────────
1. PDF sekmesinden fiyat listesi PDF'lerini seçin (Maks. 3 adet)
2. İskonto sekmesinden oranları ayarlayın
3. Önizleme sekmesinden sonuçları kontrol edin
4. Excel veya PDF olarak dışa aktarın

YENİ ÖZELLİKLER:
──────────────
✓ Çoklu PDF desteği (1-3 adet)
✓ Her PDF için ayrı önizleme
✓ Excel'de her PDF için ayrı sheet
✓ PDF'lerde otomatik isimlendirme

Başlamak için PDF sekmesine gidin...
"""
        self.preview_text.insert(1.0, welcome)
    
    def select_pdfs(self):
        """Çoklu PDF seçimi"""
        if len(self.pdf_files) >= self.max_pdf_count:
            messagebox.showwarning("Uyarı", f"Maksimum {self.max_pdf_count} PDF yükleyebilirsiniz!")
            return
        
        remaining = self.max_pdf_count - len(self.pdf_files)
        
        file_paths = filedialog.askopenfilenames(
            title=f"PDF Dosyaları Seç (Maks. {remaining} adet)",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_paths:
            # Maksimum sayıyı kontrol et
            if len(file_paths) + len(self.pdf_files) > self.max_pdf_count:
                messagebox.showwarning("Uyarı", 
                                     f"Maksimum {self.max_pdf_count} PDF yükleyebilirsiniz!\n"
                                     f"İlk {remaining} dosya yüklenecek.")
                file_paths = file_paths[:remaining]
            
            self.show_progress(f"{len(file_paths)} PDF işleniyor...")
            
            # Thread ile işle
            thread = threading.Thread(target=self.process_multiple_pdfs, args=(file_paths,))
            thread.daemon = True
            thread.start()
    
    def process_multiple_pdfs(self, file_paths):
        """Birden fazla PDF'i işle"""
        try:
            success_count = 0
            
            for file_path in file_paths:
                # PDF tipini belirle
                pdf_type = self.determine_pdf_type(file_path)
                
                # Yeni processor oluştur
                processor = PDFProcessor()
                
                # PDF işle
                success = processor.extract_data_from_pdf(file_path, pdf_type)
                
                if success:
                    # PDF bilgilerini sakla
                    pdf_info = {
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'type': pdf_type,
                        'processor': processor,
                        'product_count': processor.get_product_count()
                    }
                    
                    self.pdf_files.append(pdf_info)
                    self.pdf_processors.append(processor)
                    success_count += 1
                    
                    logging.info(f"PDF başarıyla yüklendi: {pdf_info['name']} - {pdf_info['product_count']} ürün")
            
            # UI güncellemesi
            self.root.after(0, self.update_after_multiple_pdf_processing, success_count)
            
        except Exception as e:
            logging.error(f"Çoklu PDF işleme hatası: {e}")
            self.root.after(0, lambda: self.show_error(f"PDF işleme hatası: {str(e)}"))
    
    def determine_pdf_type(self, file_path):
        """PDF tipini belirle"""
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages[:2]:
                    text += (page.extract_text() or "").lower()
                
                if 'dondurulmuş' in text or 'don.' in text:
                    return 'dondurulmus'
                elif 'gramaj' in text or 'soslu' in text:
                    return 'gramaj'
                else:
                    return 'normal'
        except:
            return 'normal'
    
    def update_after_multiple_pdf_processing(self, success_count):
        """Çoklu PDF işleme sonrası güncelleme"""
        self.hide_progress()
        
        if success_count > 0:
            self.pdf_loaded = True
            self.status_label.config(text=f"✓ {len(self.pdf_files)} PDF yüklendi")
            
            # PDF listesini güncelle
            self.update_pdf_list()
            
            # Kategori sayılarını güncelle (tüm PDF'lerdeki toplam)
            self.update_category_counts()
            
            # İstatistikleri güncelle
            self.update_statistics()
            
            # Temizle butonunu aktif et
            self.clear_btn.config(state=tk.NORMAL)
            
            # İskonto sekmesine geç
            self.show_tab('discount')
            
            total_products = sum(pdf['product_count'] for pdf in self.pdf_files)
            messagebox.showinfo("Başarılı", 
                              f"{success_count} PDF başarıyla yüklendi!\n"
                              f"Toplam {total_products} ürün bulundu.\n"
                              f"Şimdi iskonto oranlarını ayarlayabilirsiniz.")
        else:
            self.show_error("PDF'ler işlenirken hata oluştu!")
    
    def update_pdf_list(self):
        """Yüklenen PDF listesini güncelle"""
        # Eski listeyi temizle
        for widget in self.pdf_list_container.winfo_children():
            widget.destroy()
        
        if not self.pdf_files:
            self.empty_list_label = tk.Label(self.pdf_list_container,
                                            text="Henüz PDF yüklenmedi",
                                            font=('Segoe UI', 11),
                                            bg=self.colors['hover'],
                                            fg=self.colors['text_light'],
                                            pady=30)
            self.empty_list_label.pack()
            return
        
        # PDF'leri listele
        for i, pdf_info in enumerate(self.pdf_files, 1):
            pdf_frame = tk.Frame(self.pdf_list_container, bg='white', bd=1, relief='solid')
            pdf_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # PDF numarası ve ismi
            info_text = f"{i}. {pdf_info['name']}"
            name_label = tk.Label(pdf_frame,
                                text=info_text,
                                font=('Segoe UI', 11, 'bold'),
                                bg='white',
                                fg=self.colors['text'])
            name_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            # PDF tipi ve ürün sayısı
            type_text = {
                'normal': 'Normal',
                'dondurulmus': 'Dondurulmuş',
                'gramaj': 'Gramajlı/Soslu'
            }
            
            details_text = f"({type_text.get(pdf_info['type'], 'Normal')} - {pdf_info['product_count']} ürün)"
            details_label = tk.Label(pdf_frame,
                                   text=details_text,
                                   font=('Segoe UI', 10),
                                   bg='white',
                                   fg=self.colors['text_light'])
            details_label.pack(side=tk.LEFT, padx=5)
            
            # Durum ikonu
            status_label = tk.Label(pdf_frame,
                                  text="✓",
                                  font=('Segoe UI', 16),
                                  bg='white',
                                  fg=self.colors['success'])
            status_label.pack(side=tk.RIGHT, padx=10)
    
    def update_category_counts(self):
        """Tüm PDF'lerdeki kategori sayılarını güncelle"""
        total_counts = {}
        
        for pdf_info in self.pdf_files:
            processor = pdf_info['processor']
            for category, products in processor.categories.items():
                if category not in total_counts:
                    total_counts[category] = 0
                total_counts[category] += len(products)
        
        # UI'daki kategori sayılarını güncelle
        for category, info in self.category_cards.items():
            count = total_counts.get(category, 0)
            info['count_label'].config(text=f"({count} ürün)")
    
    def clear_pdfs(self):
        """Yüklenen PDF'leri temizle"""
        if messagebox.askyesno("Onay", "Tüm yüklenen PDF'leri temizlemek istediğinize emin misiniz?"):
            self.pdf_files = []
            self.pdf_processors = []
            self.current_data_all = {}
            self.pdf_loaded = False
            
            # UI güncelle
            self.update_pdf_list()
            self.update_category_counts()
            self.update_statistics()
            
            self.clear_btn.config(state=tk.DISABLED)
            self.status_label.config(text="PDF dosyalarını seçerek başlayın")
            
            # Dışa aktarma butonlarını devre dışı bırak
            self.excel_btn.config(state=tk.DISABLED)
            self.pdf_btn.config(state=tk.DISABLED)
            self.both_btn.config(state=tk.DISABLED)
            
            # Önizlemeyi temizle
            self.show_welcome_message()
    
    def set_all_discounts(self, value):
        """Tüm iskonto oranlarını ayarla"""
        for var in self.discount_vars.values():
            var.set(value)
        
        if self.pdf_loaded:
            self.preview_data()
    
    def preview_data(self):
        """Çoklu PDF önizleme"""
        if not self.pdf_loaded or not self.pdf_files:
            messagebox.showwarning("Uyarı", "Önce PDF dosyaları yükleyin!")
            return
        
        try:
            # İskonto oranlarını al
            discount_rates = {}
            for category, var in self.discount_vars.items():
                rate = var.get()
                if rate < 0 or rate > 100:
                    messagebox.showwarning("Uyarı", 
                                         f"{category} için iskonto oranı 0-100 arasında olmalıdır!")
                    return
                discount_rates[category] = rate
            
            # Her PDF için iskontoları uygula
            self.current_data_all = {}
            
            for pdf_info in self.pdf_files:
                processor = pdf_info['processor']
                discounted_data = processor.apply_discounts(discount_rates)
                
                if discounted_data:
                    self.current_data_all[pdf_info['name']] = {
                        'data': discounted_data,
                        'type': pdf_info['type'],
                        'path': pdf_info['path']
                    }
            
            if not self.current_data_all:
                messagebox.showwarning("Uyarı", "İşlenecek veri bulunamadı!")
                return
            
            # Önizlemeyi güncelle
            self.update_multi_preview()
            
            # Dışa aktarma butonlarını aktif et
            self.excel_btn.config(state=tk.NORMAL)
            self.pdf_btn.config(state=tk.NORMAL)
            self.both_btn.config(state=tk.NORMAL)
            
            # İstatistikleri güncelle
            self.update_statistics()
            
            # Önizleme sekmesine geç
            self.show_tab('preview')
            
        except Exception as e:
            logging.error(f"Önizleme hatası: {e}")
            self.show_error(f"Önizleme hatası: {str(e)}")
    
    def update_multi_preview(self):
        """Çoklu PDF önizlemesini güncelle"""
        self.preview_text.delete(1.0, tk.END)
        
        preview_text = "BUPİLİÇ İSKONTOLU FİYAT LİSTELERİ\n"
        preview_text += "=" * 100 + "\n"
        preview_text += f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        preview_text += f"Yüklenen PDF Sayısı: {len(self.pdf_files)}\n\n"
        
        grand_total_products = 0
        grand_total_discount = 0
        
        # Her PDF için önizleme
        for pdf_idx, (pdf_name, pdf_data) in enumerate(self.current_data_all.items(), 1):
            preview_text += f"\n{'#'*100}\n"
            preview_text += f"PDF {pdf_idx}: {pdf_name}\n"
            preview_text += f"{'#'*100}\n\n"
            
            pdf_total_products = 0
            pdf_total_discount = 0
            
            for category, products in pdf_data['data'].items():
                if not products:
                    continue
                
                discount_rate = self.discount_vars[category].get()
                
                preview_text += f"{'='*100}\n"
                preview_text += f"{category.upper()} - %{discount_rate:.1f} İSKONTO ({len(products)} ÜRÜN)\n"
                preview_text += f"{'='*100}\n"
                
                preview_text += f"{'ÜRÜN ADI':<50} {'ORJ.KDV HARİÇ':>13} {'ORJ.KDV DAHİL':>13} "
                preview_text += f"{'İSK.KDV HARİÇ':>13} {'İSK.KDV DAHİL':>13}\n"
                preview_text += "-" * 100 + "\n"
                
                category_discount = 0
                for product in products:
                    name = product['name'][:47] + "..." if len(product['name']) > 47 else product['name']
                    
                    orig_without = product.get('original_price_without_vat', 0)
                    orig_with = product.get('original_price_with_vat', 0)
                    disc_without = product['price_without_vat']
                    disc_with = product['price_with_vat']
                    
                    discount_amt = orig_with - disc_with
                    category_discount += discount_amt
                    
                    preview_text += f"{name:<50} {orig_without:>13.2f} {orig_with:>13.2f} "
                    preview_text += f"{disc_without:>13.2f} {disc_with:>13.2f}\n"
                
                preview_text += f"\n{' '*50} Kategori İskonto Toplamı: {category_discount:>39.2f} TL\n\n"
                
                pdf_total_products += len(products)
                pdf_total_discount += category_discount
            
            # PDF özeti
            preview_text += f"{'─'*100}\n"
            preview_text += f"PDF ÖZET: {pdf_name}\n"
            preview_text += f"Toplam Ürün: {pdf_total_products} | Toplam İskonto: {pdf_total_discount:.2f} TL\n"
            preview_text += f"{'─'*100}\n\n"
            
            grand_total_products += pdf_total_products
            grand_total_discount += pdf_total_discount
        
        # Genel özet
        preview_text += f"\n{'='*100}\n"
        preview_text += "GENEL ÖZET\n"
        preview_text += f"{'='*100}\n"
        preview_text += f"İşlenen PDF Sayısı    : {len(self.pdf_files)}\n"
        preview_text += f"Toplam Ürün Sayısı    : {grand_total_products}\n"
        preview_text += f"Toplam İskonto Tutarı : {grand_total_discount:.2f} TL\n"
        preview_text += f"{'='*100}\n"
        
        self.preview_text.insert(1.0, preview_text)
    
    def update_statistics(self):
        """İstatistikleri güncelle"""
        if self.current_data_all:
            total_pdfs = len(self.pdf_files)
            total_products = 0
            total_categories = set()
            total_discount = 0
            total_rates = []
            
            for pdf_data in self.current_data_all.values():
                for category, products in pdf_data['data'].items():
                    if products:
                        total_categories.add(category)
                        total_products += len(products)
                        
                        rate = self.discount_vars[category].get()
                        if rate not in total_rates:
                            total_rates.append(rate)
                        
                        for product in products:
                            orig = product.get('original_price_with_vat', 0)
                            disc = product['price_with_vat']
                            total_discount += (orig - disc)
            
            avg_discount = sum(total_rates) / len(total_rates) if total_rates else 0
            
            self.stat_cards['Yüklenen PDF'].config(text=str(total_pdfs))
            self.stat_cards['Toplam Ürün'].config(text=str(total_products))
            self.stat_cards['İşlenen Kategori'].config(text=str(len(total_categories)))
            self.stat_cards['Ortalama İskonto'].config(text=f"%{avg_discount:.1f}")
            self.stat_cards['Toplam İskonto'].config(text=f"{total_discount:.2f} TL")
            self.stat_cards['Toplam Kayıt'].config(text=str(total_products))
        else:
            # Varsayılan değerler
            self.stat_cards['Yüklenen PDF'].config(text=str(len(self.pdf_files)))
            self.stat_cards['Toplam Ürün'].config(text="0")
            self.stat_cards['İşlenen Kategori'].config(text="0")
            self.stat_cards['Ortalama İskonto'].config(text="%0")
            self.stat_cards['Toplam İskonto'].config(text="0 TL")
            self.stat_cards['Toplam Kayıt'].config(text="0")
    
    def export_data(self, export_type):
        """Çoklu PDF dışa aktarma"""
        if not self.current_data_all:
            messagebox.showwarning("Uyarı", "Önce önizleme yapın!")
            return
        
        try:
            if export_type == 'excel':
                # Excel'e aktar - tek dosya, çoklu sheet
                self.export_manager.export_to_excel_multi(self.current_data_all, self.discount_vars)
            elif export_type == 'pdf':
                # Her PDF için ayrı dosya oluştur
                self.export_manager.export_to_pdf_multi(self.current_data_all, self.discount_vars)
            elif export_type == 'both':
                self.export_manager.export_to_excel_multi(self.current_data_all, self.discount_vars)
                self.export_manager.export_to_pdf_multi(self.current_data_all, self.discount_vars)
        except Exception as e:
            logging.error(f"Dışa aktarma hatası: {e}")
            self.show_error(f"Dışa aktarma hatası: {str(e)}")
    
    def show_progress(self, text):
        """İlerleme göster"""
        self.progress_frame.pack(fill=tk.X, pady=(10, 0))
        self.progress_text.config(text=text)
        self.progress_fill.place(relwidth=0.5)
    
    def hide_progress(self):
        """İlerleme gizle"""
        self.progress_frame.pack_forget()
    
    def show_error(self, message):
        """Hata mesajı"""
        messagebox.showerror("Hata", message)
        self.status_label.config(text="❌ İşlem başarısız")