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
                    # 既存データに新項目がない場合の互換性対応
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
st.write("マサキ医院長向け / 開発：石川副委員長")

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
        
        # 追加項目
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

# --- 2. 組織図・紹介ツリー（全体俯瞰・注目リーダー拡大モード対応） ---
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

    full_html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Meiryo, sans-serif;
            background-color: transparent;
            margin: 0;
            padding: {pad_val};
            display: inline-block;
            min-width: 100%;
            box-sizing: border-box;
        }}
        .tree-container {{
            display: flex;
            justify-content: center;
            width: max-content;
            margin: 0 auto;
        }}
        .tree ul {{
            padding-top: 20px; 
            position: relative;
            transition: all 0.5s;
            display: flex;
            justify-content: center;
            list-style-type: none;
            margin: 0;
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
    </style>
    </head>
    <body>
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
    
    components.html(full_html, height=560, scrolling=True)

    st.markdown("---")
    st.subheader("📋 メンバー詳細 ＆ 写真・セミナー回数管理")
    st.write("各メンバーを展開すると、紹介者・備考の確認や顔写真のアップロードができます。")
    
    for m in members:
        parent_name = "トップ"
        if m.get("parent_id") is not None:
            p_obj = next((item for item in members if item["id"] == m["parent_id"]), None)
            if p_obj:
                parent_name = p_obj["name"]
                
        side_info = f" / 位置: {m.get('binary_side', '-')}" if m.get('binary_side') else ""
        
        with st.expander(f"📌 {m['name']} （上位: {parent_name}{side_info}）"):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(f"- **ランク:** {m['rank']} | **ステータス:** {m['status']}")
                st.write(f"- **紹介者:** {m.get('introducer', '（未設定）')}")
                st.write(f"- **備考:** {m.get('remarks', '（なし）')}")
                
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

# --- 3. メンバーの編集・削除 ---
elif menu == "メンバーの編集・削除":
    st.subheader("✏️ メンバー情報の編集・削除")
    members = st.session_state["members"]
    if members:
        target_name = st.selectbox("編集・削除するメンバーを選択", [m["name"] for m in members])
        target_member = next((m for m in members if m["name"] == target_name), None)
        
        if target_member:
            with st.form("edit_form"):
                st.write(f"**【{target_member['name']}】の情報を編集**")
                new_name = st.text_input("氏名", value=target_member["name"])
                
                parent_options = {m["id"]: f"{m['name']} ({m['rank']})" for m in members if m["id"] != target_member["id"]}
                parent_options[0] = "【トップ（最上部）】"
                
                current_p_id = target_member.get("parent_id")
                if current_p_id is None:
                    current_p_index = list(parent_options.keys()).index(0)
                else:
                    current_p_index = list(parent_options.keys()).index(current_p_id) if current_p_id in parent_options else 0
                
                selected_parent_id = st.selectbox(
                    "配置先の親（上位メンバー）を選択", 
                    options=list(parent_options.keys()), 
                    index=current_p_index,
                    format_func=lambda x: parent_options[x]
                )
                
                binary_side_options = ["左", "右"]
                current_side = target_member.get("binary_side", "左")
                side_index = binary_side_options.index(current_side) if current_side in binary_side_options else 0
                new_side = st.selectbox("バイナリー配置（左右）", binary_side_options, index=side_index)
                
                ranks = ["メンバー", "サブリーダー", "リーダー"]
                rank_index = ranks.index(target_member["rank"]) if target_member["rank"] in ranks else 0
                new_rank = st.selectbox("ランク・タイトル", ranks, index=rank_index)
                
                statuses = ["アクティブ", "新規", "休眠"]
                status_index = statuses.index(target_member["status"]) if target_member["status"] in statuses else 0
                new_status = st.selectbox("ステータス", statuses, index=status_index)
                
                # 追加項目の編集
                new_introducer = st.text_input("紹介者", value=target_member.get("introducer", ""))
                new_remarks = st.text_area("備考欄・メモ書き", value=target_member.get("remarks", ""))
                
                update_submitted = st.form_submit_button("変更を保存する")
                
                if update_submitted:
                    target_member["name"] = new_name
                    target_member["parent_id"] = None if selected_parent_id == 0 else selected_parent_id
                    target_member["binary_side"] = None if selected_parent_id == 0 else new_side
                    target_member["rank"] = new_rank
                    target_member["status"] = new_status
                    target_member["introducer"] = new_introducer
                    target_member["remarks"] = new_remarks
                    save_data(members)
                    st.success(f"メンバー「{new_name}」の情報を更新しました！")
            
            st.markdown("---")
            if st.button("⚠️ このメンバーを削除する", type="primary"):
                st.session_state["members"] = [m for m in members if m["id"] != target_member["id"]]
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
