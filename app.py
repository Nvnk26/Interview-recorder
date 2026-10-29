from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer


# This class has the same name and compatible structure as the DataCleaner
# defined in the training notebook. It must exist before loading the joblib file.
class DataCleaner(BaseEstimator, TransformerMixin):
    def __init__(self, cols_to_clip=None, lower_quantile=0.001, upper_quantile=0.99):
        self.cols_to_clip = ["BMI"] if cols_to_clip is None else cols_to_clip
        self.lower_quantile = lower_quantile
        self.upper_quantile = upper_quantile
        self.clip_bounds_ = {}
        self.imputer_ = SimpleImputer(strategy="median")
        self.feature_names_ = None

    def fit(self, X, y=None):
        X_df = X.copy()
        self.feature_names_ = X_df.columns.tolist()
        for col in self.cols_to_clip:
            if col in X_df.columns:
                self.clip_bounds_[col] = (
                    X_df[col].quantile(self.lower_quantile),
                    X_df[col].quantile(self.upper_quantile),
                )
        self.imputer_.fit(X_df)
        return self

    def transform(self, X):
        X_df = X.copy()
        X_imputed = pd.DataFrame(
            self.imputer_.transform(X_df),
            columns=self.feature_names_,
            index=X_df.index,
        )
        for col, (q_low, q_high) in self.clip_bounds_.items():
            X_imputed[col] = X_imputed[col].clip(lower=q_low, upper=q_high)
        return X_imputed


