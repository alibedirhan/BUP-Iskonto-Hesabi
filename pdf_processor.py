# pdf_processor.py - ÇOKLU PDF DESTEĞİ EKLENDİ
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional
import logging
import os

class PDFProcessor:
    def __init__(self):
        self.categories = {
            'Bütün Piliç Ürünleri': [],
            'Kanat Ürünleri': [],
            'But Ürünleri': [],
            'Göğüs Ürünleri': [],
            'Sakatat Ürünleri': [],
            'Yan Ürünler': []
        }
        self.raw_data = []
        self.processed_codes = set()
        self.pdf_files = {}  # PDF dosya ismi -> işlenen veriler
        self.setup_logging()
        
        # Performans için regex pattern'leri önceden derle
        self.code_pattern = re.compile(r'^(D?[A-Z]{2,4}\d{3}(?:\.\d{2})?(?:\.\d{1,2})?(?:\-\d)?)\s*$')
        self.price_pattern = re.compile(r'(\d{2,3}[,\.]\d{2})')
        
    def setup_logging(self):
        """Loglama mekanizması kur"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pdf_processor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def extract_data_from_pdf(self, pdf_path: str, pdf_type: str = "normal") -> bool:
        """PDF'den veri çıkarır - İyileştirilmiş hata yönetimi ile"""
        try:
            logging.info(f"PDF işleniyor: {pdf_path}, Tip: {pdf_type}")
            self.clear_data()
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    logging.info(f"Sayfa {page_num + 1} işleniyor...")
                    
                    # Önce tabloları dene
                    tables = page.extract_tables()
                    if tables:
                        logging.info(f"Sayfa {page_num + 1}'de {len(tables)} tablo bulundu")
                        self._process_tables(tables, pdf_type, page_num + 1)
                    else:
                        # Fallback: Metin bazlı çıkarma
                        self._process_text(page, pdf_type, page_num + 1)
                
                self._print_results()
                return True
                
        except FileNotFoundError:
            logging.error(f"PDF dosyası bulunamadı: {pdf_path}")
            return False
        except PermissionError:
            logging.error(f"PDF dosyasına erişim izni yok: {pdf_path}")
            return False
        except Exception as e:
            logging.error(f"PDF işleme hatası: {type(e).__name__}: {e}", exc_info=True)
            return False
    
    def _process_tables(self, tables: List, pdf_type: str, page_num: int):
        """Tabloları işle"""
        for table_idx, table in enumerate(tables):
            for row_idx, row in enumerate(table):
                if row and any(cell for cell in row if cell):
                    self._parse_table_row(row, pdf_type, page_num, f"Tablo-{table_idx}-Satır-{row_idx}")
    
    def _process_text(self, page, pdf_type: str, page_num: int):
        """Metin bazlı işleme"""
        text = page.extract_text()
        if text:
            logging.info(f"Sayfa {page_num}'de metin işleniyor...")
            for line_idx, line in enumerate(text.split('\n')):
                if line.strip():
                    self._parse_text_line(line, pdf_type, page_num, line_idx)
    
    def _parse_table_row(self, row: List, pdf_type: str, page_num: int, row_info: str):
        """Tablo satırını parse eder - İyileştirilmiş versiyon"""
        if not row or len(row) < 3:
            return
        
        # Ürün kodu kontrolü - ilk üç sütunu kontrol et
        for i in range(min(3, len(row))):
            if not row[i]:
                continue
                
            cell = str(row[i]).strip()
            match = self.code_pattern.match(cell)
            
            if match:
                product_code = match.group(1).strip()
                
                # Duplikasyon kontrolü - ürün kodu + kategori kombinasyonu
                category = self._determine_category_by_position(product_code, row_info, page_num)
                
                if not category:
                    logging.debug(f"KATEGORİ BULUNAMADI: {product_code}")
                    continue
                
                duplicate_key = f"{product_code}-{category}"
                if duplicate_key in self.processed_codes:
                    logging.debug(f"DUPLIKASYON: {product_code} {category}'de zaten işlendi")
                    continue
                
                # Ürün adını bul
                product_name = self._extract_product_name(row, i, pdf_type)
                
                # Fiyatları bul - İyileştirilmiş algoritma
                price_without_vat, price_with_vat = self._extract_prices_from_row(row, i + 2)
                
                if product_name and price_without_vat and price_with_vat:
                    # KDV oranını kontrol et (%1 olmalı)
                    kdv_rate = (price_with_vat / price_without_vat - 1) * 100
                    if not (0.5 <= kdv_rate <= 1.5):  # %1 KDV toleransı
                        logging.warning(f"Anormal KDV oranı {kdv_rate:.2f}% - {product_code}: {price_without_vat} / {price_with_vat}")
                    
                    product = {
                        'code': product_code,
                        'name': self._clean_product_name(product_name),
                        'price_without_vat': price_without_vat,
                        'price_with_vat': price_with_vat,
                        'category': category
                    }
                    
                    self.categories[category].append(product)
                    self.processed_codes.add(duplicate_key)
                    logging.info(f"✓ [{pdf_type} - {category}] {product['name']}: {price_without_vat:.2f} / {price_with_vat:.2f}")
                    break
    
    def _extract_product_name(self, row: List, code_index: int, pdf_type: str) -> str:
        """Ürün adını çıkar"""
        if code_index + 1 < len(row) and row[code_index + 1]:
            product_name = str(row[code_index + 1]).strip()
            
            if pdf_type == "dondurulmus":
                product_name = product_name.replace("DON.", "DONDURULMUŞ")
            
            return product_name
        return ""
    
    def _extract_prices_from_row(self, row: List, start_index: int) -> Tuple[Optional[float], Optional[float]]:
        """Satırdan fiyatları çıkar - İyileştirilmiş algoritma"""
        prices = []
        
        for j in range(start_index, len(row)):
            if row[j]:
                cell_value = str(row[j]).strip()
                
                # Fark sütununu atla (% içeren değerler)
                if '%' in cell_value or 'fark' in cell_value.lower():
                    continue
                
                price = self._extract_price_from_text(cell_value)
                if price and 5 <= price <= 2000:  # Genişletilmiş fiyat aralığı
                    prices.append(price)
        
        if len(prices) < 2:
            return None, None
        
        # PDF'de KDV hariç sonra KDV dahil gelir - son iki geçerli fiyatı al
        price_without_vat = prices[-2] if len(prices) >= 2 else prices[0]
        price_with_vat = prices[-1]
        
        # KDV dahil fiyatın daha yüksek olması gerekir
        if price_without_vat > price_with_vat:
            price_without_vat, price_with_vat = price_with_vat, price_without_vat
        
        return price_without_vat, price_with_vat
    
    def _determine_category_by_position(self, product_code: str, row_info: str, page_num: int) -> Optional[str]:
        """PDF'deki konuma ve ürün koduna göre kategori belirler"""
        
        # Tablo numarasından kategori belirleme
        table_match = re.search(r'Tablo-(\d+)', row_info)
        if table_match:
            table_num = int(table_match.group(1))
            
            # PDF'deki tablo sıralamasına göre kategori mapping
            table_category_map = {
                0: 'Bütün Piliç Ürünleri',    # İlk tablo - sol taraf DÖKME
                1: 'Bütün Piliç Ürünleri',    # İkinci tablo - sağ taraf POŞET/TABAK
                2: 'Kanat Ürünleri',          # Üçüncü tablo - sol taraf DÖKME kanat
                3: 'Kanat Ürünleri',          # Dördüncü tablo - sağ taraf TABAK kanat
                4: 'But Ürünleri',            # Beşinci tablo - sol taraf DÖKME but
                5: 'But Ürünleri',            # Altıncı tablo - sağ taraf TABAK but
                6: 'Göğüs Ürünleri',          # Yedinci tablo - sol taraf DÖKME göğüs
                7: 'Göğüs Ürünleri',          # Sekizinci tablo - sağ taraf TABAK göğüs
                8: 'Sakatat Ürünleri',        # Dokuzuncu tablo - sol taraf DÖKME sakatat
                9: 'Sakatat Ürünleri',        # Onuncu tablo - sağ taraf TABAK sakatat
                10: 'Yan Ürünler',            # On birinci tablo - sol taraf DÖKME yan
                11: 'Yan Ürünler',            # On ikinci tablo - sağ taraf POŞET yan
            }
            
            if table_num in table_category_map:
                return table_category_map[table_num]
        
        # Fallback: Ürün koduna göre kategori belirleme
        return self._determine_category_by_code(product_code)
    
    def _determine_category_by_code(self, product_code: str) -> Optional[str]:
        """Ürün koduna göre kategori belirler"""
        code_upper = product_code.upper()
        
        # Kategori mapping
        code_mapping = {
            # Normal kodlar
            'BTN': 'Bütün Piliç Ürünleri',
            'KNT': 'Kanat Ürünleri',
            'BUT': 'But Ürünleri',
            'GGS': 'Göğüs Ürünleri',
            'SAK': 'Sakatat Ürünleri',
            'YAN': 'Yan Ürünler',
            # Dondurulmuş kodlar
            'DBTN': 'Bütün Piliç Ürünleri',
            'DKNT': 'Kanat Ürünleri',
            'DBUT': 'But Ürünleri',
            'DGGS': 'Göğüs Ürünleri',
            'DSAK': 'Sakatat Ürünleri',
            'DYAN': 'Yan Ürünler'
        }
        
        # Önce tam eşleşme dene
        for prefix in code_mapping:
            if code_upper.startswith(prefix):
                return code_mapping[prefix]
        
        return None
    
    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Metinden fiyat değeri çıkarır"""
        try:
            text = text.strip()
            
            # % işareti içeriyorsa atla (Fark sütunu)
            if '%' in text or 'fark' in text.lower():
                return None
                
            # Sadece rakam, virgül ve nokta bırak
            cleaned = re.sub(r'[^\d,\.]', '', text)
            
            if not cleaned:
                return None
            
            # Virgül ve nokta düzeltmeleri
            if ',' in cleaned:
                cleaned = cleaned.replace(',', '.')
            
            value = float(cleaned)
            
            # Mantıklı fiyat aralığı
            if 5 <= value <= 2000:
                return value
            
            return None
        except (ValueError, TypeError):
            return None
    
    def _clean_product_name(self, name: str) -> str:
        """Ürün adını temizler"""
        # Gereksiz karakterleri temizle
        name = re.sub(r'[%\*]+', '', name)
        name = re.sub(r'Fark.*', '', name)
        name = re.sub(r'Kdv.*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Kısaltmaları düzelt
        replacements = {
            'DON.': 'DONDURULMUŞ',
            'TB': 'TABAK',
            'GR': 'GRAM'
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        return name.strip()
    
    def _parse_text_line(self, line: str, pdf_type: str, page_num: int, line_idx: int):
        """Metin satırını parse eder - Fallback method"""
        line = line.strip()
        if not line or len(line) < 20:
            return
        
        code_matches = list(self.code_pattern.finditer(line))
        
        for match in code_matches:
            product_code = match.group(1).strip()
            category = self._determine_category_by_code(product_code)
            
            if not category:
                continue
            
            duplicate_key = f"{product_code}-{category}"
            if duplicate_key in self.processed_codes:
                continue
            
            # Koddan sonraki kısmı al
            start_pos = match.end()
            remaining = line[start_pos:].strip()
            
            # Fiyatları çıkar
            price_matches = self.price_pattern.findall(remaining)
            prices = []
            
            for price_str in price_matches[-2:]:  # Son iki fiyat
                if '%' not in price_str:
                    price = self._extract_price_from_text(price_str)
                    if price and 10 <= price <= 2000:
                        prices.append(price)
            
            if len(prices) < 2:
                continue
            
            price_without_vat, price_with_vat = prices[0], prices[1]
            
            # Ürün adını çıkar
            product_name = remaining
            for price_str in price_matches:
                product_name = product_name.replace(price_str, '')
            
            product_name = re.sub(r'%.*?\d+[,\.]\d{2}', '', product_name)
            product_name = self._clean_product_name(product_name)
            
            if pdf_type == "dondurulmus" and "DON." in product_name:
                product_name = product_name.replace("DON.", "DONDURULMUŞ")
            
            if product_name and len(product_name) > 3:
                product = {
                    'code': product_code,
                    'name': product_name,
                    'price_without_vat': price_without_vat,
                    'price_with_vat': price_with_vat,
                    'category': category
                }
                
                self.categories[category].append(product)
                self.processed_codes.add(duplicate_key)
                logging.info(f"✓ [{pdf_type} - {category}] [{product_code}] {product['name']}: {price_without_vat:.2f} / {price_with_vat:.2f}")
    
    def _print_results(self):
        """Sonuçları yazdır"""
        print("\n" + "="*80)
        print("PARSE EDİLEN ÜRÜNLER:")
        print("="*80)
        total = 0
        for cat_name, products in self.categories.items():
            count = len(products)
            total += count
            if count > 0:
                print(f"\n✓ {cat_name}: {count} ürün")
                print("-" * 60)
                # İlk 5 ürünü göster
                for idx, product in enumerate(products[:5], 1):
                    print(f"  {idx:2d}. [{product['code']}] {product['name']}: {product['price_without_vat']:.2f} / {product['price_with_vat']:.2f} TL")
                if len(products) > 5:
                    print(f"  ... ve {len(products) - 5} ürün daha")
            else:
                print(f"\n✗ {cat_name}: 0 ürün")
        
        print(f"\n{'='*80}")
        print(f"TOPLAM: {total} ürün bulundu")
        print(f"İşlenen benzersiz kombinasyon sayısı: {len(self.processed_codes)}")
        print(f"{'='*80}")
        
        if total == 0:
            logging.warning("HİÇ ÜRÜN BULUNAMADI! PDF formatını kontrol edin.")
        else:
            logging.info(f"BAŞARILI: Toplam {total} benzersiz ürün işlendi")
    
    def apply_discounts(self, discount_rates: Dict[str, float]) -> Dict:
        """İskonto oranlarını uygular - %1 KDV ile"""
        discounted_data = {}
        
        for category, products in self.categories.items():
            if not products:
                continue
                
            discount_rate = discount_rates.get(category, 0.0)
            discount_multiplier = 1 - (discount_rate / 100)
            
            discounted_products = []
            for product in products:
                # İskonto KDV hariç fiyata uygulanır
                discounted_without_vat = round(product['price_without_vat'] * discount_multiplier, 2)
                
                # KDV dahil fiyat yeniden hesaplanır (%1 KDV)
                kdv_multiplier = 1.01  # %1 KDV
                discounted_with_vat = round(discounted_without_vat * kdv_multiplier, 2)
                
                discounted_product = {
                    'name': product['name'],
                    'price_without_vat': discounted_without_vat,
                    'price_with_vat': discounted_with_vat,
                    'original_price_without_vat': product['price_without_vat'],
                    'original_price_with_vat': product['price_with_vat']
                }
                discounted_products.append(discounted_product)
            
            if discounted_products:
                discounted_data[category] = discounted_products
        
        return discounted_data
    
    def get_categories(self) -> List[str]:
        """Mevcut kategorileri döner"""
        return list(self.categories.keys())
    
    def get_product_count(self) -> int:
        """Toplam ürün sayısını döner"""
        return sum(len(products) for products in self.categories.values())
    
    def clear_data(self):
        """Verileri temizler"""
        for category in self.categories:
            self.categories[category] = []
        self.processed_codes.clear()
    
    def merge_data_from_multiple_pdfs(self, pdf_paths: List[str]) -> bool:
        """Birden fazla PDF'den verileri birleştirir"""
        try:
            self.clear_data()
            success_count = 0
            
            for pdf_path in pdf_paths:
                pdf_type = self.determine_pdf_type(pdf_path)
                success = self.extract_data_from_pdf(pdf_path, pdf_type)
                
                if success:
                    success_count += 1
                    filename = os.path.basename(pdf_path)
                    # Mevcut verileri kaydet
                    self.pdf_files[filename] = {
                        'categories': {k: v[:] for k, v in self.categories.items()},
                        'type': pdf_type
                    }
            
            return success_count > 0
                
        except Exception as e:
            logging.error(f"Çoklu PDF birleştirme hatası: {e}")
            return False
    
    def determine_pdf_type(self, pdf_path: str) -> str:
        """PDF tipini belirler"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
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
    
    def get_all_products(self) -> Dict:
        """Tüm PDF'lerden birleştirilmiş ürünleri döndürür"""
        merged_categories = {k: [] for k in self.categories.keys()}
        
        for pdf_data in self.pdf_files.values():
            for category, products in pdf_data['categories'].items():
                merged_categories[category].extend(products)
        
        return merged_categories
    
    def get_pdf_names(self) -> List[str]:
        """İşlenen PDF isimlerini döndürür"""
        return list(self.pdf_files.keys())