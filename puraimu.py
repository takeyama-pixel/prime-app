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
                    return data
        except Exception:
            pass
            
    return [
        {"id": 1, "name": "大西 真由美", "parent_id": None, "binary_side": None, "rank": "リーダー", "status": "アクティブ", "seminar_count": 5, "image": ""},
        {"id": 2, "name": "山田 太郎", "parent_id": 1, "binary_side": "左", "rank": "リーダー", "status": "アクティブ", "seminar_count": 3, "image": ""},
        {"id": 3, "name": "佐藤 花子", "parent_id": 1, "binary_side": "右", "rank": "メンバー", "status": "アクティブ", "seminar_count": 1, "image": ""},
    ]

def save_data(members):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=4)

st.title("プライム共済 組織・教育管理アプリ")
st.write("マサキ医院長向け / 開発：石川副委員長")

if "members" not in st.session_state:
    st.session_state["members"] = load_data()

menu = st.sidebar.selectbox("メニュー選択", ["組織図・紹介ツリー", "新規メンバー登録", "メンバーの削除・編集", "グループ全体集計"])

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
                        "image": ""
                    })
                    save_data(members)
                    st.success(f"トップメンバー「{name}」を追加しました！")

# --- 2. 組織図・紹介ツリー（無限階層・クリーンなツリー構造） ---
elif menu == "組織図・紹介ツリー":
    st.subheader("🌳 バイナリー組織図（無限階層・すっきりツリー構造）")
    st.write("左右どちらにも自由にスクロールして全体を見渡せます。")
    
    members = st.session_state["members"]
    
    def render_node_html(member_id):
        m = next((item for item in members if item["id"] == member_id), None)
        if not m:
            return '<div class="node-card empty">未配置</div>'
            
        img_b64 = get_image_base64(m.get("image", ""))
        if img_b64:
            img_tag = f'<img src="{img_b64}" class="member-img">'
        else:
            img_tag = '<div class="member-img no-img">写真なし</div>'
            
        # 親の名前 + 左右バッジを写真の上に表示
        parent_info = ""
        if m.get("parent_id"):
            p_obj = next((item for item in members if item["id"] == m["parent_id"]), None)
            if p_obj:
                side = m.get("binary_side", "")
                parent_info = f'<div class="parent-badge">{p_obj["name"]} - {side}</div>'
        else:
            parent_info = '<div class="parent-badge top">👑 トップ</div>'
        
        left_child = next((item for item in members if item.get("parent_id") == m["id"] and item.get("binary_side") == "左"), None)
        right_child = next((item for item in members if item.get("parent_id") == m["id"] and item.get("binary_side") == "右"), None)
        
        left_html = render_node_html(left_child["id"]) if left_child else '<div class="node-wrapper"><div class="node-card empty">未配置</div></div>'
        right_html = render_node_html(right_child["id"]) if right_child else '<div class="node-wrapper"><div class="node-card empty">未配置</div></div>'
        
        if not left_child and not right_child:
            return f"""
            <div class="node-wrapper">
                <div class="node-card">
                    {parent_info}
                    {img_tag}
                    <div class="name">{m['name']}</div>
                    <div class="info">{m['rank']} (参:{m['seminar_count']}回)</div>
                </div>
            </div>
            """
            
        return f"""
        <div class="node-wrapper">
            <div class="node-card">
                {parent_info}
                {img_tag}
                <div class="name">{m['name']}</div>
                <div class="info">{m['rank']} (参:{m['seminar_count']}回)</div>
            </div>
            <div class="line-container">
                <div class="h-line"></div>
            </div>
            <div class="children-container">
                <div class="child-branch">{left_html}</div>
                <div class="child-branch">{right_html}</div>
            </div>
        </div>
        """

    roots = [m for m in members if m.get("parent_id") is None]
    
    trees_html = ""
    for root in roots:
        trees_html += render_node_html(root["id"])

    # 接続線のズレやはみ出しを完全に解消した最新レイアウトCSS
    full_html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Meiryo, sans-serif;
            background-color: transparent;
            margin: 0;
            padding: 20px;
            display: inline-block;
            min-width: 100%;
            box-sizing: border-box;
        }}
        .tree-root {{
            display: flex;
            flex-direction: column;
            align-items: center;
            width: max-content;
            margin: 0 auto;
        }}
        .node-wrapper {{
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            margin: 0 8px;
        }}
        .node-card {{
            text-align: center;
            width: 110px;
            background: transparent;
            padding: 2px;
            z-index: 2;
            position: relative;
        }}
        .node-card.empty {{
            width: 80px;
            height: 60px;
            border: 2px dashed #ccc;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 9px;
            background: #fafafa;
            margin-top: 10px;
        }}
        .parent-badge {{
            font-size: 9px;
            font-weight: bold;
            color: #1565c0;
            background: #e3f2fd;
            padding: 2px 6px;
            border-radius: 10px;
            display: inline-block;
            margin-bottom: 3px;
            white-space: nowrap;
        }}
        .parent-badge.top {{
            color: #2e7d32;
            background: #e8f5e9;
        }}
        .member-img {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #4CAF50;
            margin: 0 auto 2px auto;
            display: block;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .member-img.no-img {{
            width: 42px;
            height: 42px;
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
            font-size: 11px;
            color: #333;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .info {{
            font-size: 8px;
            color: #666;
        }}
        
        /* 接続線のデザインをスッキリ整理 */
        .line-container {{
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 15px;
            position: relative;
        }}
        .line-container::before {{
            content: '';
            width: 2px;
            height: 15px;
            background-color: #bbb;
        }}
        .h-line {{
            position: absolute;
            bottom: 0;
            left: 25%;
            right: 25%;
            height: 2px;
            background-color: #bbb;
        }}
        .children-container {{
            display: flex;
            justify-content: center;
            position: relative;
            width: 100%;
        }}
        .child-branch {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0 10px;
            position: relative;
        }}
        .child-branch::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            width: 2px;
            height: 15px;
            background-color: #bbb;
            transform: translateX(-50%);
        }}
    </style>
    </head>
    <body>
        <div class="tree-root">
            {trees_html}
        </div>
    </body>
    </html>
    """
    
    components.html(full_html, height=540, scrolling=True)

    st.markdown("---")
    st.subheader("📋 メンバー詳細 ＆ 写真・セミナー回数管理")
    st.write("各メンバーを展開すると、顔写真のアップロードや情報の変更ができます。")
    
    for m in members:
        parent_name = "トップ"
        if m.get("parent_id"):
            p_obj = next((item for item in members if item["id"] == m["parent_id"]), None)
            if p_obj:
                parent_name = p_obj["name"]
                
        side_info = f" / 位置: {m.get('binary_side', '-')}" if m.get('binary_side') else ""
        
        with st.expander(f"📌 {m['name']} （上位: {parent_name}{side_info}）"):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(f"- **ランク:** {m['rank']} | **ステータス:** {m['status']}")
                
                new_count = st.number_input("セミナー参加回数を更新", min_value=0, value=m["seminar_count"], key=f"sem_{m['id']}")
                if new_count != m["seminar_count"]:
                    m["seminar_count"] = new_count
                    save_data(members)
                
                uploaded_file = st.file_uploader(f"{m['name']} の顔写真・スクショをアップロード", type=["jpg", "png", "jpeg"], key=f"img_{m['id']}")
                if uploaded_file:
                    img_path = os.path.join(UPLOAD_DIR, f"member_{m['id']}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    m["image"] = img_path
                    save_data(members)
                    st.success("顔写真を保存しました！組織図に反映されます。")
            
            with col_b:
                if m["image"] and os.path.exists(m["image"]):
                    st.image(m["image"], caption=f"{m['name']} の顔写真", width=120)
                else:
                    st.write("（顔写真未登録）")

# --- 3. メンバーの削除・編集 ---
elif menu == "メンバーの削除・編集":
    st.subheader("🗑️ メンバーの削除・見直し")
    members = st.session_state["members"]
    if members:
        member_names = [m["name"] for m in members]
        target_name = st.selectbox("削除するメンバーを選択", member_names)
        
        if st.button("選択したメンバーを削除する", type="primary"):
            st.session_state["members"] = [m for m in members if m["name"] != target_name]
            save_data(st.session_state["members"])
            st.success(f"メンバー「{target_name}」を削除しました！")
    else:
        st.write("登録されているメンバーはいません。")

# --- 4. 全体集計 ---
elif menu == "グループ全体集計":
    st.subheader("📊 グループ実績・教育ダッシュボード")
    members = st.session_state["members"]
    total_members = len(members)
    total_seminars = sum([m["seminar_count"] for m in members])
    left_count = len([m for m in members if m.get("binary_side") == "左"])
    right_count = len([m for m in members if m.get("binary_side") == "右"])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("総メンバー数", f"{total_members} 名")
    col2.metric("左右バランス", f"左:{left_count} / 右:{right_count}")
    col3.metric("総セミナー受講回数", f"{total_seminars} 回")
