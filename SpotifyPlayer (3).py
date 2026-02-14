import os
import random
import pygame
import time
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageFilter, ImageEnhance
import io
from threading import Thread
from pynput import keyboard

# --- 配置 ---
LOCATION_FILE = "Location.txt"
# 支持的音頻格式（擴展到最全）
SUPPORTED_EXTENSIONS = (
    # === 常見壓縮格式 ===
    '.mp3',      # MP3
    '.m4a',      # AAC (Apple)
    '.aac',      # AAC
    '.ogg',      # Ogg Vorbis
    '.oga',      # Ogg Audio
    '.opus',     # Opus (高质量)
    '.wma',      # Windows Media Audio
    
    # === 無損格式 ===
    '.flac',     # FLAC (最常見的無損)
    '.wav',      # WAV (未壓縮)
    '.aiff',     # AIFF (Apple 無損)
    '.aif',      # AIFF 縮寫
    '.ape',      # Monkey's Audio (無損)
    '.alac',     # Apple Lossless
    '.wv',       # WavPack (無損)
    '.tta',      # True Audio (無損)
    
    # === 視頻容器格式（提取音頻）===
    '.ogv',      # Ogg Video (含音頻軌)
    '.mp4',      # MP4 Audio/Video
    '.m4b',      # Apple Audiobook
    '.m4p',      # Apple Protected
    '.m4v',      # Apple Video (含音頻)
    '.3gp',      # 3GP Audio/Video
    '.webm',     # WebM Audio/Video
    '.mka',      # Matroska Audio
    '.mkv',      # Matroska Video (含音頻)
    '.avi',      # AVI (含音頻軌)
    '.mov',      # QuickTime (含音頻)
    '.wmv',      # Windows Media Video (含音頻)
    '.flv',      # Flash Video (含音頻)
    
    # === 其他格式 ===
    '.mpc',      # Musepack
    '.mp+',      # Musepack 舊格式
    '.ofr',      # OptimFROG
    '.ofs',      # OptimFROG DualStream
    '.spx',      # Speex
)
ALBUM_ART_SIZE = 500
FONT_SIZE_TITLE = 64
FONT_SIZE_ARTIST = 32
TEXT_MARGIN_LEFT = 80
TEXT_MARGIN_BOTTOM = 80

# --- 全局鍵盤監聽器（系統級，不受輸入法影響）---
class GlobalKeyListener:
    def __init__(self):
        self.key_actions = {
            'prev': False,   # 上一首
            'next': False,   # 下一首
            'pause': False,  # 暫停
            'quit': False    # 退出
        }
        # 記錄按鍵狀態，防止重複觸發
        self.key_pressed = {
            'f5': False,
            'f6': False,
            'f7': False,
            'space': False,
            '4': False,
            '6': False,
            'd': False,
            'f': False,
            'left': False,
            'right': False,
            'esc': False
        }
        self.listener = None
        
    def on_press(self, key):
        try:
            # F5: 上一首
            if key == keyboard.Key.f5:
                if not self.key_pressed['f5']:
                    self.key_actions['prev'] = True
                    self.key_pressed['f5'] = True
            # F6: 播放/暫停
            elif key == keyboard.Key.f6:
                if not self.key_pressed['f6']:
                    self.key_actions['pause'] = True
                    self.key_pressed['f6'] = True
            # F7: 下一首
            elif key == keyboard.Key.f7:
                if not self.key_pressed['f7']:
                    self.key_actions['next'] = True
                    self.key_pressed['f7'] = True
            # ESC: 退出
            elif key == keyboard.Key.esc:
                if not self.key_pressed['esc']:
                    self.key_actions['quit'] = True
                    self.key_pressed['esc'] = True
            # 數字鍵 4: 上一首
            elif hasattr(key, 'char') and key.char == '4':
                if not self.key_pressed['4']:
                    self.key_actions['prev'] = True
                    self.key_pressed['4'] = True
            # 數字鍵 6: 下一首
            elif hasattr(key, 'char') and key.char == '6':
                if not self.key_pressed['6']:
                    self.key_actions['next'] = True
                    self.key_pressed['6'] = True
            # 空格鍵: 暫停
            elif key == keyboard.Key.space:
                if not self.key_pressed['space']:
                    self.key_actions['pause'] = True
                    self.key_pressed['space'] = True
            # 方向鍵
            elif key == keyboard.Key.left:
                if not self.key_pressed['left']:
                    self.key_actions['prev'] = True
                    self.key_pressed['left'] = True
            elif key == keyboard.Key.right:
                if not self.key_pressed['right']:
                    self.key_actions['next'] = True
                    self.key_pressed['right'] = True
            # 字母鍵 D: 上一首
            elif hasattr(key, 'char') and key.char in ['d', 'D']:
                if not self.key_pressed['d']:
                    self.key_actions['prev'] = True
                    self.key_pressed['d'] = True
            # 字母鍵 F: 下一首
            elif hasattr(key, 'char') and key.char in ['f', 'F']:
                if not self.key_pressed['f']:
                    self.key_actions['next'] = True
                    self.key_pressed['f'] = True
        except:
            pass
    
    def on_release(self, key):
        """按鍵釋放時重置狀態"""
        try:
            if key == keyboard.Key.f5:
                self.key_pressed['f5'] = False
            elif key == keyboard.Key.f6:
                self.key_pressed['f6'] = False
            elif key == keyboard.Key.f7:
                self.key_pressed['f7'] = False
            elif key == keyboard.Key.esc:
                self.key_pressed['esc'] = False
            elif key == keyboard.Key.space:
                self.key_pressed['space'] = False
            elif key == keyboard.Key.left:
                self.key_pressed['left'] = False
            elif key == keyboard.Key.right:
                self.key_pressed['right'] = False
            elif hasattr(key, 'char'):
                if key.char == '4':
                    self.key_pressed['4'] = False
                elif key.char == '6':
                    self.key_pressed['6'] = False
                elif key.char in ['d', 'D']:
                    self.key_pressed['d'] = False
                elif key.char in ['f', 'F']:
                    self.key_pressed['f'] = False
        except:
            pass
    
    def get_and_clear_action(self, action):
        """獲取動作並清除標誌"""
        if self.key_actions.get(action, False):
            self.key_actions[action] = False
            return True
        return False
    
    def start(self):
        """啟動後台監聽"""
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release  # 添加釋放處理
        )
        self.listener.start()
    
    def stop(self):
        """停止監聽"""
        if self.listener:
            self.listener.stop()

