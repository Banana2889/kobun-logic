import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import time
import random

# --- 1. 基本設定 ---
st.set_page_config(page_title="古文ロジック・恋愛抄 ～義経伝・極雅～", layout="centered")

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

# --- 3. UI・デザイン ---
def inject_miyabi_style():
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0f0a1e 0%, #2d1a2a 100%); color: #f3e5ab; font-family: "Hiragino Mincho ProN", "Yu Mincho", "MS PMincho", "serif"; }
    [data-testid="stForm"], [data-testid="stAlert"], .result-box { background-color: #f8f4e6 !important; padding: 25px !important; border-radius: 10px; border: 3px double #d4af37 !important; color: #1a1a1a !important; margin-bottom: 20px; }
    .result-box { background-color: #ffffff !important; color: #000000 !important; border: 5px solid #000000 !important; }
    [data-testid="stRadio"] { background-color: #ffffff !important; padding: 15px; border-radius: 10px; border: 2px solid #d4af37; }
    [data-testid="stRadio"] label { color: #000000 !important; font-weight: bold !important; }
    @keyframes sakura-fall { 0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; } 100% { transform: translateY(100vh) rotate(360deg); opacity: 0; } }
    .sakura-bg { position: fixed; top: -10%; color: #ffb7c5; font-size: 24px; pointer-events: none; z-index: 1; animation: sakura-fall 12s linear infinite; }
    </style>
    """ + "".join([f'<div class="sakura-bg" style="left:{random.randint(0,95)}%; animation-delay:{random.uniform(0,10)}s;">🌸</div>' for i in range(15)]) + " ", unsafe_allow_html=True)

def inject_result_animation(is_correct):
    anim_placeholder = st.empty()
    if is_correct:
        petals = "".join([f'<div style="position:fixed; top:50%; left:50%; font-size:30px; color:#ffb7c5; pointer-events:none; z-index:10001; animation: explode 2s ease-out forwards; --tx:{random.randint(-200,200)}vw; --ty:{random.randint(-200,200)}vh; --tr:{random.randint(0,720)}deg; animation-delay:{random.uniform(0,0.2)}s;">🌸</div>' for _ in range(50)])
        anim_placeholder.markdown(petals + "<style>@keyframes explode { 0% { opacity:0; transform:translate(-50%,-50%) scale(0.1); } 20% { opacity:1; } 100% { opacity:0; transform:translate(var(--tx), var(--ty)) scale(2) rotate(var(--tr)); } }</style>", unsafe_allow_html=True)
        time.sleep(1.2)
    else:
        anim_placeholder.markdown('<div style="position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,80,0.4); pointer-events:none; z-index:9999;"></div>', unsafe_allow_html=True)
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
        'last_feedback': "", 'last_correct': False, 'current_options': [],
        'total_mistakes': 0, 'consecutive_mistakes': 0, 'ending_id': ""
    })

# --- 全10章の問題データ ---
scenes = [
    {"title": "第1章：闇夜の決意", "context": "修行の裏で密かに一族の再興を期して牙を研ぎ続ける。", "hint": "「ける」は過去を表す助動詞です。", "options": [{"text": "「昼は寺に読経し、夜は貴船の奥にのぼりて、兵法をぞ習ひける」", "correct": True, "feedback": "【正解】夜な夜な兵法に励む姿が目に浮かびます。"}, {"text": "「夜は貴船の奥にのぼりて、兵法をぞ習いおはします」", "correct": False, "feedback": "【失敗】自らの動作に最高敬語は不適切です。"}]},
    {"title": "第2章：兄弟の再会", "context": "挙兵した兄の元へ駆けつけ、忠義を誓う。", "hint": "謙譲語の「参る」に注目しましょう。", "options": [{"text": "「御前に畏まりて、九郎義経、参り候ふ」", "correct": True, "feedback": "【正解】兄・頼朝への忠誠心が伝わります。"}, {"text": "「御前に畏まりて、九郎義経、参り給ふ」", "correct": False, "feedback": "【失敗】己の動作に尊敬語は使いません。"}]},
    {"title": "第3章：激流を越えて", "context": "宇治川の早瀬を突破しなければならない。", "hint": "「押し渡る」に尊敬の助動詞を添えましょう。", "options": [{"text": "「まっさきに喚いて、宇治川の早瀬をぞ押し渡り給ふ」", "correct": True, "feedback": "【正解】勇猛果敢な姿が見事に描かれています。"}, {"text": "「まっさきに喚いて、宇治川の早瀬をぞ見送り給ふ」", "correct": False, "feedback": "【失敗】渡らねば勝利はありませぬ。"}]},
    {"title": "第4章：絶壁の奇襲", "context": "険しい地形から一気に攻め下る。", "hint": "「おとす」に尊敬語を使い、緊迫感を出しなさい。", "options": [{"text": "「義経、三十騎ばかりを率て、真っ逆様におとし給ふ」", "correct": True, "feedback": "【正解】鵯越の奇襲、お見事です。"}, {"text": "「三十騎ばかりを率て、山陰に隠れ給ふ」", "correct": False, "feedback": "【失敗】奇襲になりませぬ。"}]},
    {"title": "第5章：嵐の船出", "context": "荒れる海を前に、敵の意表を突く。", "hint": "断定・強調の「なれ」を使いましょう。", "options": [{"text": "「追い風なればこそ、船をば出だすなれ」", "correct": True, "feedback": "【正解】これぞ義経の真骨頂。"}, {"text": "「追い風なればこそ、船をば留むるなれ」", "correct": False, "feedback": "【失敗】機を逃します。"}]},
    {"title": "第6章：誇りの回収", "context": "戦いの最中、弓を落としてしまう。", "hint": "「かき寄せる」という動作が重要です。", "options": [{"text": "「鞭をもって、弓をかき寄せ、ついに取りてぞ帰り給ふ」", "correct": True, "feedback": "【正解】弓流し。武士の誇りを守りました。"}, {"text": "「鞭をもって、弓を打ち捨て、ついに取りてぞ帰り給ふ」", "correct": False, "feedback": "【失敗】敵の嘲笑を浴びてしまいます。"}]},
    {"title": "第7章：非情の采配", "context": "敵の機動力を奪うため、船人を狙う。", "hint": "命令形「射よ」を使いましょう。", "options": [{"text": "「あやまちすな、水手・梶取を射よ」", "correct": True, "feedback": "【正解】勝利を決定づける非情の采配です。"}, {"text": "「あやまちすな、水手・梶取を助けよ」", "correct": False, "feedback": "【失敗】敵を止められませぬ。"}]},
    {"title": "第8章：窮地の跳躍", "context": "敵が迫る。船から船へ飛び移る。", "hint": "「飛びわたる」という瞬発力を表現しましょう。", "options": [{"text": "「ゆらりと飛びのき、二丈ばかりの船のわたりを、飛びわたり給ふ」", "correct": True, "feedback": "【正解】八艘飛び、お見事。"}, {"text": "「ゆらりと立ち止まり給ひ、船のわたりを眺め給ふ」", "correct": False, "feedback": "【失敗】捕まってしまいます。"}]},
    {"title": "第9章：偽装の忍耐", "context": "山伏の姿で関所を抜けようとする。", "hint": "怪しまれないよう「急ぎ通る」ことが肝要です。", "options": [{"text": "「義経、杖を突いて、山伏の態にて、急ぎ通り給ふ」", "correct": True, "feedback": "【正解】安宅の関、緊迫の場面です。"}, {"text": "「義経、杖を突いて、山伏の態にて、物申し給ふ」", "correct": False, "feedback": "【失敗】怪しまれてしまいます。"}]},
    {"title": "第10章：静かなる終幕", "context": "自ら幕を引く準備を整える。", "hint": "最期の動作「自害」を敬語で表現します。", "options": [{"text": "「持仏堂の戸を強くしめ、内よりかんぬきをさして、自害し給ふ」", "correct": True, "feedback": "【正解】最期まで誇り高き姿、感服いたしました。"}, {"text": "「戸を強くしめ、内よりかんぬきをさして、逃げおはします」", "correct": False, "feedback": "【失敗】もはや道は残されておりませぬ。"}]}
]

# --- 5. メイン進行 ---
if st.session_state.app_mode == 'pre_mapping':
    st.title("🎎 事前調査")
    with st.form("pre_form"):
        for cat in CATEGORIES: st.session_state.pre_text[cat] = st.text_area(cat, height=80)
        for q in PRE_LIKERT_QUESTIONS: st.session_state.pre_likert[q] = st.select_slider(q, options=[1, 2, 3, 4, 5], value=3)
        if st.form_submit_button("物語を開始する"):
            st.session_state.app_mode = 'game'; st.session_state.stage_start_time = time.perf_counter(); st.rerun()

elif st.session_state.app_mode == 'game':
    scene = scenes[st.session_state.stage]
    if not st.session_state.current_options:
        # 4択にするために他の選択肢をダミーとして追加
        options = scene['options'] + [{"text": "不適切な選択肢A", "correct": False, "feedback": "不適切です"}, {"text": "不適切な選択肢B", "correct": False, "feedback": "不適切です"}]
        st.session_state.current_options = random.sample(options, len(options))

    st.header(f"✨ {scene['title']}")
    st.info(f"📜 {scene['context']}")
    
    img_name = f"gazou{st.session_state.stage + 1}.png"
    img_path = os.path.join(IMAGE_DIR, img_name)
    if os.path.exists(img_path): st.image(img_path, use_container_width=True)

    if not st.session_state.answered:
        # ヒントボタン
        with st.expander("💡 文の導き（ヒント）"):
            st.write(scene['hint'])
            
        choice = st.radio("👇 言の葉を選んでください:", [o['text'] for o in st.session_state.current_options], index=None)
        if st.button("伝える"):
            if choice:
                thinking_time = round(time.perf_counter() - st.session_state.stage_start_time, 2)
                st.session_state.results.append(thinking_time)
                sel = next(o for o in st.session_state.current_options if o['text'] == choice)
                
                # 判定
                is_correct = sel['correct']
                if not is_correct:
                    st.session_state.total_mistakes += 1
                    st.session_state.consecutive_mistakes += 1
                else:
                    st.session_state.consecutive_mistakes = 0
                
                st.session_state.update({'answered': True, 'last_correct': is_correct, 'last_feedback': sel['feedback']})
                inject_result_animation(is_correct)
                
                # エンディング条件チェック
                if st.session_state.consecutive_mistakes >= 2:
                    st.session_state.ending_id = "断絶の絆"; st.session_state.app_mode = 'post_mapping'; st.rerun()
                elif st.session_state.stage < 5 and st.session_state.total_mistakes >= 2:
                    st.session_state.ending_id = "迷いの中道"; st.session_state.app_mode = 'post_mapping'; st.rerun()
                elif st.session_state.stage < 8 and st.session_state.total_mistakes >= 2:
                    st.session_state.ending_id = "薄氷の信頼"; st.session_state.app_mode = 'post_mapping'; st.rerun()
                
                st.rerun()
    else:
        st.write(st.session_state.last_feedback)
        if st.button("次へ進む"):
            if st.session_state.stage < 9:
                st.session_state.update({'stage': st.session_state.stage+1, 'answered': False, 'current_options': [], 'stage_start_time': time.perf_counter()})
                st.rerun()
            else:
                # 最終判定
                if st.session_state.total_mistakes == 0: st.session_state.ending_id = "極雅・義経伝"
                else: st.session_state.ending_id = "落花の終幕"
                st.session_state.app_mode = 'post_mapping'; st.rerun()

elif st.session_state.app_mode == 'post_mapping':
    st.title("🎎 事後調査")
    with st.form("post_form"):
        for cat in CATEGORIES: st.session_state.post_text[cat] = st.text_area(cat, height=80)
        for q in POST_LIKERT_QUESTIONS: st.session_state.post_likert[q] = st.select_slider(q, options=[1, 2, 3, 4, 5], value=3)
        if st.form_submit_button("結果を表示する"):
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                df = conn.read(worksheet="Sheet1", ttl=0)
                pre_dict = {"日時": now, "タイプ": "事前", **st.session_state.pre_text, **st.session_state.pre_likert}
                post_dict = {"日時": now, "タイプ": "事後", **st.session_state.post_text, **st.session_state.post_likert, "ログ": f"Ending: {st.session_state.ending_id} / {st.session_state.results}"}
                updated_df = pd.concat([df, pd.DataFrame([pre_dict, post_dict])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
            except: pass
            st.session_state.app_mode = 'complete'; st.rerun()

elif st.session_state.app_mode == 'complete':
    st.header(f"📜 終幕：{st.session_state.ending_id}")
    
    if st.session_state.ending_id == "極雅・義経伝":
        st.balloons(); st.success("【全問正解】義経公との絆は永遠のものとなりました。雅なる知識、感服いたしました。")
    elif st.session_state.ending_id == "落花の終幕":
        st.warning("【ノーマルエンド】物語は終わりを迎えましたが、あなたの知識にはまだ磨く余地があるようです。")
    else:
        st.error("【バッドエンド】義経公との道は途絶えてしまいました。古文の理（ことわり）を再度学び直しましょう。")

    st.markdown("### ⚠️ 【重要】以下の画面をスクリーンショットして提出してください")
    res_html = f"""
    <div class="result-box">
        <h3 style="text-align: center; border-bottom: 2px solid #000;">📜 研究回答データ記録 📜</h3>
        <p><strong>■ 到達した終幕:</strong> {st.session_state.ending_id}</p>
        <p><strong>■ 第1〜10章 思考時間(秒):</strong><br>{st.session_state.results}</p>
        <p><strong>■ 合計ミス回数:</strong> {st.session_state.total_mistakes}回</p>
        <hr style="border: 1px dashed #000;">
        <p><strong>■ アンケート評価値:</strong><br>事前:{list(st.session_state.pre_likert.values())} / 事後:{list(st.session_state.post_likert.values())}</p>
        <p style="text-align: center; font-size: 0.7rem; border-top: 1px solid #000; padding-top: 5px;">この画面を保存して研究者へ送信してください。</p>
    </div>
    """
    st.markdown(res_html, unsafe_allow_html=True)
    if st.button("最初に戻る"): st.session_state.clear(); st.rerun()