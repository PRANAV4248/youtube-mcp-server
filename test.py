import os
from mpv import MPV

mpv_config_dir = os.path.join(os.environ.get('APPDATA'), 'mpv')

player = MPV(
    ytdl=True,
    input_default_bindings=True, 
    input_vo_keyboard=True,
    config=True,
    config_dir=mpv_config_dir,
    load_scripts=True,
    osc=False
)

url = "https://www.youtube.com/watch?v=1NnT8RjQHg8"

print(f"Loading video: {url}")
player.play(url)
player.wait_for_playback()
