import streamlit as st
from datetime import datetime
import os
import json
import base64

UPLOAD_DIR = "prime_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DATA_FILE = "prime_members_data.json"

# 画像をBase64エンコードしてHTML表示する関数
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

# データの読み込み関数（綺麗なバイナリーツリー初期構造を設定）
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and "parent_id" in data[0]:
                    return data
        except Exception:
            pass
            
    # マサキ医院長のイメージに近づけた初期バイナリーツリーデータ
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

# --- 2. 組織図・紹介ツリー（左右2系列のバイナリーカード表示） ---
elif menu == "組織図・紹介ツリー":
    st.subheader("🌳 バイナリー組織図（顔写真付き・左右2系列）")
    st.write("トップを起点に、左系列と右系列に分かれたツリー構造を表示しています。")
    
    members = st.session_state["members"]
    
    # メンバーカードを描画する関数
    def render_card(m, side_label=""):
        img_b64 = get_image_base64(m.get("image", ""))
        if img_b64:
            img_tag = f'<img src="{img_b64}" style="width:55px; height:55px; border-radius:50%; object-fit:cover; border:2px solid #4CAF50; margin-bottom:4px;">'
        else:
            img_tag = '<div style="width:55px; height:55px; border-radius:50%; background:#e0e0e0; display:flex; align-items:center; justify-content:center; margin:0 auto 4px auto; font-size:9px; color:#666;">写真なし</div>'
        
        badge = f'<div style="background:#e0f7fa; color:#00796b; padding:1px 4px; border-radius:3px; font-size:10px; display:inline-block; margin-top:2px;">{side_label}</div>' if side_label else ''
        
        return f"""
        <div style="border: 2px solid #d0d0d0; border-radius: 10px; padding: 8px; text-align: center; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.08); width: 130px; margin: 0 auto;">
            {img_tag}
            <div style="font-weight: bold; font-size: 13px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{m['name']}</div>
            <div style="font-size: 10px; color: #666;">{m['rank']} (参:{m['seminar_count']}回)</div>
            {badge}
        </div>
        """

    roots = [m for m in members if m.get("parent_id") is None]
    
    for root in roots:
        # トップ階層
        st.markdown(f"<div style='text-align: center; font-weight: bold; color: #555; margin-bottom: 5px;'>👑 トップ</div>", unsafe_allow_html=True)
        st.markdown(render_card(root), unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 20px; color: #888; margin: 5px 0;'>│</div>", unsafe_allow_html=True)
        
        # 左右の枝分かれ（バイナリー2系列）を表示
        left_child = next((m for m in members if m.get("parent_id") == root["id"] and m.get("binary_side") == "左"), None)
        right_child = next((m for m in members if m.get("parent_id") == root["id"] and m.get("binary_side") == "右"), None)
        
        col_L, col_R = st.columns(2)
        
        with col_L:
            st.markdown("<div style='text-align: center; color: #1976D2; font-weight: bold; font-size: 12px;'>◀ 左系列</div>", unsafe_allow_html=True)
            if left_child:
                st.markdown(render_card(left_child, "左"), unsafe_allow_html=True)
                
                # さらにその下の階層（例：左側のさらに左右）
                sub_left = next((m for m in members if m.get("parent_id") == left_child["id"] and m.get("binary_side") == "左"), None)
                sub_right = next((m for m in members if m.get("parent_id") == left_child["id"] and m.get("binary_side") == "右"), None)
                if sub_left or sub_right:
                    st.markdown("<div style='text-align: center; color: #aaa; font-size: 14px;'>│</div>", unsafe_allow_html=True)
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        if sub_left: st.markdown(render_card(sub_left, "左"), unsafe_allow_html=True)
                    with sub_col2:
                        if sub_right: st.markdown(render_card(sub_right, "右"), unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: center; color: #aaa; font-size: 11px; padding: 10px;'>（未配置）</div>", unsafe_allow_html=True)
                
        with col_R:
            st.markdown("<div style='text-align: center; color: #E64A19; font-weight: bold; font-size: 12px;'>右系列 ▶</div>", unsafe_allow_html=True)
            if right_child:
                st.markdown(render_card(right_child, "右"), unsafe_allow_html=True)
                
                # さらにその下の階層（例：右側のさらに左右）
                sub_left = next((m for m in members if m.get("parent_id") == right_child["id"] and m.get("binary_side") == "左"), None)
                sub_right = next((m for m in members if m.get("parent_id") == right_child["id"] and m.get("binary_side") == "右"), None)
                if sub_left or sub_right:
                    st.markdown("<div style='text-align: center; color: #aaa; font-size: 14px;'>│</div>", unsafe_allow_html=True)
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        if sub_left: st.markdown(render_card(sub_left, "左"), unsafe_allow_html=True)
                    with sub_col2:
                        if sub_right: st.markdown(render_card(sub_right, "右"), unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: center; color: #aaa; font-size: 11px; padding: 10px;'>（未配置）</div>", unsafe_allow_html=True)

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
