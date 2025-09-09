# main.py - MODERN ARAYÜZ VERSİYONU
import tkinter as tk
from tkinter import ttk
import sys
import os
import logging

def main():
    # Türkçe karakter desteği için encoding ayarı
    if sys.platform.startswith('win'):
        try:
            import locale
            locale.setlocale(locale.LC_ALL, 'Turkish_Turkey.1254')
        except:
            pass
    
    # Logging ayarları
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bupilic_app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Mevcut ui_components'ten import
    from ui_components import ModernPriceCalculatorUI
    
    root = tk.Tk()
    root.title("Bupiliç İskontolu Fiyat Hesaplayıcı v3.0")
    root.geometry("1400x800")
    root.minsize(1200, 700)
    
    # Icon ayarı
    try:
        if os.path.exists('icon.ico'):
            root.iconbitmap('icon.ico')
    except:
        pass
    
    # Pencereyi ortala
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    app = ModernPriceCalculatorUI(root)
    
    logging.info("Bupiliç İskontolu Fiyat Hesaplayıcı v3.0 başlatıldı")
    
    root.mainloop()

if __name__ == "__main__":
    main()