class SpotifyPlayer:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        # 初始化全局鍵盤監聽器（系統級，不受輸入法影響）
        self.global_keys = GlobalKeyListener()
        self.global_keys.start()
        print("✅ 全局鍵盤監聽已啟動（不受輸入法影響）")
        
        # 设置环境变量，确保获得键盘输入（绕过输入法）
        os.environ['SDL_IME_SHOW_UI'] = '0'
        
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("Music Player")

        # 禁用 Pygame 的按鍵重複功能 (防止按住不放產生連續事件)
        pygame.key.set_repeat(0)
        
        # 确保窗口获得焦点
        pygame.event.set_grab(True)
        pygame.key.set_mods(0)  # 清除所有修饰键状态

        self.MUSIC_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_END)

        self.font_title = pygame.font.SysFont("Microsoft YaHei", FONT_SIZE_TITLE, bold=True)
        self.font_artist = pygame.font.SysFont("Microsoft YaHei", FONT_SIZE_ARTIST)
        
        self.playlist = []
        self.current_index = 0
        self.is_paused = False
        self.running = True

        # --- 曲線救國方案：時間戳限制 ---
        # 記錄上次切歌的時間（毫秒），強制最小間隔 300ms
        self.last_skip_time = 0
        self.SKIP_COOLDOWN_MS = 300  # 切歌冷卻時間（毫秒）

        self.bg_surface = None
        self.cover_surface = None
        self.text_surface_title = None
        self.text_surface_artist = None

        self.load_songs_from_location()

    def load_songs_from_location(self):
        if not os.path.exists(LOCATION_FILE):
            print(f"錯誤：找不到 {LOCATION_FILE} 文件！")
            print(f"請在程序目錄下創建 {LOCATION_FILE}，並在裡面寫入音樂文件夾的路徑。")
            input("按 Enter 鍵退出...")
            self.running = False
            return
        
        with open(LOCATION_FILE, 'r', encoding='utf-8') as f:
            music_dir = f.read().strip()
        
        if not os.path.isdir(music_dir):
            print(f"錯誤：音樂文件夾不存在：{music_dir}")
            print(f"請檢查 {LOCATION_FILE} 中的路徑是否正確。")
            input("按 Enter 鍵退出...")
            self.running = False
            return

        for root, _, files in os.walk(music_dir):
            for file in files:
                if file.lower().endswith(SUPPORTED_EXTENSIONS):
                    self.playlist.append(os.path.join(root, file))
        
        if not self.playlist:
            print(f"錯誤：在 {music_dir} 中找不到任何音樂文件！")
            print(f"\n支持的格式共 {len(SUPPORTED_EXTENSIONS)} 種：")
            print("  壓縮格式：mp3, m4a, aac, ogg, opus, wma 等")
            print("  無損格式：flac, wav, aiff, ape, alac, wv, tta 等")
            print("  視頻格式：ogv, mp4, mkv, webm, avi, mov, wmv, flv 等（提取音頻）")
            print("  完整列表：" + ", ".join(SUPPORTED_EXTENSIONS))
            input("按 Enter 鍵退出...")
            self.running = False
            return
        
        random.shuffle(self.playlist)
        print(f"✅ 成功加載 {len(self.playlist)} 首歌曲！")
        
        # 統計格式分佈
        format_count = {}
        video_formats = {'.ogv', '.mp4', '.m4v', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.3gp'}
        video_count = 0
        
        for song in self.playlist:
            ext = os.path.splitext(song)[1].lower()
            format_count[ext] = format_count.get(ext, 0) + 1
            if ext in video_formats:
                video_count += 1
        
        print(f"\n📊 格式統計：")
        for ext, count in sorted(format_count.items(), key=lambda x: x[1], reverse=True):
            # 標註視頻格式
            marker = " [視頻]" if ext in video_formats else ""
            print(f"  {ext}: {count} 首{marker}")
        
        if video_count > 0:
            print(f"\n💡 提示：檢測到 {video_count} 個視頻文件，將提取音頻軌道播放")
        print("\n" + "="*60)
        print("🎵 音樂播放器已啟動 - 全局鍵盤控制（不受輸入法影響）")
        print("="*60)
        print("\n⭐【推薦按鍵 - 中英文輸入法都可用】")
        print("  F5 鍵：上一首")
        print("  F6 鍵：播放 / 暫停")
        print("  F7 鍵：下一首")
        print("  ESC 鍵：退出")
        print("\n【其他可用按鍵】")
        print("  數字 4 / 6：上一首 / 下一首")
        print("  方向鍵 ← / →：上一首 / 下一首")
        print("  空格鍵：播放 / 暫停")
        print("  字母 D / F：上一首 / 下一首")
        print("\n💡 提示：所有按鍵使用系統級監聽，中文輸入法下也能正常工作！")
        print("="*60 + "\n")

    def get_metadata(self, file_path):
        filename = os.path.basename(file_path)
        title = os.path.splitext(filename)[0]
        artist = "Unknown Artist"
        image_pil = None
        try:
            audio = File(file_path)
            if audio and audio.tags:
                if 'TIT2' in audio.tags: title = str(audio.tags['TIT2'])
                elif 'title' in audio.tags: title = str(audio.tags['title'][0])
                if 'TPE1' in audio.tags: artist = str(audio.tags['TPE1'])
                elif 'artist' in audio.tags: artist = str(audio.tags['artist'][0])
                
                artwork_data = None
                if isinstance(audio, MP3):
                    for tag in audio.tags.values():
                        if isinstance(tag, APIC):
                            artwork_data = tag.data
                            break
                elif hasattr(audio, 'pictures') and audio.pictures:
                    artwork_data = audio.pictures[0].data
                
                if artwork_data:
                    image_pil = Image.open(io.BytesIO(artwork_data))
        except:
            pass
        
        if image_pil is None:
            image_pil = Image.new('RGB', (500, 500), color=(50, 50, 50))
        return title, artist, image_pil

    def prepare_ui_assets(self, image_pil, title, artist):
        # 1. 背景：適度模糊 + 保持鮮豔色彩
        bg_image = image_pil.copy()
        # 先縮小（提升性能）
        bg_image = bg_image.resize((self.width // 12, self.height // 12), resample=Image.BILINEAR)
        # 適度模糊（既有氛圍感，又不會太糊）
        bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=8))
        # 放大回原尺寸
        bg_image = bg_image.resize((self.width, self.height), resample=Image.BILINEAR)
        
        # 稍微增強飽和度（讓顏色更鮮豔）
        color_enhancer = ImageEnhance.Color(bg_image)
        bg_image = color_enhancer.enhance(1.2)
        
        # 適度降低亮度（既能突出前景，又不會太暗）
        brightness_enhancer = ImageEnhance.Brightness(bg_image)
        bg_image = brightness_enhancer.enhance(0.45)
        
        self.bg_surface = pygame.image.fromstring(bg_image.tobytes(), bg_image.size, bg_image.mode).convert()
        
        # 2. 封面
        cover_image = image_pil.copy()
        cover_image.thumbnail((ALBUM_ART_SIZE, ALBUM_ART_SIZE), Image.LANCZOS)
        self.cover_surface = pygame.image.fromstring(cover_image.tobytes(), cover_image.size, cover_image.mode).convert()
        
        # 3. 文字
        self.text_surface_title = self.font_title.render(title, True, (255, 255, 255))
        self.text_surface_artist = self.font_artist.render(artist, True, (200, 200, 200))

    def play_song(self):
        if not self.playlist: return
        
        file_path = self.playlist[self.current_index]
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            # 停止舊歌
            pygame.mixer.music.stop()
            
            # 準備UI資源 (這是最耗時的一步)
            title, artist, img_pil = self.get_metadata(file_path)
            self.prepare_ui_assets(img_pil, title, artist)
            
            # 加載新歌
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.is_paused = False
            
            print(f"▶️  正在播放 [{file_ext}]: {title} - {artist}")
            
        except Exception as e:
            print(f"\n⚠️  無法播放: {file_name}")
            print(f"   格式: {file_ext}")
            print(f"   錯誤: {str(e)}")
            print(f"   提示: 您的系統可能不支持此格式，正在跳到下一首...\n")
            
            # 自動跳到下一首
            time.sleep(1)
            self.next_song()

    def next_song(self):
        # 檢查是否在冷卻時間內
        current_time = pygame.time.get_ticks()
        if current_time - self.last_skip_time < self.SKIP_COOLDOWN_MS:
            return  # 冷卻中，忽略這次切歌請求
        
        self.last_skip_time = current_time  # 更新時間戳
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_song()
        # 清空事件队列中积累的按键事件
        pygame.event.clear([pygame.KEYDOWN, pygame.KEYUP])

    def prev_song(self):
        # 檢查是否在冷卻時間內
        current_time = pygame.time.get_ticks()
        if current_time - self.last_skip_time < self.SKIP_COOLDOWN_MS:
            return  # 冷卻中，忽略這次切歌請求
        
        self.last_skip_time = current_time  # 更新時間戳
        self.current_index = (self.current_index - 1 + len(self.playlist)) % len(self.playlist)
        self.play_song()
        # 清空事件队列中积累的按键事件
        pygame.event.clear([pygame.KEYDOWN, pygame.KEYUP])

    def toggle_pause(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self.is_paused = True

    def draw(self):
        if self.bg_surface:
            self.screen.blit(self.bg_surface, (0, 0))
            if self.cover_surface:
                cx = (self.width - self.cover_surface.get_width()) // 2
                cy = (self.height - self.cover_surface.get_height()) // 2
                self.screen.blit(self.cover_surface, (cx, cy))
            
            ty = self.height - TEXT_MARGIN_BOTTOM - self.text_surface_title.get_height() - self.text_surface_artist.get_height() - 10
            ay = ty + self.text_surface_title.get_height() + 10
            self.screen.blit(self.text_surface_title, (TEXT_MARGIN_LEFT, ty))
            self.screen.blit(self.text_surface_artist, (TEXT_MARGIN_LEFT, ay))
        pygame.display.flip()

    def run_player(self):
        if not self.playlist: return
        
        # 初始播放
        self.play_song()
        
        clock = pygame.time.Clock()

        while self.running:
            # --- 檢查全局鍵盤監聽器（系統級，不受輸入法影響）---
            if self.global_keys.get_and_clear_action('quit'):
                self.running = False
                break
            if self.global_keys.get_and_clear_action('next'):
                self.next_song()
            if self.global_keys.get_and_clear_action('prev'):
                self.prev_song()
            if self.global_keys.get_and_clear_action('pause'):
                self.toggle_pause()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # 自動播放下一首 (不需要鎖，因為這不是按鍵觸發的)
                elif event.type == self.MUSIC_END:
                    self.next_song()

                # --- 按鍵按下處理 ---
                # 注意：F5/F6/F7/空格/數字鍵/方向鍵/D/F 都由全局監聽器處理
                # 這裡只保留 ESC（因為需要立即響應退出）
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            self.draw()
            clock.tick(75) # 保持 75 FPS

        # 停止全局鍵盤監聽
        self.global_keys.stop()
        pygame.quit()

if __name__ == "__main__":
    player = SpotifyPlayer()
    player.run_player()
