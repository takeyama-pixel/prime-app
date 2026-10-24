import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import os
import json
import base64

UPLOAD_DIR = "prime_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DATA_FILE = "prime_members_data.json"

def get_image_base64(path):
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            pass
    return None

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and "parent_id" in data[0]:
                    for m in data:
                        if "introducer" not in m:
                            m["introducer"] = ""
                        if "remarks" not in m:
                            m["remarks"] = ""
                    return data
        except Exception:
            pass
            
    return [
        {"id": 1, "name": "大西 真由美", "parent_id": None, "binary_side": None, "rank": "リーダー", "status": "アクティブ", "seminar_count": 5, "introducer": "", "remarks": "", "image": ""},
        {"id": 2, "name": "山田 太郎", "parent_id": 1, "binary_side": "左", "rank": "リーダー", "status": "アクティブ", "seminar_count": 3, "introducer": "大西 真由美", "remarks": "要フォロー", "image": ""},
        {"id": 3, "name": "佐藤 花子", "parent_id": 1, "binary_side": "右", "rank": "メンバー", "status": "アクティブ", "seminar_count": 1, "introducer": "大西 真由美", "remarks": "", "image": ""},
    ]

def save_data(members):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=4)

st.title("プライム共済 組織・教育管理アプリ")
st.write("マサキ医院長向け / 開発：石川副委員長[cite: 1, 2]")

if "members" not in st.session_state:
    st.session_state["members"] = load_data()

menu = st.sidebar.selectbox("メニュー選択", ["組織図・紹介ツリー", "新規メンバー登録", "メンバーの編集・削除", "グループ全体集計"])

# --- 1. 新規メンバー登録 ---
if menu == "新規メンバー登録":
    st.subheader("➕ 新規メンバーの追加・バイナリー配置")
    st.write("組織図上の誰の、左右どちらに配置するかを指定して登録します。")
    
    members = st.session_state["members"]
    
    with st.form("member_form"):
        name = st.text_input("メンバー氏名")
        
        parent_options = {m["id"]: f"{m['name']} ({m['rank']})" for m in members}
        parent_options[0] = "【トップ（最上部）】"
        
        selected_parent_id = st.selectbox(
            "配置先の親（上位メンバー）を選択", 
            options=list(parent_options.keys()), 
            format_func=lambda x: parent_options[x]
        )
        
        binary_side = st.selectbox("バイナリー配置（左右）", ["左", "右"])
        
        rank = st.selectbox("ランク・タイトル", ["メンバー", "サブリーダー", "リーダー"])
        status = st.selectbox("ステータス", ["アクティブ", "新規", "休眠"])
        seminar_count = st.number_input("セミナー参加回数", min_value=0, value=0)
        
        introducer = st.text_input("紹介者（自由入力）")
        remarks = st.text_area("備考欄・メモ書き")
        
        submitted = st.form_submit_button("メンバーを登録する")
        
        if submitted:
            if not name:
                st.warning("氏名を入力してください。")
            else:
                p_id = None if selected_parent_id == 0 else selected_parent_id
                
                if p_id is not None:
                    existing = [m for m in members if m.get("parent_id") == p_id and m.get("binary_side") == binary_side]
                    if existing:
                        st.error(f"エラー: 選択した親の「{binary_side}」側には、すでにメンバー「{existing[0]['name']}」が配置されています！")
                    else:
                        new_id = max([m["id"] for m in members], default=0) + 1
                        members.append({
                            "id": new_id,
                            "name": name,
                            "parent_id": p_id,
                            "binary_side": binary_side,
                            "rank": rank,
                            "status": status,
                            "seminar_count": seminar_count,
                            "introducer": introducer,
                            "remarks": remarks,
                            "image": ""
                        })
                        save_data(members)
                        st.success(f"メンバー「{name}」を配置しました！")
                else:
                    new_id = max([m["id"] for m in members], default=0) + 1
                    members.append({
                        "id": new_id,
                        "name": name,
                        "parent_id": None,
                        "binary_side": None,
                        "rank": rank,
                        "status": status,
                        "seminar_count": seminar_count,
                        "introducer": introducer,
                        "remarks": remarks,
                        "image": ""
                    })
                    save_data(members)
                    st.success(f"トップメンバー「{name}」を追加しました！")

