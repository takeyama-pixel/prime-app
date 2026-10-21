import streamlit as st
from datetime import datetime
import os

UPLOAD_DIR = "prime_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("プライム共済 組織・教育管理アプリ（把握用）")
st.write("マサキ医院長向け / 開発：石川副委員長")

# サイドメニュー
menu = st.sidebar.selectbox("メニュー選択", ["組織図・紹介ツリー", "新規メンバー登録", "メンバーの削除・編集", "グループ全体集計"])

# セッション状態の初期化（初期データ）
if "members" not in st.session_state:
    st.session_state["members"] = [
        {"id": 1, "name": "山田 太郎", "upline": "マサキ（自分）", "binary_pos": "左（Left）", "rank": "リーダー", "status": "アクティブ", "seminar_count": 3, "image": ""},
        {"id": 2, "name": "佐藤 花子", "upline": "山田 太郎", "binary_pos": "右（Right）", "rank": "メンバー", "status": "アクティブ", "seminar_count": 1, "image": ""},
        {"id": 3, "name": "鈴木 一郎", "upline": "マサキ（自分）", "binary_pos": "右（Right）", "rank": "サブリーダー", "status": "休眠", "seminar_count": 0, "image": ""},
    ]

# --- 1. 新規メンバー登録（写真アップ対応） ---
if menu == "新規メンバー登録":
    st.subheader("➕ 新規メンバーの追加・登録")
    
    with st.form("member_form"):
        name = st.text_input("メンバー氏名")
        
        # 紹介者（ユニレベル・アップ）の候補
        upline_list = ["マサキ（自分）"] + [m["name"] for m in st.session_state["members"]]
        upline = st.selectbox("紹介者（ユニレベル・アップ）", upline_list)
        
        # バイナリーの配置
        binary_pos = st.selectbox("バイナリー配置", ["左（Left）", "右（Right）"])
        
        rank = st.selectbox("ランク・タイトル", ["メンバー", "サブリーダー", "リーダー"])
        status = st.selectbox("ステータス", ["アクティブ", "新規", "休眠"])
        seminar_count = st.number_input("セミナー参加回数", min_value=0, value=0)
        
        submitted = st.form_submit_button("メンバーを登録する")
        
        if submitted:
            if name:
                new_id = max([m["id"] for m in st.session_state["members"]], default=0) + 1
                st.session_state["members"].append({
                    "id": new_id,
                    "name": name,
                    "upline": upline,
                    "binary_pos": binary_pos,
                    "rank": rank,
                    "status": status,
                    "seminar_count": seminar_count,
                    "image": ""
                })
                st.success(f"メンバー「{name}」を追加しました！")
            else:
                st.warning("氏名を入力してください。")

# --- 2. 組織図・紹介ツリー ＆ 写真管理 ---
elif menu == "組織図・紹介ツリー":
    st.subheader("🌳 組織図（バイナリー ＆ ユニレベル紹介系列）")
    
    # バイナリーの左右表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔵 バイナリー：左系列 (Left)")
        left_members = [m for m in st.session_state["members"] if m["binary_pos"] == "左（Left）"]
        if left_members:
            for m in left_members:
                st.info(f"**{m['name']}** \n\n (紹介者: {m['upline']} / ランク: {m['rank']} / 参加: {m['seminar_count']}回)")
        else:
            st.write("（まだ登録されていません）")
            
    with col2:
        st.markdown("### 🔴 バイナリー：右系列 (Right)")
        right_members = [m for m in st.session_state["members"] if m["binary_pos"] == "右（Right）"]
        if right_members:
            for m in right_members:
                st.warning(f"**{m['name']}** \n\n (紹介者: {m['upline']} / ランク: {m['rank']} / 参加: {m['seminar_count']}回)")
        else:
            st.write("（まだ登録されていません）")

    st.markdown("---")
    st.subheader("📋 紹介系列（ユニレベル）ツリー・詳細 ＆ 写真管理")
    st.write("各メンバーを展開すると、紹介のつながりの確認や、写真のアップロードができます。")
    
    for m in st.session_state["members"]:
        with st.expander(f"📌 {m['name']} （紹介者: {m['upline']} / 位置: {m['binary_pos']}）"):
            st.write(f"- **ランク:** {m['rank']} | **ステータス:** {m['status']}")
            
            # セミナー回数の即時更新
            new_count = st.number_input("セミナー参加回数を更新", min_value=0, value=m["seminar_count"], key=f"sem_{m['id']}")
            m["seminar_count"] = new_count
            
            # 写真のアップロード機能
            uploaded_file = st.file_uploader(f"{m['name']} の関連写真・スクショをアップロード", type=["jpg", "png", "jpeg"], key=f"img_{m['id']}")
            if uploaded_file:
                img_path = os.path.join(UPLOAD_DIR, f"member_{m['id']}.jpg")
                with open(img_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                m["image"] = img_path
                st.success("写真を保存しました！")
                
            # アップロード済み画像の表示
            if m["image"] and os.path.exists(m["image"]):
                st.image(m["image"], caption=f"{m['name']} の登録写真", width=200)

# --- 3. メンバーの削除・編集 ---
elif menu == "メンバーの削除・編集":
    st.subheader("🗑️ メンバーの削除・見直し")
    st.write("不要になったメンバーや、登録間違いがあった場合はここから簡単に削除できます。")
    
    if st.session_state["members"]:
        member_names = [m["name"] for m in st.session_state["members"]]
        target_name = st.selectbox("削除するメンバーを選択", member_names)
        
        if st.button("選択したメンバーを削除する", type="primary"):
            st.session_state["members"] = [m for m in st.session_state["members"] if m["name"] != target_name]
            st.success(f"メンバー「{target_name}」を削除しました！メニューを切り替えてご確認ください。")
    else:
        st.write("登録されているメンバーはいません。")

# --- 4. 全体集計 ---
elif menu == "グループ全体集計":
    st.subheader("📊 グループ実績・教育ダッシュボード")
    
    total_members = len(st.session_state["members"])
    total_seminars = sum([m["seminar_count"] for m in st.session_state["members"]])
    left_count = len([m for m in st.session_state["members"] if m["binary_pos"] == "左（Left）"])
    right_count = len([m for m in st.session_state["members"] if m["binary_pos"] == "右（Right）"])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("総メンバー数", f"{total_members} 名")
    col2.metric("左右バランス", f"左:{left_count} / 右:{right_count}")
    col3.metric("総セミナー受講回数", f"{total_seminars} 回")