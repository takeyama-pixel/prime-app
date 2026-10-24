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

# --- 2. 組織図・紹介ツリー（HTMLコンポーネントによる確実な表示） ---
elif menu == "組織図・紹介ツリー":
    st.subheader("🌳 バイナリー組織図（顔写真付き・左右2系列）")
    st.write("トップを起点に、左系列と右系列が左右に分かれるツリー構造です。")
    
    members = st.session_state["members"]
    
    def make_card(m, side_label=""):
        if not m:
            return '<div style="width: 110px; height: 85px; border: 2px dashed #ccc; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 11px; background: #fafafa; margin: 0 auto;">（未配置）</div>'
            
        img_b64 = get_image_base64(m.get("image", ""))
        if img_b64:
            img_tag = f'<img src="{img_b64}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #4CAF50; margin-bottom:2px;">'
        else:
            img_tag = '<div style="width:45px; height:45px; border-radius:50%; background:#e0e0e0; display:flex; align-items:center; justify-content:center; margin:0 auto 2px auto; font-size:9px; color:#666;">写真なし</div>'
        
        badge_bg = "#e3f2fd" if side_label == "左" else "#fbe9e7"
        badge_color = "#1565c0" if side_label == "左" else "#d84315"
        badge = f'<div style="background:{badge_bg}; color:{badge_color}; padding:1px 4px; border-radius:3px; font-size:9px; display:inline-block; margin-top:1px; font-weight:bold;">{side_label}系列</div>' if side_label else ''
        
        return f"""
        <div style="border: 2px solid #d0d0d0; border-radius: 10px; padding: 5px; text-align: center; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.08); width: 120px; margin: 0 auto;">
            {img_tag}
            <div style="font-weight: bold; font-size: 12px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{m['name']}</div>
            <div style="font-size: 9px; color: #666;">{m['rank']} (参:{m['seminar_count']}回)</div>
            {badge}
        </div>
        """

    roots = [m for m in members if m.get("parent_id") is None]
    
    for root in roots:
        top_html = make_card(root)
        
        left_child = next((m for m in members if m.get("parent_id") == root["id"] and m.get("binary_side") == "左"), None)
        right_child = next((m for m in members if m.get("parent_id") == root["id"] and m.get("binary_side") == "右"), None)
        
        left_html = make_card(left_child, "左")
        right_html = make_card(right_child, "右")
        
        sub_l_l = next((m for m in members if left_child and m.get("parent_id") == left_child["id"] and m.get("binary_side") == "左"), None)
        sub_l_r = next((m for m in members if left_child and m.get("parent_id") == left_child["id"] and m.get("binary_side") == "右"), None)
        sub_r_l = next((m for m in members if right_child and m.get("parent_id") == right_child["id"] and m.get("binary_side") == "左"), None)
        sub_r_r = next((m for m in members if right_child and m.get("parent_id") == right_child["id"] and m.get("binary_side") == "右"), None)
        
        sub_l_l_html = make_card(sub_l_l, "左")
        sub_l_r_html = make_card(sub_l_r, "右")
        sub_r_l_html = make_card(sub_r_l, "左")
        sub_r_r_html = make_card(sub_r_r, "右")

        # 完全なHTMLとしてコンポーネント化（文字漏れを完全に防止）
        tree_html = f"""
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Meiryo, sans-serif;
                background-color: transparent;
                margin: 0;
                padding: 10px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .node-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 100%;
            }}
            .branch-line-v {{
                width: 2px;
                height: 15px;
                background-color: #999;
            }}
            .branch-line-h {{
                width: 200px;
                height: 2px;
                background-color: #999;
            }}
            .row {{
                display: flex;
                justify-content: space-around;
                width: 100%;
                max-width: 320px;
            }}
            .col {{
                flex: 1;
                text-align: center;
                padding: 0 4px;
            }}
        </style>
        </head>
        <body>
            <div class="node-container">
                <div style="margin-bottom: 4px; color: #555; font-size: 11px; font-weight: bold;">👑 トップ</div>
                <div style="margin-bottom: 10px;">{top_html}</div>
                
                <div class="branch-line-v"></div>
                <div class="branch-line-h" style="margin-bottom: 10px;"></div>
                
                <div class="row" style="margin-bottom: 10px;">
                    <div class="col">{left_html}</div>
                    <div class="col">{right_html}</div>
                </div>
                
                <div class="row" style="margin-bottom: 5px;">
                    <div class="col"><div style="margin: 0 auto; width: 2px; height: 12px; background: #999;"></div></div>
                    <div class="col"><div style="margin: 0 auto; width: 2px; height: 12px; background: #999;"></div></div>
                </div>
                
                <div class="row">
                    <div class="col" style="display: flex; justify-content: space-around;">
                        <div style="transform: scale(0.85);">{sub_l_l_html}</div>
                        <div style="transform: scale(0.85);">{sub_l_r_html}</div>
                    </div>
                    <div class="col" style="display: flex; justify-content: space-around;">
                        <div style="transform: scale(0.85);">{sub_r_l_html}</div>
                        <div style="transform: scale(0.85);">{sub_r_r_html}</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Streamlitのコンポーネントとして安全に出力（文字漏れしない）
        components.html(tree_html, height=340, scrolling=True)

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
            save_data(members)
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
