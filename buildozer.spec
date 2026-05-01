[app]

title = YouTube Downloader
package.name = youtubedownloader
package.domain = org.youtube.downloader

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1
requirements = python3,kivy,kivymd,yt-dlp

orientation = portrait

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 30
android.minapi = 21
android.target = 33
android.ndk = 23b

android.archs = arm64-v8a

[buildozer]

log_level = 2
warn_on_root = 1