# Streamlit demo: dự đoán nhóm tiểu đường

Ứng dụng nhập thông tin qua 3 chặng, tự tính BMI từ chiều cao/cân nặng và xuất nhãn `0` hoặc `1` bằng mô hình đã huấn luyện trong notebook.

## 1. Xuất mô hình từ notebook

**Cách khuyến nghị:** dùng file `Diabete_final_streamlit_ready.ipynb` có trong gói này. Đây là bản sao của notebook gốc đã được chuẩn bị để chạy từ đầu: ô cài đặt đặt trước ô import `kagglehub`, bổ sung các import `precision_score` và `roc_auc_score` còn thiếu, xóa output cũ và thêm ô xuất mô hình ở cuối. File `Diabete_final.ipynb` gốc của bạn không bị thay đổi.

1. Tải `Diabete_final_streamlit_ready.ipynb` lên Google Colab hoặc mở bằng môi trường Jupyter.
2. Chạy toàn bộ notebook từ đầu đến cuối theo thứ tự. Ô cuối cùng sẽ lưu Logistic Regression, ngưỡng phân loại và các bước tiền xử lý cần thiết cho ứng dụng.
3. Nếu chạy trên Google Colab, ô xuất sẽ tự gọi tải `diabetes_model_bundle.joblib` xuống máy. Nếu chạy Jupyter cục bộ, tìm tệp này trong thư mục làm việc của notebook.
4. Đặt `diabetes_model_bundle.joblib` vào cùng thư mục với `app.py`.

Nếu bạn tiếp tục dùng file notebook gốc, hãy bổ sung `precision_score` vào import ở ô 26, bổ sung `roc_auc_score` vào import ở ô 27, cài `kagglehub` trước khi import nó ở ô 4, rồi sao chép nội dung `export_model_cell.txt` vào một ô code mới ở cuối notebook.

Tệp mô hình lưu lại Logistic Regression, ngưỡng đã chọn từ tập Validation, bộ làm sạch, bộ chuẩn hóa và các đặc trưng đã chọn. Không huấn luyện lại mô hình trong ứng dụng.

## 2. Cài đặt trên Windows

Cài Python từ trang chủ Python nếu máy chưa có. Khi cài, bật tùy chọn thêm Python vào PATH nếu trình cài đặt có hiển thị tùy chọn đó.

Mở Command Prompt (CMD), dùng `cd` để chuyển vào thư mục chứa `app.py`, sau đó chạy lần lượt:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Chạy ứng dụng:

```bat
python -m streamlit run app.py
```

Streamlit sẽ in địa chỉ cục bộ, thường là `http://localhost:8501`. Giữ cửa sổ CMD mở khi sử dụng ứng dụng.

Nếu lệnh `py` không hoạt động, thử thay `py` bằng `python`. Nếu gặp lỗi khi tải mô hình do không tương thích phiên bản scikit-learn, xem phần `library_versions` được in ra khi chạy ô xuất mô hình và cài đúng phiên bản `scikit-learn` được ghi ở đó rồi chạy lại ứng dụng.

## 3. Cấu trúc thư mục

```text
diabetes_streamlit_demo/
├── app.py
├── requirements.txt
├── export_model_cell.txt
├── Diabete_final_streamlit_ready.ipynb
├── README.md
└── diabetes_model_bundle.joblib   # chép vào sau khi xuất từ notebook
```

## Lưu ý về dữ liệu và sức khỏe

- Nhãn `0` là nhóm không được gắn nhãn tiền tiểu đường/tiểu đường trong bộ dữ liệu; nhãn `1` gộp tiền tiểu đường hoặc tiểu đường.
- Các khoảng tuổi, học vấn và thu nhập được mã hóa theo bộ dữ liệu khảo sát BRFSS 2015. Các khoảng thu nhập được giữ theo USD của bộ dữ liệu gốc.
- Bộ dữ liệu là khảo sát người trưởng thành tại Hoa Kỳ năm 2015. Kết quả không nhất thiết khái quát được cho người dùng tại Việt Nam.
- Điểm do mô hình trả về không phải xác suất lâm sàng đã được hiệu chuẩn, và demo không dùng để chẩn đoán hoặc thay thế lời khuyên y tế.
