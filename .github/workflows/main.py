from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.clock import Clock
import yt_dlp
import os

KV = '''
MDScreen:
    md_bg_color: 0.95, 0.95, 0.95, 1
    
    MDTopAppBar:
        title: "YouTube Загрузчик"
        pos_hint: {"top": 1}
        md_bg_color: 1, 0.2, 0.2, 1
        specific_text_color: 1, 1, 1, 1
        
    MDScrollView:
        do_scroll_y: True
        do_scroll_x: False
        
        BoxLayout:
            orientation: "vertical"
            padding: 20
            spacing: 15
            size_hint_y: None
            height: self.minimum_height
            
            MDTextField:
                id: url_input
                hint_text: "Вставьте ссылку на видео"
                mode: "rectangle"
                size_hint_x: 1
                
            MDTextField:
                id: quality_button
                hint_text: "Выберите качество"
                mode: "rectangle"
                size_hint_x: 1
                on_focus: if self.focus: app.show_quality_menu()
                readonly: True
                
            MDRectangleFlatButton:
                text: "Выбрать папку"
                on_release: app.choose_folder()
                size_hint_x: 1
                
            MDLabel:
                id: folder_label
                text: "Папка: По умолчанию"
                size_hint_x: 1
                halign: "center"
                
            MDRectangleFlatButton:
                id: download_btn
                text: "Скачать"
                md_bg_color: 0.2, 0.6, 0.2, 1
                text_color: 1, 1, 1, 1
                on_release: app.start_download()
                size_hint_x: 1
                
            MDProgressBar:
                id: progress_bar
                value: 0
                size_hint_x: 1
                
            MDLabel:
                id: status_label
                text: ""
                size_hint_x: 1
                halign: "center"
'''

class YouTubeDownloaderApp(MDApp):
    dialog = None
    download_path = None
    
    def build(self):
        self.title = "YouTube Загрузчик"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Red"
        
        self.qualities = [
            "Лучшее (4K/8K)",
            "1080p (Full HD)",
            "720p (HD)",
            "480p (стандарт)",
            "360p (экономия)",
            "Только аудио (MP3)"
        ]
        
        return Builder.load_string(KV)
    
    def show_quality_menu(self):
        from kivymd.uix.menu import MDDropdownMenu
        
        menu_items = [
            {
                "text": quality,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=quality: self.select_quality(x)
            }
            for quality in self.qualities
        ]
        
        self.menu = MDDropdownMenu(
            caller=self.root.ids.quality_button,
            items=menu_items,
            width_mult=4
        )
        self.menu.open()
    
    def select_quality(self, quality):
        self.root.ids.quality_button.text = quality
        self.selected_quality = quality
        self.menu.dismiss()
    
    def choose_folder(self):
        # На Android используем стандартную папку Downloads
        self.download_path = os.path.expanduser("~/storage/downloads")
        if not os.path.exists(self.download_path):
            self.download_path = os.path.expanduser("~/Downloads")
        self.root.ids.folder_label.text = f"📁 Папка выбрана"
        self.show_message("Готово", "Видео будут сохранены в Downloads")
    
    def show_message(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title,
                text=text,
                buttons=[MDFlatButton(text="OK", on_release=self.close_dialog)]
            )
            self.dialog.open()
    
    def close_dialog(self, instance):
        self.dialog.dismiss()
        self.dialog = None
    
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip('%')
            try:
                progress = float(percent)
                Clock.schedule_once(lambda dt: self.update_progress(progress), 0)
            except:
                pass
    
    def update_progress(self, value):
        self.root.ids.progress_bar.value = value
        self.root.ids.status_label.text = f"Загрузка: {value:.0f}%"
    
    def start_download(self):
        url = self.root.ids.url_input.text.strip()
        if not url:
            self.show_message("Ошибка", "Введите ссылку на видео!")
            return
        
        if not hasattr(self, 'selected_quality'):
            self.show_message("Ошибка", "Выберите качество!")
            return
        
        if not self.download_path:
            self.download_path = os.path.expanduser("~/storage/downloads")
        
        ydl_opts = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
        }
        
        quality_map = {
            "Лучшее (4K/8K)": 'bestvideo+bestaudio/best',
            "1080p (Full HD)": 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            "720p (HD)": 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            "480p (стандарт)": 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            "360p (экономия)": 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        }
        
        if self.selected_quality == "Только аудио (MP3)":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            })
        else:
            ydl_opts['format'] = quality_map.get(self.selected_quality, 'bestvideo+bestaudio/best')
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        
        ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['android', 'web']}}
        
        from threading import Thread
        
        def download_thread():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                Clock.schedule_once(lambda dt: self.download_complete(), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.download_error(str(e)), 0)
        
        self.root.ids.download_btn.disabled = True
        self.root.ids.status_label.text = "Начинаем загрузку..."
        self.root.ids.progress_bar.value = 0
        
        Thread(target=download_thread).start()
    
    def download_complete(self):
        self.root.ids.download_btn.disabled = False
        self.root.ids.progress_bar.value = 100
        self.root.ids.status_label.text = "✅ Готово!"
        self.show_message("Успех", "Видео скачано в папку Downloads!")
    
    def download_error(self, error):
        self.root.ids.download_btn.disabled = False
        self.root.ids.status_label.text = "❌ Ошибка"
        self.show_message("Ошибка", str(error)[:200])

if __name__ == "__main__":
    YouTubeDownloaderApp().run()