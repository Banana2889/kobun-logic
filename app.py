import streamlit as st
import os
import time
import base64
import csv
import random

# --- 1. 基本設定とパス（ここを修正しました） ---
st.set_page_config(page_title="古文ロジック・恋愛抄 ～義経伝・極雅～", layout="centered")

# プログラムと同じフォルダにある「kobungazou」を見に行く設定
IMAGE_DIR = "kobungazou" 
CSV_PATH = "research_data.csv" # CSVも同じフォルダに保存するように変更

# 調査カテゴリ
CATEGORIES = [
    "古文の単語や文法を学ぶことに関してどう思いますか",
    "古文の内容理解に関してどう思いますか",
    "古文の当時の時代の背景、価値観に関してどう思いますか",
    "古文の人間関係に次いでどう思いますか"
]
LIKERT_QUESTIONS = ["古文は面白いと思いますか", "このゲームはおもしろかった？"]

# --- 2. ハイパーウルトラ雅なUI・アニメーション ---
def inject_miyabi_style():
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0f0a1e 0%, #2d1a2a 100%); color: #f3e5ab; font-family: 'Yu Mincho', serif; }
    [data-testid="stForm"], [data-testid="stAlert"] { background-color: #f8f4e6 !important; padding: 30px !important; border-radius: 15px; border: 4px double #d4af37 !important; box-shadow: 0 15px 35px rgba(0,0,0,0.6); color: #1a1a1a !important; }
    [data-testid="stForm"] label, [data-testid="stForm"] p, [data-testid="stAlert"] { color: #1a1a1a !important; font-weight: bold !important; font-size: 1.1rem !important; }
    [data-testid="stRadio"] { background-color: #ffffff !important; padding: 20px; border-radius: 15px; border: 3px solid #d4af37; }
    [data-testid="stRadio"] label { color: #000000 !important; font-weight: 900 !important; font-size: 1.2rem !important; }
    .stTextArea textarea, .stTextInput input { background-color: #ffffff !important; color: #000000 !important; border: 2px solid #999 !important; }
    @keyframes sakura-fall { 0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; } 100% { transform: translateY(100vh) rotate(360deg); opacity: 0; } }
    .sakura-bg { position: fixed; top: -10%; color: #ffb7c5; font-size: 24px; pointer-events: none; z-index: 1; animation: sakura-fall 12s linear infinite; }
    @keyframes rainbow-flash { 0% { filter: hue-rotate(0deg) brightness(1.5); } 100% { filter: hue-rotate(360deg) brightness(1.5); } }
    .rainbow-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 10000; mix-blend-mode: color-dodge; animation: rainbow-flash 0.5s linear infinite; background: radial-gradient(circle, rgba(255,255,255,0.4) 0%, transparent 70%); }
    @keyframes tear-drop { 0% { transform: translateY(-10vh); opacity: 0; } 50% { opacity: 0.8; } 100% { transform: translateY(100vh); opacity: 0; } }
    .tear { position: fixed; color: #aaccff; font-size: 20px; pointer-events: none; z-index: 10000; animation: tear-drop 1.5s linear infinite; }
    </style>
    """ + "".join([f'<div class="sakura-bg" style="left:{random.randint(0,95)}%; animation-delay:{random.uniform(0,10)}s;">🌸</div>' for i in range(20)]) + " ", unsafe_allow_html=True)

def inject_result_animation(is_correct):
    if is_correct:
        st.markdown('<div class="rainbow-overlay"></div>', unsafe_allow_html=True)
        explode_html = "".join([f'<div style="position:fixed; top:50%; left:50%; font-size:35px; color:#ffb7c5; pointer-events:none; z-index:10001; animation: explode 2s ease-out forwards; --tx:{random.randint(-250,250)}vw; --ty:{random.randint(-250,250)}vh; --tr:{random.randint(0,720)}deg; animation-delay:{random.uniform(0,0.5)}s;">🌸</div>' for _ in range(80)])
        st.markdown(explode_html + """<style>@keyframes explode { 0% { opacity:0; transform:translate(-50%,-50%) scale(0.1); } 20% { opacity:1; } 100% { opacity:0; transform:translate(var(--tx), var(--ty)) scale(2.5) rotate(var(--tr)); } }</style>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,80,0.5); pointer-events:none; z-index:9999;"></div>', unsafe_allow_html=True)
        tears = "".join([f'<div class="tear" style="left:{random.randint(0,100)}%; animation-delay:{random.uniform(0,1.5)}s;">💧</div>' for _ in range(60)])
        tears += "".join([f'<div class="tear" style="left:{random.randint(0,100)}%; color:white; font-size:18px; animation-delay:{random.uniform(0,1.5)}s;">❄️</div>' for _ in range(30)])
        st.markdown(tears, unsafe_allow_html=True)

# --- 3. セッション管理 ---
inject_miyabi_style()

if 'app_mode' not in st.session_state:
    st.session_state.update({'app_mode': 'pre_mapping', 'pre_text': {cat: "" for cat in CATEGORIES}, 'pre_likert': {q: 3 for q in LIKERT_QUESTIONS}, 'post_text': {cat: "" for cat in CATEGORIES}, 'post_likert': {q: 3 for q in LIKERT_QUESTIONS}, 'stage': 0, 'love_meter': 50, 'answered': False, 'results': [], 'stage_start_time': 0, 'last_feedback': "", 'last_correct': False})

# --- 全10章の問題データ (義経伝) ---
scenes = [
    {"title": "第1章：闇夜の決意", "context": "平家全盛の世。修行の裏で密かに一族の再興を期して牙を研ぎ続ける。", "options": [{"text": "「昼は寺に読経し、夜は貴船の奥にのぼりて、兵法をぞ習ひける」", "score": 10, "correct": True, "feedback": "【正解】夜な夜な兵法に励む姿が目に浮かびます。"}, {"text": "「夜は貴船の奥にのぼりて、兵法をぞ習いおはします」", "score": -10, "correct": False, "feedback": "【失敗】自らの動作に最高敬語は不自然です。"}, {"text": "「夜は貴船の奥にのぼりて、兵法をぞ教えさせ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】教えを乞う立場であり、教える側ではございませぬ。"}, {"text": "「夜は貴船の奥にのぼりて、兵法をぞ遊びおはす」", "score": -10, "correct": False, "feedback": "【失敗】命がけの修行、遊びではございませぬ。"}]},
    {"title": "第2章：兄弟の再会", "context": "挙兵した兄の元へ駆けつけた場面。一族の悲願を果たすため、忠義を誓う。", "options": [{"text": "「御前に畏まりて、九郎義経、参り候ふ」", "score": 10, "correct": True, "feedback": "【正解】頼朝への深い敬意と忠誠心が伝わります。"}, {"text": "「御前に畏まりて、九郎義経、参り給ふ」", "score": -10, "correct": False, "feedback": "【失敗】己の参上に尊敬語は不要です。"}, {"text": "「御前に畏まりて、九郎義経、来たり候ふ」", "score": -10, "correct": False, "feedback": "【失敗】謙譲の意を示す「参る」が相応しいでしょう。"}, {"text": "「御前に畏まりて、九郎義経、見えさせ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】敬語の使い方が不自然です。"}]},
    {"title": "第3章：激流を越えて", "context": "水の流れを突破しなければならない。自ら最前線へ。", "options": [{"text": "「まっさきに喚いて、宇治川の早瀬をぞ押し渡り給ふ」", "score": 10, "correct": True, "feedback": "【正解】勇猛果敢な姿が見事に描かれています。"}, {"text": "「まっさきに喚いて、宇治川の早瀬をぞ渡りおはします」", "score": -10, "correct": False, "feedback": "【失敗】物語の勢いには「給ふ」が最も合います。"}, {"text": "「まっさきに喚いて、宇治川の早瀬をぞ見送り給ふ」", "score": -10, "correct": False, "feedback": "【失敗】見送っていては勝利は得られませぬ。"}, {"text": "「まっさきに喚いて、宇治川の早瀬をぞなぶり給ふ」", "score": -10, "correct": False, "feedback": "【失敗】川をなぶる表現は不適切です。"}]},
    {"title": "第4章：絶壁の奇襲", "context": "敵の防備が固い陣に対し、険しい地形から一気に攻め下る。", "options": [{"text": "「義経、三十騎ばかりを率て、真っ逆様におとし給ふ」", "score": 10, "correct": True, "feedback": "【正解】鵯越の奇襲、お見事です。"}, {"text": "「三十騎ばかりを率て、おとしおはします」", "score": -10, "correct": False, "feedback": "【失敗】「給ふ」の方がこの場面に相応しいです。"}, {"text": "「三十騎ばかりを率て、山陰に隠れ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】隠れていては奇襲になりませぬ。"}, {"text": "「三十騎ばかりを率て、見守り給ふ」", "score": -10, "correct": False, "feedback": "【失敗】見守るだけでは勝利は掴めませぬ。"}]},
    {"title": "第5章：嵐の船出", "context": "荒れる海を前に、あえて厳しい条件を利用して敵の意表を突く。", "options": [{"text": "「追い風なればこそ、船をば出だすなれ」", "score": 10, "correct": True, "feedback": "【正解】これぞ義経の真骨頂です。"}, {"text": "「追い風なればこそ、船をば出ださせ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】強意の「なれ」が相応しい場面です。"}, {"text": "「追い風なればこそ、船をば留むるなれ」", "score": -10, "correct": False, "feedback": "【失敗】留めてしまっては機を逃します。"}, {"text": "「追い風なればこそ、船をば弄び給ふ」", "score": -10, "correct": False, "feedback": "【失敗】不真面目な印象を与えます。"}]},
    {"title": "第6章：誇りの回収", "context": "激戦の最中、弓を落としてしまう。敵の嘲笑を防ぐため自ら動く。", "options": [{"text": "「鞭をもって、弓をかき寄せ、ついに取りてぞ帰り給ふ」", "score": 10, "correct": True, "feedback": "【正解】弓流し、誇りを守り抜く執念です。"}, {"text": "「鞭をもって、弓を打ち捨て、ついに取りてぞ帰り給ふ」", "score": -10, "correct": False, "feedback": "【失敗】打ち捨てては敵の拾い物になります。"}, {"text": "「鞭をもって、弓を拾い取らせ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】自らの手で取り戻すことに意味があります。"}, {"text": "「鞭をもって、弓を笑いおはします」", "score": -10, "correct": False, "feedback": "【失敗】笑っている場合ではございませぬ。"}]},
    {"title": "第7章：非情の采配", "context": "海上の戦い。敵の機動力を奪うため、船を操る者たちを射るよう命じる。", "options": [{"text": "「あやまちすな、水手・梶取を射よ」", "score": 10, "correct": True, "feedback": "【正解】勝利を決定づける非情の采配です。"}, {"text": "「あやまちすな、水手・梶取を射させ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】直接の命令形に緊張感が宿ります。"}, {"text": "「あやまちすな、水手・梶取を助けよ」", "score": -10, "correct": False, "feedback": "【失敗】助けていては敵を止められませぬ。"}, {"text": "「あやまちすな、水手・梶取をなぶり殺せ」", "score": -10, "correct": False, "feedback": "【失敗】残酷すぎます。"}]},
    {"title": "第8章：窮地の跳躍", "context": "敵が迫る。身の軽さを活かして瞬時に距離を取る。", "options": [{"text": "「ゆらりと飛びのき、二丈ばかりの船のわたりを、飛びわたり給ふ」", "score": 10, "correct": True, "feedback": "【正解】八艘飛び、見事です。"}, {"text": "「ゆらりと飛びのきおはし、船のわたりをわたり給ふ」", "score": -10, "correct": False, "feedback": "【失敗】文章の勢いが削がれます。"}, {"text": "「ゆらりと踏みとどまり、船のわたりを飛びわたり給ふ」", "score": -10, "correct": False, "feedback": "【失敗】捕まってしまいます。"}, {"text": "「ゆらりと立ち止まり給ひ、船のわたりを眺め給ふ」", "score": -10, "correct": False, "feedback": "【失敗】眺めている暇はございませぬ。"}]},
    {"title": "第9章：偽装の忍耐", "context": "正体を隠して関所を抜ける場面。仲間から激しい扱いを受けるが、耐えて去る。", "options": [{"text": "「義経、杖を突いて、山伏の態にて、急ぎ通り給ふ」", "score": 10, "correct": True, "feedback": "【正解】安宅の関の緊迫した情景です。"}, {"text": "「義経、杖を突いて、山伏の態にて、歩ませ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】「急ぎ通る」ことが重要です。"}, {"text": "「義経、杖を突いて、山伏の態にて、物申し給ふ」", "score": -10, "correct": False, "feedback": "【失敗】声を上げては怪しまれます。"}, {"text": "「義経、杖を突いて、山伏の態にて、命じ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】不自然な振る舞いになります。"}]},
    {"title": "第10章：静かなる終幕", "context": "ついに追い詰められる。自ら幕を引く準備を整える。", "options": [{"text": "「持仏堂の戸を強くしめ、内よりかんぬきをさして、自害し給ふ」", "score": 10, "correct": True, "feedback": "【正解】最期まで誇り高き姿、感服いたしました。"}, {"text": "「戸を強くしめ、内よりかんぬきをさして、眠りおはす」", "score": -10, "correct": False, "feedback": "【失敗】眠る場面ではございませぬ。"}, {"text": "「戸を強くしめ、内よりかんぬきをさして、まどひ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】義経公は惑いません。"}, {"text": "「戸を強くしめ、内よりかんぬきをさして、逃げおはします」", "score": -10, "correct": False, "feedback": "【失敗】逃げる道は残されておりませぬ。"}]}
]

# --- 4. 画面進行 ---
if st.session_state.app_mode == 'pre_mapping':
    st.title("🎎 古文ロジック ～事前調査～")
    with st.form("pre_form"):
        st.subheader("🖋️ 貴殿の今の認識を記されたし")
        for cat in CATEGORIES: st.session_state.pre_text[cat] = st.text_area(cat, height=80)
        st.subheader("📊 5段階評価")
        for q in LIKERT_QUESTIONS: st.session_state.pre_likert[q] = st.select_slider(q, options=[1, 2, 3, 4, 5], value=3)
        if st.form_submit_button("物語へ進む"):
            st.session_state.app_mode = 'game'; st.session_state.stage_start_time = time.perf_counter(); st.rerun()

elif st.session_state.app_mode == 'game':
    scene = scenes[st.session_state.stage]
    st.header(f"✨ {scene['title']}")
    st.progress(st.session_state.stage / 10)
    st.info(f"📜 状況説明: {scene['context']}")
    
    # 画像表示部分を修正（より安定した表示）
    img_name = f"gazou{st.session_state.stage + 1}.png"
    img_path = os.path.join(IMAGE_DIR, img_name)
    if os.path.exists(img_path): 
        st.image(img_path, width=700) # 警告対策としてwidthを指定
    else: 
        st.warning(f"画像が見つかりませぬ: {img_name}")

    if not st.session_state.answered:
        choice = st.radio("👇 適切な言の葉を選びなさい:", [o['text'] for o in scene['options']], index=None)
        if st.button("伝える"):
            if choice:
                st.session_state.results.append(time.perf_counter() - st.session_state.stage_start_time)
                sel = next(o for o in scene['options'] if o['text'] == choice)
                st.session_state.update({'love_meter': st.session_state.love_meter + sel['score'], 'answered': True, 'last_correct': sel['correct'], 'last_feedback': sel['feedback']})
                inject_result_animation(sel['correct']); st.rerun()
    else:
        if st.session_state.last_correct: st.success(st.session_state.last_feedback)
        else: st.error(st.session_state.last_feedback)
        inject_result_animation(st.session_state.last_correct)
        if st.button("次へ"):
            if st.session_state.stage < 9: st.session_state.update({'stage': st.session_state.stage+1, 'answered': False, 'stage_start_time': time.perf_counter()})
            else: st.session_state.app_mode = 'post_mapping'
            st.rerun()

elif st.session_state.app_mode == 'post_mapping':
    st.title("🎎 古文ロジック ～事後調査～")
    with st.form("post_form"):
        st.subheader("🖋️ 物語を経た変化を記されたし")
        for cat in CATEGORIES: st.session_state.post_text[cat] = st.text_area(cat, height=80)
        for q in LIKERT_QUESTIONS: st.session_state.post_likert[q] = st.select_slider(q, options=[1, 2, 3, 4, 5], value=3)
        if st.form_submit_button("保存して終了"):
            now = time.strftime("%Y-%m-%d %H:%M:%S"); file_exists = os.path.isfile(CSV_PATH)
            with open(CSV_PATH, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                if not file_exists: writer.writerow(["日時", "タイプ"] + CATEGORIES + LIKERT_QUESTIONS + ["ログ"])
                writer.writerow([now, "事後"] + [st.session_state.post_text[cat] for cat in CATEGORIES] + [st.session_state.post_likert[q] for q in LIKERT_QUESTIONS] + [str(st.session_state.results)])
            st.session_state.app_mode = 'complete'; st.rerun()

elif st.session_state.app_mode == 'complete':
    st.balloons(); st.header("🎊 義経伝、読了。感謝いたします"); st.success("すべてのデータが保存されました。")
    if st.button("最初に戻る"): st.session_state.clear(); st.rerun()