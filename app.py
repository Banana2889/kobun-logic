import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import time
import random

# --- 1. 基本設定 ---
# 全端末でフォントを安定させるため、標準的な明朝体・セリフ体へのフォントフォールバックを設定
st.set_page_config(page_title="古文ロジック・義経伝", layout="centered")

IMAGE_DIR = "kobungazou"

CATEGORIES = [
    "古文の単語や文法を学ぶことに関してどう思いますか",
    "古文の内容理解に関してどう思いますか",
    "古文の当時の時代の背景、価値観に関してどう思いますか",
    "古文の人間関係に次いでどう思いますか"
]

PRE_LIKERT_QUESTIONS = ["古文は面白いと思いますか"]
POST_LIKERT_QUESTIONS = ["古文は面白いと思いますか", "このゲームはおもしろかった？"]

# --- 2. Googleスプレッドシート接続 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. UI・デザイン（全端末対応・雅スタイル） ---
def inject_miyabi_style():
    st.markdown("""
    <style>
    /* 全体背景と基本文字 */
    .stApp { 
        background: linear-gradient(180deg, #0f0a1e 0%, #2d1a2a 100%); 
        color: #f3e5ab; 
        font-family: "Yu Mincho", "MS PMincho", "Hiragino Mincho ProN", serif; 
    }
    /* 巻物風ボックス */
    [data-testid="stForm"], [data-testid="stAlert"], .result-box { 
        background-color: #f8f4e6 !important; 
        padding: 25px !important; 
        border-radius: 10px; 
        border: 3px double #d4af37 !important; 
        color: #1a1a1a !important;
        margin-bottom: 20px;
    }
    .result-box { color: #000 !important; }
    /* 文字化け・視認性対策：黒文字強調 */
    [data-testid="stForm"] label, [data-testid="stForm"] p, .result-box h3, .result-box p { 
        color: #000000 !important; 
        font-weight: bold !important; 
    }
    /* 選択肢ボタン */
    [data-testid="stRadio"] { background-color: #ffffff !important; padding: 15px; border-radius: 10px; border: 2px solid #d4af37; }
    [data-testid="stRadio"] label { color: #000000 !important; font-weight: 900 !important; }
    
    /* アニメーション */
    @keyframes sakura-fall { 0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; } 100% { transform: translateY(100vh) rotate(360deg); opacity: 0; } }
    .sakura-bg { position: fixed; top: -10%; color: #ffb7c5; font-size: 24px; pointer-events: none; z-index: 1; animation: sakura-fall 12s linear infinite; }
    @keyframes rainbow-flash { 0% { filter: hue-rotate(0deg) brightness(1.5); } 100% { filter: hue-rotate(360deg) brightness(1.5); } }
    .rainbow-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 10000; mix-blend-mode: color-dodge; animation: rainbow-flash 0.5s linear infinite; background: radial-gradient(circle, rgba(255,255,255,0.4) 0%, transparent 70%); }
    </style>
    """ + "".join([f'<div class="sakura-bg" style="left:{random.randint(0,95)}%; animation-delay:{random.uniform(0,10)}s;">🌸</div>' for i in range(15)]) + " ", unsafe_allow_html=True)

def inject_result_animation(is_correct):
    anim_placeholder = st.empty()
    with anim_placeholder.container():
        if is_correct:
            st.markdown('<div class="rainbow-overlay"></div>', unsafe_allow_html=True)
            time.sleep(1.2)
        else:
            st.markdown('<div style="position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,80,0.4); pointer-events:none; z-index:9999;"></div>', unsafe_allow_html=True)
            time.sleep(1.0)
    anim_placeholder.empty()

# --- 4. セッション管理 ---
inject_miyabi_style()

if 'app_mode' not in st.session_state:
    st.session_state.update({
        'app_mode': 'pre_mapping', 'pre_text': {cat: "" for cat in CATEGORIES}, 
        'pre_likert': {q: 3 for q in PRE_LIKERT_QUESTIONS}, 
        'post_text': {cat: "" for cat in CATEGORIES}, 
        'post_likert': {q: 3 for q in POST_LIKERT_QUESTIONS}, 
        'stage': 0, 'answered': False, 'results': [], 'stage_start_time': 0, 
        'last_feedback': "", 'last_correct': False, 'current_options': []
    })

