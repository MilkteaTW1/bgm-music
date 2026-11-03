"""Video type -> music rules.

Each profile answers: what should background music for this kind of video sound like?
Numbers are plain knobs the composer and the reviewer both read, so a rule lives in one place.
"""

MODES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
}

# groove: none = no drums, soft = hats only, pop = kick/snare/hats, drive = busier four-on-the-floor
PROFILES = {
    "tutorial": dict(
        label="教學 / 講解", aliases=["教學", "教程", "講解", "課程", "tutorial", "howto", "lesson", "explainer"],
        bpm=(82, 94), mode="major", keys=[0, 5, 7], progs=[[1, 5, 6, 4], [1, 4, 5, 4], [6, 4, 1, 5]],
        groove="none", pad=0.55, arp=0.35, bass=0.45, melody=0.0, bright=0.35, reverb=0.25,
        voice=True, lufs=-27, onsets=(0.8, 3.0),
        why="有人聲講話：不放鼓、不放旋律，只留柔和和弦與輕輕的分解和弦，避開人聲最清楚的頻段。"),
    "vlog": dict(
        label="Vlog / 日常", aliases=["vlog", "日常", "生活", "daily", "lifestyle"],
        bpm=(96, 108), mode="major", keys=[0, 7, 2], progs=[[1, 5, 6, 4], [1, 6, 4, 5], [4, 1, 5, 6]],
        groove="soft", pad=0.4, arp=0.45, bass=0.5, melody=0.35, bright=0.55, reverb=0.2,
        voice=True, lufs=-25, onsets=(2.0, 5.0),
        why="輕鬆明亮：節奏只用輕輕的踩鈸，加一點簡單旋律，整體要有精神但不搶說話。"),
    "tech": dict(
        label="科技介紹 / 產品", aliases=["科技", "產品", "3c", "開箱", "tech", "product", "unboxing", "keynote"],
        bpm=(100, 116), mode="dorian", keys=[2, 9, 4], progs=[[1, 4, 1, 5], [1, 7, 6, 7], [1, 3, 4, 5]],
        groove="pop", pad=0.35, arp=0.6, bass=0.55, melody=0.15, bright=0.65, reverb=0.18,
        voice=True, lufs=-25, onsets=(3.0, 6.5),
        why="未來感、乾淨：分解和弦當主角，低音穩定，鼓點精簡，聲音偏亮但不刺耳。"),
    "gaming": dict(
        label="遊戲實況", aliases=["遊戲", "實況", "game", "gaming", "stream", "gameplay"],
        bpm=(118, 134), mode="minor", keys=[9, 4, 2], progs=[[1, 7, 6, 7], [1, 6, 3, 7], [1, 4, 7, 3]],
        groove="drive", pad=0.3, arp=0.6, bass=0.7, melody=0.3, bright=0.7, reverb=0.12,
        voice=True, lufs=-24, onsets=(4.0, 8.0),
        why="有衝勁：節奏明確、低音厚，但仍要讓出人聲的空間，所以中頻壓低。"),
    "travel": dict(
        label="旅遊 / 風景", aliases=["旅遊", "旅行", "風景", "travel", "scenery", "landscape", "drone"],
        bpm=(88, 100), mode="lydian", keys=[7, 0, 5], progs=[[1, 2, 5, 1], [1, 5, 6, 4], [4, 5, 1, 1]],
        groove="soft", pad=0.6, arp=0.4, bass=0.4, melody=0.45, bright=0.6, reverb=0.4,
        voice=False, lufs=-20, onsets=(1.5, 4.0),
        why="開闊、有畫面：厚厚的和弦加上很多空間感，旋律慢慢唱，可以比有講話的片子更大聲。"),
    "food": dict(
        label="美食 / 料理", aliases=["美食", "料理", "食譜", "food", "cooking", "recipe"],
        bpm=(92, 104), mode="major", keys=[5, 0, 7], progs=[[1, 6, 2, 5], [1, 4, 6, 5], [2, 5, 1, 6]],
        groove="soft", pad=0.35, arp=0.5, bass=0.55, melody=0.4, bright=0.5, reverb=0.15,
        voice=True, lufs=-25, onsets=(2.0, 5.0),
        why="溫暖輕快：和弦帶一點爵士味(第二級、第六級)，節奏悠閒，聽起來像在廚房。"),
    "emotional": dict(
        label="感人 / 回憶", aliases=["感人", "回憶", "故事", "紀錄", "emotional", "story", "memory", "documentary", "sad"],
        bpm=(66, 78), mode="minor", keys=[9, 2, 4], progs=[[1, 6, 3, 7], [6, 4, 1, 5], [1, 4, 6, 5]],
        groove="none", pad=0.7, arp=0.3, bass=0.35, melody=0.5, bright=0.3, reverb=0.5,
        voice=False, lufs=-22, onsets=(0.5, 2.5),
        why="慢、柔、有空間：沒有鼓，大量長音和弦，旋律稀疏而且留白。"),
    "corporate": dict(
        label="商業 / 簡報", aliases=["商業", "簡報", "企業", "公司", "corporate", "business", "presentation", "ad"],
        bpm=(100, 112), mode="major", keys=[0, 7, 5], progs=[[1, 5, 6, 4], [1, 4, 5, 5], [4, 5, 3, 6]],
        groove="pop", pad=0.4, arp=0.5, bass=0.55, melody=0.25, bright=0.6, reverb=0.15,
        voice=True, lufs=-26, onsets=(2.5, 5.5),
        why="正面、可靠：標準的流行和弦，節奏乾淨，不要太有個性，才不會搶走內容。"),
}


def find(name):
    """Match a video type from a key or any alias (Chinese or English, partial match)."""
    n = name.strip().lower()
    if n in PROFILES:
        return n
    for key, p in PROFILES.items():
        if any(a in n or n in a for a in p["aliases"]):
            return key
    return None