st.set_page_config(
    page_title="Dự đoán nguy cơ tiểu đường",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
        .block-container {max-width: 1050px; padding-top: 2.5rem; padding-bottom: 3rem;}
        .main-title {
            font-family: Arial, "Segoe UI", sans-serif;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.8;
            margin: 0 0 0.8rem 0;
            padding: 0.2rem 0 0.25rem 0;
            overflow: visible;
        }
        .stage-title {
            font-family: Arial, "Segoe UI", sans-serif;
            font-size: 1.5rem;
            font-weight: 600;
            line-height: 1.5;
            margin: 1.2rem 0 0.8rem 0;
            padding: 0.1rem 0 0.15rem 0;
        }
        .subtle-text {color: #475569; font-size: 0.95rem;}
        div.stButton > button {min-height: 2.75rem; font-weight: 600;}
        div[data-testid="stNumberInput"] input {font-variant-numeric: tabular-nums;}
        a[data-testid="stHeaderAction"],
        a.header-anchor-link,
        [data-testid="stHeaderActionElements"],
        [data-testid="stHeadingWithActionElements"],
        .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a,
        .stMarkdown h4 a, .stMarkdown h5 a, .stMarkdown h6 a {
            display: none !important;
            visibility: hidden !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

MODEL_PATH = Path(__file__).with_name("diabetes_model_bundle.joblib")

if not MODEL_PATH.exists():
    st.markdown('<div class="main-title">Dự đoán nguy cơ tiểu đường</div>', unsafe_allow_html=True)
    st.write("Chưa tìm thấy tệp `diabetes_model_bundle.joblib`.")
    st.write(
        "Hãy mở notebook huấn luyện, chạy toàn bộ các ô đến hết phần đánh giá mô hình, "
        "sau đó chạy đoạn mã trong tệp `export_model_cell.txt`. Đặt tệp được xuất vào "
        "cùng thư mục với `app.py` rồi chạy lại Streamlit."
    )
    st.stop()

try:
    bundle = joblib.load(MODEL_PATH)
except Exception as exc:
    st.markdown('<div class="main-title">Không thể tải mô hình</div>', unsafe_allow_html=True)
    st.write(
        "Có thể phiên bản scikit-learn dùng khi xuất mô hình khác với phiên bản đang cài. "
        "Hãy xem các phiên bản được in ra khi chạy ô xuất mô hình và cài cùng phiên bản đó."
    )
    st.code(str(exc))
    st.stop()

model = bundle["model"]
threshold = float(bundle["threshold"])
cleaner = bundle["cleaner"]
preprocessor = bundle["preprocessor"]
selected_features = bundle["selected_features"]
scale_cols = bundle["scale_cols"]
binary_cols = bundle["binary_cols"]
feature_cols = bundle["feature_cols"]
all_cols_ordered = scale_cols + binary_cols


# The feature-engineering rules below mirror the notebook's add_engineered_features().
def add_engineered_features(data: pd.DataFrame) -> pd.DataFrame:
    df2 = data.copy()

    df2["BMI_cat"] = pd.cut(
        df2["BMI"],
        bins=[0, 18.5, 25, 30, 35, 200],
        labels=False,
        include_lowest=True,
    ).astype(float)
    bmi_label_map = {0: "Gầy", 1: "Bình thường", 2: "Thừa cân", 3: "Béo I", 4: "Béo II+"}
    df2["BMI_cat_name"] = df2["BMI_cat"].map(bmi_label_map)

    df2["BMI_x_GenHlth"] = df2["BMI"] * df2["GenHlth"]

    df2["AgeGroup"] = pd.cut(
        df2["Age"], bins=[0, 3, 7, 10, 13], labels=False, include_lowest=True
    ).astype(float)
    df2["AgeGroup_name"] = df2["AgeGroup"].map(
        {0: "18-34", 1: "35-54", 2: "55-69", 3: "70+"}
    )

    lifestyle = df2[
        ["PhysActivity", "Fruits", "Veggies", "Smoker", "HvyAlcoholConsump"]
    ].copy()
    lifestyle[["Smoker", "HvyAlcoholConsump"]] *= -1
    df2["LifestyleScore"] = lifestyle.sum(axis=1, min_count=5)
    df2["LifestyleLevel"] = pd.cut(
        df2["LifestyleScore"], bins=[-3, 0, 1, 4], labels=False, include_lowest=True
    ).astype(float)

    health_parts = pd.DataFrame(
        {
            "mental": (df2["MentHlth"] > 14).where(df2["MentHlth"].notna()),
            "physical": (df2["PhysHlth"] > 14).where(df2["PhysHlth"].notna()),
            "walk": df2["DiffWalk"],
            "stroke": df2["Stroke"],
            "heart": df2["HeartDiseaseorAttack"],
        }
    )
    df2["HealthBurden"] = health_parts.astype(float).sum(axis=1, min_count=5)

    obesity = (df2["BMI"] > 29.99).astype(float)
    obesity = obesity.where(df2["BMI"].notna())
    metabolic = pd.concat(
        [df2[["HighBP", "HighChol"]], obesity.rename("obesity")], axis=1
    )
    df2["MetabolicRisk"] = metabolic.sum(axis=1, min_count=3)
    return df2


def apply_feature_pipeline(input_values: dict) -> pd.DataFrame:
    raw = pd.DataFrame([input_values], columns=feature_cols)
    cleaned = cleaner.transform(raw)
    engineered = add_engineered_features(cleaned).drop(
        columns=["BMI_cat_name", "AgeGroup_name"]
    )
    transformed = preprocessor.transform(engineered)
    transformed_df = pd.DataFrame(transformed, columns=all_cols_ordered)
    return transformed_df[selected_features]


GENERAL_HEALTH = {
    "Xuất sắc": 1,
    "Rất tốt": 2,
    "Tốt": 3,
    "Bình thường": 4,
    "Kém": 5,
}

AGE_GROUPS = {
    "18–24 tuổi": 1,
    "25–29 tuổi": 2,
    "30–34 tuổi": 3,
    "35–39 tuổi": 4,
    "40–44 tuổi": 5,
    "45–49 tuổi": 6,
    "50–54 tuổi": 7,
    "55–59 tuổi": 8,
    "60–64 tuổi": 9,
    "65–69 tuổi": 10,
    "70–74 tuổi": 11,
    "75–79 tuổi": 12,
    "Từ 80 tuổi trở lên": 13,
}

EDUCATION_LEVELS = {
    "Chưa đi học hoặc chỉ học mẫu giáo": 1,
    "Lớp 1–8": 2,
    "Lớp 9–11": 3,
    "Tốt nghiệp THPT hoặc tương đương": 4,
    "Cao đẳng/đại học 1–3 năm": 5,
    "Tốt nghiệp đại học từ 4 năm trở lên": 6,
}

INCOME_LEVELS = {
    "Dưới 10.000 USD/năm": 1,
    "Từ 10.000 đến dưới 15.000 USD/năm": 2,
    "Từ 15.000 đến dưới 20.000 USD/năm": 3,
    "Từ 20.000 đến dưới 25.000 USD/năm": 4,
    "Từ 25.000 đến dưới 35.000 USD/năm": 5,
    "Từ 35.000 đến dưới 50.000 USD/năm": 6,
    "Từ 50.000 đến dưới 75.000 USD/năm": 7,
    "Từ 75.000 USD/năm trở lên": 8,
}

BINARY_QUESTIONS = [
    ("HighBP", "Bạn từng được nhân viên y tế thông báo rằng bạn bị cao huyết áp?"),
    ("HighChol", "Bạn từng được thông báo rằng mình có cholesterol cao?"),
    ("CholCheck", "Bạn đã kiểm tra cholesterol trong vòng 5 năm qua?"),
    ("Smoker", "Bạn đã hút ít nhất 100 điếu thuốc trong suốt cuộc đời?"),
    ("Stroke", "Bạn từng bị đột quỵ?"),
    (
        "HeartDiseaseorAttack",
        "Bạn từng bị bệnh tim mạch vành, đau thắt ngực hoặc nhồi máu cơ tim?",
    ),
    (
        "PhysActivity",
        "Trong 30 ngày qua, bạn có vận động ngoài công việc thường ngày không?",
    ),
    ("Fruits", "Bạn ăn trái cây ít nhất một lần mỗi ngày?"),
    ("Veggies", "Bạn ăn rau ít nhất một lần mỗi ngày?"),
    (
        "HvyAlcoholConsump",
        "Bạn thuộc nhóm tiêu thụ rượu bia ở mức cao theo định nghĩa khảo sát?",
    ),
    ("AnyHealthcare", "Bạn có bảo hiểm hoặc hình thức chi trả chăm sóc sức khỏe?"),
    (
        "NoDocbcCost",
        "Trong 12 tháng qua, bạn từng không thể đi khám vì chi phí?",
    ),
    ("DiffWalk", "Bạn gặp khó khăn nghiêm trọng khi đi bộ hoặc leo cầu thang?"),
]


# Keep every answer between stages when the user navigates back and forth.
STATE_DEFAULTS = {
    "stage": 1,
    "height_cm": 170.0,
    "weight_kg": 70.0,
    "MentHlth": 0,
    "PhysHlth": 0,
    "ui_GenHlth": "Tốt",
    "ui_Age": "35–39 tuổi",
    "ui_Education": "Tốt nghiệp THPT hoặc tương đương",
    "ui_Income": "Từ 25.000 đến dưới 35.000 USD/năm",
    "ui_Sex": "Nữ",
}
for state_key, default_value in STATE_DEFAULTS.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value
for field, _ in BINARY_QUESTIONS:
    if f"ui_{field}" not in st.session_state:
        st.session_state[f"ui_{field}"] = "Không"


st.markdown('<div class="main-title">Dự đoán nguy cơ tiểu đường</div>', unsafe_allow_html=True)
if st.session_state.stage == 1:
    st.markdown('<div class="stage-title">Chặng 1/3</div>', unsafe_allow_html=True)
    st.write("Nhập chiều cao và cân nặng; BMI sẽ được tính tự động.")

    height_col, weight_col = st.columns(2)
    with height_col:
        st.session_state.height_cm = st.number_input(
            "Chiều cao (cm)",
            min_value=100.0,
            max_value=230.0,
            step=1.0,
            value=float(st.session_state.height_cm),
        )
    with weight_col:
        st.session_state.weight_kg = st.number_input(
            "Cân nặng (kg)",
            min_value=25.0,
            max_value=300.0,
            step=1.0,
            value=float(st.session_state.weight_kg),
        )

    bmi_value = st.session_state.weight_kg / ((st.session_state.height_cm / 100.0) ** 2)
    st.markdown(f"**BMI được tính tự động: {bmi_value:.1f}**")

    mental_col, physical_col = st.columns(2)
    with mental_col:
        st.session_state.MentHlth = st.number_input(
            "Trong 30 ngày qua, có bao nhiêu ngày sức khỏe tinh thần không tốt?",
            min_value=0,
            max_value=30,
            step=1,
            value=int(st.session_state.MentHlth),
        )
    with physical_col:
        st.session_state.PhysHlth = st.number_input(
            "Trong 30 ngày qua, có bao nhiêu ngày sức khỏe thể chất không tốt?",
            min_value=0,
            max_value=30,
            step=1,
            value=int(st.session_state.PhysHlth),
        )

    st.write("")
    if st.button("Tiếp tục", type="primary", use_container_width=True, key="to_stage_2"):
        st.session_state.stage = 2
        st.rerun()

elif st.session_state.stage == 2:
    st.markdown('<div class="stage-title">Chặng 2/3</div>', unsafe_allow_html=True)
    st.write("Chọn phương án phù hợp nhất với thông tin của bạn.")

    left_col, right_col = st.columns(2)
    with left_col:
        gen_hlth_opts = list(GENERAL_HEALTH.keys())
        st.session_state.ui_GenHlth = st.selectbox(
            "Bạn tự đánh giá sức khỏe tổng quát của mình như thế nào?",
            gen_hlth_opts,
            index=gen_hlth_opts.index(st.session_state.ui_GenHlth),
        )
        age_opts = list(AGE_GROUPS.keys())
        st.session_state.ui_Age = st.selectbox(
            "Nhóm tuổi",
            age_opts,
            index=age_opts.index(st.session_state.ui_Age),
        )
    with right_col:
        edu_opts = list(EDUCATION_LEVELS.keys())
        st.session_state.ui_Education = st.selectbox(
            "Trình độ học vấn cao nhất",
            edu_opts,
            index=edu_opts.index(st.session_state.ui_Education),
        )
        inc_opts = list(INCOME_LEVELS.keys())
        st.session_state.ui_Income = st.selectbox(
            "Mức thu nhập hằng năm",
            inc_opts,
            index=inc_opts.index(st.session_state.ui_Income),
        )

    st.write("")
    back_col, next_col = st.columns(2)
    with back_col:
        if st.button("Quay lại", use_container_width=True, key="back_to_stage_1"):
            st.session_state.stage = 1
            st.rerun()
    with next_col:
        if st.button("Tiếp tục", type="primary", use_container_width=True, key="to_stage_3"):
            st.session_state.stage = 3
            st.rerun()

elif st.session_state.stage == 3:
    st.markdown('<div class="stage-title">Chặng 3/3</div>', unsafe_allow_html=True)

    left_col, right_col = st.columns(2)
    questions_with_sex = BINARY_QUESTIONS + [("Sex", "Giới tính")]
    for i, (field, question) in enumerate(questions_with_sex):
        target_col = left_col if i % 2 == 0 else right_col
        with target_col:
            if field == "Sex":
                st.session_state.ui_Sex = st.radio(
                    question,
                    options=["Nữ", "Nam"],
                    horizontal=True,
                    index=["Nữ", "Nam"].index(st.session_state.ui_Sex),
                )
            else:
                key_name = f"ui_{field}"
                st.session_state[key_name] = st.radio(
                    question,
                    options=["Không", "Có"],
                    horizontal=True,
                    index=["Không", "Có"].index(st.session_state[key_name]),
                )
    st.write("")
    back_col, predict_col = st.columns(2)
    with back_col:
        if st.button("Quay lại", use_container_width=True, key="back_to_stage_2"):
            st.session_state.stage = 2
            st.rerun()
    with predict_col:
        predict_clicked = st.button(
            "Dự đoán",
            type="primary",
            use_container_width=True,
            key="run_prediction",
        )

    if predict_clicked:
        bmi_value = st.session_state.weight_kg / ((st.session_state.height_cm / 100.0) ** 2)
        input_values = {
            "BMI": bmi_value,
            "GenHlth": GENERAL_HEALTH[st.session_state.ui_GenHlth],
            "MentHlth": int(st.session_state.MentHlth),
            "PhysHlth": int(st.session_state.PhysHlth),
            "Age": AGE_GROUPS[st.session_state.ui_Age],
            "Education": EDUCATION_LEVELS[st.session_state.ui_Education],
            "Income": INCOME_LEVELS[st.session_state.ui_Income],
            "Sex": 1 if st.session_state.ui_Sex == "Nam" else 0,
        }
        for field, _ in BINARY_QUESTIONS:
            input_values[field] = 1 if st.session_state[f"ui_{field}"] == "Có" else 0

        try:
            model_input = apply_feature_pipeline(input_values)
            score = float(model.predict_proba(model_input)[:, 1][0])
            predicted_label = int(score >= threshold)
        except Exception as exc:
            st.markdown("### Không thể tạo dự đoán")
            st.write(
                "Dữ liệu đầu vào chưa khớp với cấu trúc đặc trưng trong mô hình đã xuất. "
                "Hãy kiểm tra lại notebook và chạy ô xuất mô hình sau khi toàn bộ quy trình huấn luyện hoàn tất."
            )
            st.code(str(exc))
        else:
            st.session_state.last_prediction = {
                "label": predicted_label,
                "score": score,
                "bmi": bmi_value,
                "threshold": threshold,
            }
            st.session_state.stage = 4
            st.rerun()

if st.session_state.stage == 4 and "last_prediction" in st.session_state:
    result = st.session_state.last_prediction
    st.divider()
    st.markdown('<div class="stage-title">Kết quả dự đoán</div>', unsafe_allow_html=True)
    st.markdown(f"**BMI tính từ chiều cao và cân nặng: {result['bmi']:.1f}**")
    if result["label"] == 1:
        st.markdown('<div class="stage-title">Nhãn dự đoán: 1</div>', unsafe_allow_html=True)
        st.write("Theo nhãn của bộ dữ liệu, nhóm 1 gồm người được xếp vào nhóm tiền tiểu đường hoặc tiểu đường.")
    else:
        st.markdown('<div class="stage-title">Nhãn dự đoán: 0</div>', unsafe_allow_html=True)
        st.write("Theo nhãn của bộ dữ liệu, nhóm 0 là nhóm không được xếp vào nhóm tiền tiểu đường hoặc tiểu đường.")
    st.markdown(f"**Điểm ước tính của mô hình cho nhãn 1: {result['score']:.1%}**")
    st.caption(
        "Điểm này không phải xác suất lâm sàng đã được hiệu chuẩn. Kết quả chỉ phục vụ mục đích học tập, "
        "không dùng để chẩn đoán hoặc thay thế ý kiến của nhân viên y tế. Mô hình được học từ dữ liệu khảo sát "
        "người trưởng thành tại Hoa Kỳ năm 2015 nên có thể không phù hợp để đánh giá người dùng tại Việt Nam."
    )
    if st.button("Chỉnh sửa thông tin", use_container_width=True, key="edit_answers"):
        st.session_state.stage = 1
        st.rerun()