# --- 2. 組織図・紹介ツリー（全体俯瞰・注目リーダー拡大モード ＆ 印刷用PDF対応ビュー） ---
elif menu == "組織図・紹介ツリー":
    st.subheader("🌳 バイナリー組織図（全体俯瞰・結線ツリー）")
    
    members = st.session_state["members"]
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        view_mode = st.selectbox("表示モード", ["通常表示", "全体俯瞰（コンパクト）モード"])
    with col_opt2:
        leader_candidates = [m["name"] for m in members]
        highlight_leaders = st.multiselect("⭐ ミーティングで大きく強調するリーダー（3〜5人選択可）", options=leader_candidates, default=[])

    if view_mode == "全体俯瞰（コンパクト）モード":
        img_size = "28px"
        card_width = "90px"
        font_size = "9px"
        pad_val = "10px 20px"
    else:
        img_size = "42px"
        card_width = "110px"
        font_size = "11px"
        pad_val = "20px 40px"

    def render_tree_li(member_id):
        m = next((item for item in members if item["id"] == member_id), None)
        if not m:
            return '<li><div class="node-card empty">未配置</div></li>'
            
        is_highlighted = m["name"] in highlight_leaders
        current_img_size = "64px" if is_highlighted else img_size
        current_card_width = "130px" if is_highlighted else card_width
        highlight_border = "3px solid #ff9800" if is_highlighted else "2px solid #4CAF50"
        highlight_bg = "#fff8e1" if is_highlighted else "transparent"

        img_b64 = get_image_base64(m.get("image", ""))
        if img_b64:
            img_tag = f'<img src="{img_b64}" class="member-img" style="width: {current_img_size}; height: {current_img_size}; border: {highlight_border};">'
        else:
            img_tag = f'<div class="member-img no-img" style="width: {current_img_size}; height: {current_img_size};">写真なし</div>'
            
        parent_info = ""
        if m.get("parent_id") is not None:
            p_obj = next((item for item in members if item["id"] == m["parent_id"]), None)
            if p_obj:
                side = m.get("binary_side", "")
                parent_info = f'<div class="parent-badge">{p_obj["name"]} - {side}</div>'
        else:
            parent_info = '<div class="parent-badge top">👑 トップ階層</div>'
        
        left_child = next((item for item in members if item.get("parent_id") == m["id"] and item.get("binary_side") == "左"), None)
        right_child = next((item for item in members if item.get("parent_id") == m["id"] and item.get("binary_side") == "右"), None)
        
        card_html = f"""
        <div class="node-card" style="width: {current_card_width}; background: {highlight_bg};">
            {parent_info}
            {img_tag}
            <div class="name" style="font-size: {font_size};">{m['name']}</div>
            <div class="info" style="font-size: 8px;">{m['rank']} (参:{m['seminar_count']}回)</div>
        </div>
        """
        
        if not left_child and not right_child:
            return f"<li>{card_html}</li>"
            
        left_html = render_tree_li(left_child["id"]) if left_child else '<li><div class="node-card empty">未配置</div></li>'
        right_html = render_tree_li(right_child["id"]) if right_child else '<li><div class="node-card empty">未配置</div></li>'
        
        return f"""
        <li>
            {card_html}
            <ul>
                {left_html}
                {right_html}
            </ul>
        </li>
        """

    roots = [m for m in members if m.get("parent_id") is None]
    
    tree_lis = ""
    for root in roots:
        tree_lis += render_tree_li(root["id"])

    # 全画面・横スクロールのツリー全体をキレイに1枚のPDF/印刷にするための専用レイアウトスタイル
    full_html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Meiryo, sans-serif;
            background-color: #ffffff;
            margin: 0;
            padding: {pad_val};
            display: block;
            width: 100%;
            box-sizing: border-box;
        }}
        .tree-container {{
            display: flex;
            justify-content: center;
            width: 100%;
            overflow-x: auto;
        }}
        .tree ul {{
            padding-top: 20px; 
            position: relative;
            transition: all 0.5s;
            display: flex;
            justify-content: center;
            list-style-type: none;
            margin: 0 auto;
            padding-left: 0;
        }}
        .tree li {{
            float: left; 
            text-align: center;
            list-style-type: none;
            position: relative;
            padding: 20px 10px 0 10px;
            transition: all 0.5s;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .tree li::before, .tree li::after {{
            content: '';
            position: absolute; 
            top: 0; 
            right: 50%;
            border-top: 2px solid #aaa;
            width: 50%; 
            height: 20px;
        }}
        .tree li::after {{
            right: auto; 
            left: 50%;
            border-left: 2px solid #aaa;
        }}
        .tree li:only-child::after, .tree li:only-child::before {{
            display: none;
        }}
        .tree li:only-child {{ 
            padding-top: 0; 
        }}
        .tree li:first-child::before, .tree li:last-child::after {{
            border: 0px none;
        }}
        .tree li:last-child::before {{
            border-right: 2px solid #aaa;
            border-radius: 0 6px 0 0;
        }}
        .tree li:first-child::after {{
            border-radius: 6px 0 0 0;
        }}
        .tree ul ul::before {{
            content: ''; 
            position: absolute; 
            top: 0; 
            left: 50%;
            border-left: 2px solid #aaa;
            width: 0; 
            height: 20px;
        }}
        .node-card {{
            text-align: center;
            padding: 4px;
            border-radius: 8px;
            z-index: 2;
            position: relative;
        }}
        .node-card.empty {{
            width: 70px;
            height: 50px;
            border: 2px dashed #ccc;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 8px;
            background: #fafafa;
            margin-top: 10px;
        }}
        .parent-badge {{
            font-size: 8px;
            font-weight: bold;
            color: #1565c0;
            background: #e3f2fd;
            padding: 1px 5px;
            border-radius: 8px;
            display: inline-block;
            margin-bottom: 2px;
            white-space: nowrap;
        }}
        .parent-badge.top {{
            color: #2e7d32;
            background: #e8f5e9;
        }}
        .member-img {{
            border-radius: 50%;
            object-fit: cover;
            margin: 0 auto 2px auto;
            display: block;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .member-img.no-img {{
            border-radius: 50%;
            background: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 8px;
            color: #666;
            margin: 0 auto 2px auto;
        }}
        .name {{
            font-weight: bold;
            color: #333;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .info {{
            font-size: 8px;
            color: #666;
        }}
        
        /* 印刷・PDF出力時の最適化設定 */
        @media print {{
            body {{
                background-color: #ffffff;
            }}
            .tree-container {{
                overflow: visible !important;
            }}
        }}
    </style>
    </head>
    <body>
        <div style="text-align: center; font-weight: bold; font-size: 16px; margin-bottom: 10px; color: #333;">プライム共済 組織図レポート</div>
        <div class="tree-container">
            <div class="tree">
                <ul>
                    {tree_lis}
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 組織図の表示
    components.html(full_html, height=520, scrolling=True)

    st.markdown("### 📄 組織図のPDF保存・LINE/メール共有")
    st.write("下のボタンを押すと、**組織図全体が綺麗に収まったPDF保存画面（印刷画面）**が直接開きます。「PDFとして保存」を選択してください。")
    
    # ブラウザの機能を使って組織図全体をPDFとして出力・印刷するためのボタン
    pdf_button_html = f"""
    <html>
    <head>