# --- 全10章の問題データ ---
scenes = [
   {"title": "第1章：闇夜の決意", "context": "平家全盛の世。修行の裏で密かに一族の再興を期して牙を研ぎ続ける。", "options": [{"text": "「昼は寺に読経し、夜は貴船の奥にのぼりて、兵法をぞ習ひける」", "score": 10, "correct": True, "feedback": "【正解】夜な夜な兵法に励む姿が目に浮かびます。"}, {"text": "「夜は貴船の奥にのぼりて、兵法をぞ習いおはします」", "score": -10, "correct": False, "feedback": "【失敗】自らの動作に最高敬語は不適切です。"}, {"text": "「夜は貴船の奥にのぼりて、兵法をぞ教えさせ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】教えを乞う立場であり、教える側ではございませぬ。"}, {"text": "「夜は貴船の奥にのぼりて、兵法をぞ遊びおはす」", "score": -10, "correct": False, "feedback": "【失敗】命がけの修行、遊びではございませぬ。"}]},
    {"title": "第2章：兄弟の再会", "context": "挙兵した兄の元へ駆けつけた場面。一族の悲願を果たすため、忠義を誓う。", "options": [{"text": "「御前に畏まりて、九郎義経、参り候ふ」", "score": 10, "correct": True, "feedback": "【正解】頼朝への深い敬意と忠誠心が伝わります。"}, {"text": "「御前に畏まりて、九郎義経、参り給ふ」", "score": -10, "correct": False, "feedback": "【失敗】己の参上に尊敬語は不要です。"}, {"text": "「御前に畏まりて、九郎義経、来たり候ふ」", "score": -10, "correct": False, "feedback": "【失敗】「参る」が最も相応しいでしょう。"}, {"text": "「御前に畏まりて、九郎義経、見えさせ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】敬語の使い方が不自然です。"}]},
    {"title": "第3章：激流を越えて", "context": "水の流れを突破しなければならない。自ら最前線へ。", "options": [{"text": "「まっさきに喚いて、宇治川の早瀬をぞ押し渡り給ふ」", "score": 10, "correct": True, "feedback": "【正解】勇猛果敢な姿が見事に描かれています。"}, {"text": "「まっさきに喚いて、宇治川の早瀬をぞ渡りおはします」", "score": -10, "correct": False, "feedback": "【失敗】「給ふ」が最も勢いがあります。"}, {"text": "「まっさきに喚いて、宇治川の早瀬をぞ見送り給ふ」", "score": -10, "correct": False, "feedback": "【失敗】見送っていては勝利は掴めませぬ。"}, {"text": "「まっさきに喚いて、宇治川の早瀬をぞなぶり給ふ」", "score": -10, "correct": False, "feedback": "【失敗】不適切な表現です。"}]},
    {"title": "第4章：絶壁の奇襲", "context": "敵陣に対し、誰も予想しない険しい地形から一気に攻め下る。", "options": [{"text": "「義経、三十騎ばかりを率て、真っ逆様におとし給ふ」", "score": 10, "correct": True, "feedback": "【正解】鵯越の奇襲、お見事です。"}, {"text": "「三十騎ばかりを率て、おとしおはします」", "score": -10, "correct": False, "feedback": "【失敗】「給ふ」が相応しい場面です。"}, {"text": "「三十騎ばかりを率て、山陰に隠れ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】奇襲になりませぬ。"}, {"text": "「三十騎ばかりを率て、見守り給ふ」", "score": -10, "correct": False, "feedback": "【失敗】勝利は得られませぬ。"}]},
    {"title": "第5章：嵐の船出", "context": "荒れる海を前に、厳しい条件を利用して敵の意表を突く。", "options": [{"text": "「追い風なればこそ、船をば出だすなれ」", "score": 10, "correct": True, "feedback": "【正解】これぞ義経の真骨頂。"}, {"text": "「追い風なればこそ、船をば出ださせ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】強意の「なれ」が相応しいです。"}, {"text": "「追い風なればこそ、船をば留むるなれ」", "score": -10, "correct": False, "feedback": "【失敗】機を逃します。"}, {"text": "「追い風なればこそ、船をば弄び給ふ」", "score": -10, "correct": False, "feedback": "【失敗】不真面目な印象を与えます。"}]},
    {"title": "第6章：誇りの回収", "context": "戦いの最中、弓を落としてしまう。敵の嘲笑を防ぐため自ら動く。", "options": [{"text": "「鞭をもって、弓をかき寄せ、ついに取りてぞ帰り給ふ」", "score": 10, "correct": True, "feedback": "【正解】弓流し。誇りを守り抜く執念です。"}, {"text": "「鞭をもって、弓を打ち捨て、ついに取りてぞ帰り給ふ」", "score": -10, "correct": False, "feedback": "【失敗】嘲笑の的になります。"}, {"text": "「鞭をもって、弓を拾い取らせ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】自らの手で取り戻すことに意味があります。"}, {"text": "「鞭をもって、弓を笑いおはします」", "score": -10, "correct": False, "feedback": "【失敗】笑っている場合ではございませぬ。"}]},
    {"title": "第7章：非情の采配", "context": "敵の機動力を奪うため、船を操る者たちを射るよう命じる。", "options": [{"text": "「あやまちすな、水手・梶取を射よ」", "score": 10, "correct": True, "feedback": "【正解】非情ながら勝利を決定づける采配です。"}, {"text": "「あやまちすな、水手・梶取を射させ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】軍の緊張感を表します。"}, {"text": "「あやまちすな、水手・梶取を助けよ」", "score": -10, "correct": False, "feedback": "【失敗】敵を止められませぬ。"}, {"text": "「あやまちすな、水手・梶取をなぶり殺せ」", "score": -10, "correct": False, "feedback": "【失敗】残酷すぎます。"}]},
    {"title": "第8章：窮地の跳躍", "context": "敵が迫る。身の軽さを活かして瞬時に距離を取る。", "options": [{"text": "「ゆらりと飛びのき、二丈ばかりの船のわたりを、飛びわたり給ふ」", "score": 10, "correct": True, "feedback": "【正解】八艘飛び、お見事。"}, {"text": "「ゆらりと飛びのきおはし、船のわたりをわたり給ふ」", "score": -10, "correct": False, "feedback": "【失敗】勢いが削がれます。"}, {"text": "「ゆらりと踏みとどまり、船のわたりを飛びわたり給ふ」", "score": -10, "correct": False, "feedback": "【失敗】捕まってしまいます。"}, {"text": "「ゆらりと立ち止まり給ひ、船のわたりを眺め給ふ」", "score": -10, "correct": False, "feedback": "【失敗】眺めている暇はございませぬ。"}]},
    {"title": "第9章：偽装の忍耐", "context": "正体を隠して関所を抜ける場面。仲間からの打擲に耐えて去る。", "options": [{"text": "「義経、杖を突いて、山伏の態にて、急ぎ通り給ふ」", "score": 10, "correct": True, "feedback": "【正解】安宅の関、緊迫の場面です。"}, {"text": "「義経、杖を突いて、山伏の態にて、歩ませ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】急ぐことが肝要です。"}, {"text": "「義経、杖を突いて、山伏の態にて、物申し給ふ」", "score": -10, "correct": False, "feedback": "【失敗】怪しまれます。"}, {"text": "「義経、杖を突いて、山伏の態にて、命じ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】不自然な振る舞いです。"}]},
    {"title": "第10章：静かなる終幕", "context": "尊厳を保つため、自ら幕を引く準備を整える。", "options": [{"text": "「持仏堂の戸を強くしめ、内よりかんぬきをさして、自害し給ふ」", "score": 10, "correct": True, "feedback": "【正解】最期まで誇り高き姿、感服いたしました。"}, {"text": "「戸を強くしめ、内よりかんぬきをさして、眠りおはす」", "score": -10, "correct": False, "feedback": "【失敗】眠る場面ではございませぬ。"}, {"text": "「戸を強くしめ、内よりかんぬきをさして、まどひ給ふ」", "score": -10, "correct": False, "feedback": "【失敗】義経公は惑いません。"}, {"text": "「戸を強くしめ、内よりかんぬきをさして、逃げおはします」", "score": -10, "correct": False, "feedback": "【失敗】逃げる道は残されておりませぬ。"}]}

# --- 5. メインロジック ---
if st.session_state.app_mode == 'pre_mapping':
    st.title("🎎 古文ロジック ～事前調査～")
    with st.form("pre_form"):
        for cat in CATEGORIES: st.session_state.pre_text[cat] = st.text_area(cat, height=80)
        for q in PRE_LIKERT_QUESTIONS: st.session_state.pre_likert[q] = st.select_slider(q, options=[1, 2, 3, 4, 5], value=3)
        if st.form_submit_button("物語へ進む"):
            st.session_state.app_mode = 'game'; st.session_state.stage_start_time = time.perf_counter(); st.rerun()

elif st.session_state.app_mode == 'game':
    scene = scenes[st.session_state.stage]
    if not st.session_state.current_options:
        st.session_state.current_options = random.sample(scene['options'], len(scene['options']))

    st.header(f"✨ {scene['title']}")
    st.progress(st.session_state.stage / 10)
    st.info(f"📜 状況説明: {scene['context']}")
    
    img_name = f"gazou{st.session_state.stage + 1}.png"
    img_path = os.path.join(IMAGE_DIR, img_name)
    if os.path.exists(img_path): st.image(img_path, width=700)
    else: st.warning(f"画像が見つかりませぬ: {img_name}")

    if not st.session_state.answered:
        choice = st.radio("👇 適切な言の葉を選びなさい:", [o['text'] for o in st.session_state.current_options], index=None)
        if st.button("伝える"):
            if choice:
                st.session_state.results.append(round(time.perf_counter() - st.session_state.stage_start_time, 2))
                sel = next(o for o in scene['options'] if o['text'] == choice)
                st.session_state.update({'answered': True, 'last_correct': sel['correct'], 'last_feedback': sel['feedback']})
                inject_result_animation(sel['correct']); st.rerun()
    else:
        if st.session_state.last_correct: st.success(st.session_state.last_feedback)
        else: st.error(st.session_state.last_feedback)
        if st.button("次へ"):
            if st.session_state.stage < 9: st.session_state.update({'stage': st.session_state.stage+1, 'answered': False, 'current_options': [], 'stage_start_time': time.perf_counter()})
            else: st.session_state.app_mode = 'post_mapping'
            st.rerun()

elif st.session_state.app_mode == 'post_mapping':
    st.title("🎎 古文ロジック ～事後調査～")
    with st.form("post_form"):
        for cat in CATEGORIES: st.session_state.post_text[cat] = st.text_area(cat, height=80)
        for q in POST_LIKERT_QUESTIONS: st.session_state.post_likert[q] = st.select_slider(q, options=[1, 2, 3, 4, 5], value=3)
        if st.form_submit_button("記録を保存して終了"):
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                # バックアップとしてスプレッドシートへも送信（失敗しても次へ進む）
                df = conn.read(worksheet="Sheet1", ttl=0)
                pre_dict = {"日時": now, "タイプ": "事前", **st.session_state.pre_text, **st.session_state.pre_likert}
                post_dict = {"日時": now, "タイプ": "事後", **st.session_state.post_text, **st.session_state.post_likert, "ログ": str(st.session_state.results)}
                updated_df = pd.concat([df, pd.DataFrame([pre_dict, post_dict])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
            except: pass
            st.session_state.app_mode = 'complete'; st.rerun()

elif st.session_state.app_mode == 'complete':
    st.balloons()
    st.header("🎊 義経伝、読了。感謝いたします")
    
    # --- スクリーンショット用集計エリア ---
    st.markdown("### ⚠️ 【重要】以下の画面をスクリーンショットして送ってください")
    
    res_html = f"""
    <div class="result-box">
        <h3>📊 研究回答データ記録</h3>
        <p><strong>記録日時:</strong> {time.strftime("%Y/%m/%d %H:%M")}</p>
        <hr>
        <p><strong>【回答時間ログ（第1〜10章）】</strong><br>{st.session_state.results}</p>
        <hr>
        <p><strong>【事前アンケート】</strong><br>評価値: {list(st.session_state.pre_likert.values())}</p>
        <p><strong>【事後アンケート】</strong><br>評価値: {list(st.session_state.post_likert.values())}</p>
        <hr>
        <p style="font-size: 0.8rem;">※この画面をキャプチャし、研究者へ提出してください。</p>
    </div>
    """
    st.markdown(res_html, unsafe_allow_html=True)
    
    if st.button("最初に戻る"): st.session_state.clear(); st.rerun()