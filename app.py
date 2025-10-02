import streamlit as st
from services import persistence
from domain.models import User
from utils.ids import create_id_with_prefix
from services.matching import compute_matches
from services.sample_data import make_users
from dataclasses import asdict
import datetime as dt

st.set_page_config(page_title="AI Club Matching Demo", layout="wide")


def load_users():
    return persistence.load_list('users')


def save_users(users):
    persistence.replace_all('users', users)


def load_clubs():
    return persistence.load_list('clubs')


def save_clubs(clubs):
    persistence.replace_all('clubs', clubs)


st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
                        "User Signup", "Matching (Admin)", "Results", "Seed Sample Users"], index=0)


if page == "User Signup":
    st.header("사용자 등록")
    name = st.text_input("이름")
    region = st.selectbox("지역", ["서울", "부산", "대전", "대구"])
    rank = st.selectbox("직급", ["사원", "주임", "대리", "과장"])
    interests = st.multiselect(
        "관심사", ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"])
    atmosphere = st.selectbox("선호 분위기", ["외향", "내향", "밸런스"])
    if st.button("저장", disabled=not (name and interests)):
        users = load_users()
        uid = create_id_with_prefix('u')
        user = User(id=uid, name=name, region=region, rank=rank,
                    interests=interests, preferred_atmosphere=atmosphere)
        users.append(asdict(user))
        save_users(users)
        st.success(f"저장 완료: {name}")
    st.divider()
    st.subheader("현재 사용자")
    users = load_users()
    if users:
        st.dataframe(users, use_container_width=True)
    else:
        st.info("아직 등록된 사용자가 없습니다.")

elif page == "Matching (Admin)":
    st.header("매칭 실행 (Admin)")
    users_raw = load_users()
    if not users_raw:
        st.warning("사용자가 없습니다.")
    else:
        st.write(f"총 사용자: {len(users_raw)}")
        target_size = st.number_input(
            "그룹 인원 (기본 5)", min_value=3, max_value=10, value=5)
        if st.button("매칭 실행"):
            # Convert to User objects
            user_objs = [User(**u) for u in users_raw]
            clubs = compute_matches(user_objs, target_size=target_size)
            clubs_dicts = [asdict(c) for c in clubs]
            save_clubs(clubs_dicts)
            st.success(f"생성된 클럽 수: {len(clubs_dicts)}")
    st.divider()
    st.subheader("매칭 이전 사용자 미리보기")
    st.dataframe(load_users(), use_container_width=True)

elif page == "Results":
    st.header("클럽 결과")
    clubs = load_clubs()
    if not clubs:
        st.info("아직 생성된 클럽이 없습니다.")
    else:
        for c in clubs:
            with st.expander(f"클럽 {c['id']} | 인원 {len(c['member_ids'])}"):
                st.write("리더:", c['leader_id'])
                st.write("멤버:", ', '.join(c['member_ids']))
                st.json(c['match_score_breakdown'])

elif page == "Seed Sample Users":
    st.header("샘플 사용자 생성")
    if st.button("15명 생성"):
        users = load_users()
        if users:
            st.warning("이미 사용자 존재. 추가만 진행.")
        new = [asdict(u) for u in make_users(15)]
        users.extend(new)
        save_users(users)
        st.success("샘플 추가 완료")
    st.dataframe(load_users(), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Data dir: data | {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}Z")
