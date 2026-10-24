import streamlit as st
from datetime import datetime
import os
import json

UPLOAD_DIR = "prime_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DATA_FILE = "prime_members_data.json"

# データの読み込み関数
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 初期データ（バイナリー構造：parent_id と binary_side を持つ）
    return [
        {"id": 1, "name": "大西 真由美", "parent_id": None, "binary_side": None, "rank": "リーダー", "status": "アクティブ", "seminar_count": 5, "image": ""},
        {"id": 2, "name": "山田 太郎", "parent_id": 1, "binary_side": "左", "rank": "リーダー", "status": "アクティブ", "seminar_count": 3, "image": ""},
        {"id": 3, "name": "佐藤 花子", "parent_id": 1, "binary_side": "右", "rank": "メンバー", "status": "アクティブ", "seminar_count": 1, "image": ""},
    ]

# データの保存関数
def save_data(members):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=4)

st.title("プライム共済 組織・教育管理アプリ")
st.write("マサキ医院長向け / 開発：石川副委員長")

# セッション状態の初期化とファイル同期
if "members" not in st.session_state:
    st.session_state["members"] = load_data()

# サイドメニュー
menu = st.sidebar.selectbox("メニュー選択", ["組織図・紹介ツリー", "新規メンバー登録", "メンバーの削除・編集", "グループ全体集計"])

# --- 1. 新規メンバー登録（バイナリー配置対応） ---
if menu == "新規メンバー登録":
    st.subheader("➕ 新規メンバーの追加・バイナリー配置")
    st.write("組織図上のどこ（誰の左右）に配置するかを指定して登録します。")
    
    members = st.session_state["members"]
    
    with st.form("member_form"):
        name = st.text_input("メンバー氏名")
        
        # 配置先の親（アップライン）を選択
        parent_options = {m["id"]: m["name"] for m in members}
        parent_options[0] = "【トップ（大西真由美など最上部）】"
        
        selected_parent_id = st.selectbox(
            "配置先の親（上位メンバー）を選択", 
            options=list(parent_options.keys()), 
            format_func=lambda x: parent_options[x]
        )
        
        # 左右の指定（トップ以外の場合）
        binary_side = st.selectbox("バイナリー配置（左右）", ["左", "右"])
        
        rank = st.selectbox("ランク・タイトル", ["メンバー", "サブリーダー", "リーダー"])
        status = st.selectbox("ステータス", ["アクティブ", "新規", "休眠"])
        seminar_count = st.number_input("セミナー参加回数", min_value=0, value=0)
        
        submitted = st.form_submit_button("メンバーを登録する")
        
        if submitted:
            if not name:
                st.warning("氏名を入力してください。")
            else:
                # トップ以外の場合、その親の同じ左右にすでにメンバーがいないかチェック
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
                    # トップ追加（通常は1人のみ想定だが一応許可）
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

# --- 2. 組織図・紹介ツリー ＆ 写真管理 ---
elif menu == "組織図・紹介ツリー":
    st.subheader("🌳 バイナリー組織図（顔写真付き）")
    st.write("ピンチイン・アウト（拡大・縮小）して全体のつながりを確認できます。")
    
    members = st.session_state["members"]
    
    # Graphviz（ツリー図・写真埋め込み対応）の構築
    dot_code = """
    digraph {
        graph [rankdir = "TB", nodesep=0.4, ranksep=0.6, bgcolor="transparent"];
        node [fontname="Meiryo", shape=box, style="rounded,filled", fillcolor="#ffffff", fontcolor="#262730", imagescale=true, width=1.1, height=1.3, labelloc="b", margin=0.1];
        edge [color="#666666", fontsize=10];
    """
    
    for m in members:
        label = f"{m['name']}\\n({m['rank']})"
        
        # 写真が登録されている場合はノードに埋め込む
        if m["image"] and os.path.exists(m["image"]):
            # Graphvizのimage属性を使用
            dot_code += f'    "{m["id"]}" [label="{label}", image="{m["image"]}", shape=box, style="filled", fillcolor="#f9f9f9"];\n'
        else:
            dot_code += f'    "{m["id"]}" [label="{label}", shape=box, style="rounded,filled", fillcolor="#f0f2f6"];\n'
        
        # 親子関係のエッジ（左右のラベル付き）
        if m.get("parent_id") is not None:
            side = m.get("binary_side", "")
            dot_code += f'    "{m["parent_id"]}" -> "{m["id"]}" [label="{side}"];\n'
                
    dot_code += "}"
    
    # ツリー図を描画
    st.graphviz_chart(dot_code)

    st.markdown("---")
    st.subheader("📋 メンバー詳細 ＆ 写真・セミナー回数管理")
    st.write("各メンバーを展開すると、顔写真のアップロードや情報の変更ができます。")
    
    for m in members:
        # 親の名前を取得
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
                
                # セミナー回数の即時更新
                new_count = st.number_input("セミナー参加回数を更新", min_value=0, value=m["seminar_count"], key=f"sem_{m['id']}")
                if new_count != m["seminar_count"]:
                    m["seminar_count"] = new_count
                    save_data(members)
                
                # 写真のアップロード機能
                uploaded_file = st.file_uploader(f"{m['name']} の顔写真・スクショをアップロード", type=["jpg", "png", "jpeg"], key=f"img_{m['id']}")
                if uploaded_file:
                    img_path = os.path.join(UPLOAD_DIR, f"member_{m['id']}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    m["image"] = img_path
                    save_data(members)
                    st.success("顔写真を保存しました！組織図に反映されます。")
            
            with col_b:
                # アップロード済み画像の表示
                if m["image"] and os.path.exists(m["image"]):
                    st.image(m["image"], caption=f"{m['name']} の顔写真", width=120)
                else:
                    st.write("（顔写真未登録）")

# --- 3. メンバーの削除・編集 ---
elif menu == "メンバーの削除・編集":
    st.subheader("🗑️ メンバーの削除・見直し")
    st.write("不要になったメンバーや登録間違いの修正はここから行えます。")
    
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
