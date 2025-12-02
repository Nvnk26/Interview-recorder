# Online Interview Recording System
# 1. OVERVIEW
`web_phong_van` là hệ thống phỏng vấn trực tuyến chuyên nghiệp cho phép ứng viên trả lời câu hỏi thông qua video.  
Hệ thống hỗ trợ:
- Giao diện câu hỏi theo trình tự  
- Giới hạn thời gian trả lời  
- Ghi hình bằng MediaRecorder  
- Tự động upload video  
- Token-based access (mỗi ứng viên một token duy nhất)  
- Break-time giữa các câu  
- Webhook/email khi hoàn thành

Dự án thích hợp dùng cho nhà tuyển dụng, trung tâm đánh giá nhân sự, hoặc tổ chức phỏng vấn từ xa.

# 2. SYSTEM FEATURES (FULL DETAILS)
## 2.1 Video Recording Engine
- Sử dụng MediaRecorder API  
- Hỗ trợ các codec:
  - `video/webm;codecs=vp8`
  - `video/webm;codecs=vp9`
- Preview camera trực tiếp  
- Auto fallback khi codec không hỗ trợ  
- Tự động dừng khi countdown = 0  
- Lưu video dưới dạng blob, sau đó upload bằng Fetch  
- Re-encoding compatibility với ffmpeg (server-side)

## 2.2 Time Control System
Mỗi câu hỏi có:
- **Thời gian trả lời:** ví dụ 10s  
- **Break time sau câu hỏi:** ví dụ 5s  
- **3 break tuỳ chỉnh:** 5s – 5s – 3s  
- Trong break có thể hiển thị:
  - “Next”
  - “Start Recording”
  - Hoặc auto-skip  
Countdown gồm:
- Timer hiển thị mm:ss  
- Progress bar  
- Âm thông báo cuối thời gian (tùy chọn)

## 2.3 Token Authentication
- Mỗi ứng viên có token duy nhất  
- Token kiểm tra:
  1. Tồn tại  
  2. Chưa hết hạn  
  3. Chưa used  
- Nếu invalid → redirect sang trang lỗi  
- Token log:
  - CPU visited  
  - Browser info  
  - Device type

## 2.4 Upload & Storage Module
Upload workflow:
1. MediaRecorder → Blob  
2. Blob → FormData  
3. Fetch POST → `/api/upload-video`  
4. Backend lưu file: `/records/<token>/<question>.webm`  
5. (Optional) ffmpeg remux → mp4  
6. Gửi webhook/email khi mọi video hoàn tất  

Upload có:
- Chunking (tùy chọn)  
- Retry 3 lần  
- Tối đa kích thước 300MB/video  
- Hash checksum SHA-256

## 2.5 UI/UX
- Mobile-first  
- Bootstrap 5  
- 3 nút chính:
  - Start Recording  
  - Stop Recording  
  - Next  
- Màn hình câu hỏi:
  - Title  
  - Description  
  - Countdown  
  - Preview camera  
- Màn hình break:
  - Thời gian còn lại  
  - Hướng dẫn  
  - Nút skip

# 3. SYSTEM ARCHITECTURE
```text
┌───────────────────┐
│      Browser       │
│  (Frontend + JS)   │
└───────┬───────────┘
        │ MediaRecorder
        ▼
┌───────────────────┐
│     Upload API     │
│  /api/upload-video │
└───────┬───────────┘
        │ Save video
        ▼
┌───────────────────┐
│    File Storage    │
│ /records/<token>/  │
└───────┬───────────┘
        │ Log DB
        ▼
┌───────────────────┐
│  PostgreSQL DB     │
└───────┬───────────┘
        │ Notify
        ▼
┌───────────────────┐
│ Webhook / Email HR │
└───────────────────┘
```
# 4. Project structure
``` text
web_phong_van/
│
├── index.html
├── style.css
├── recorder.js
├── recorder-v3.js
├── /questions/questions.json
│
├── /records/
│   └── <token>/<question>.webm
│
└── server/
    ├── index.js
    ├── db.sql
    ├── config.js
    ├── utils/
    └── services/
```
# 5. INSTALLATION & DEPLOYMENT
## 5.1 Clone project
``` bash
git clone https://github.com/nhnminh1409/web_phong_van
cd web_phong_van
```
## 5.2 Node.js dependencies
``` bash
npm install
```
## 5.3 Environment variables (server/.env)
``` ini
PORT=3000
DATABASE_URL=postgres://user:pass@localhost:5432/interview
VIDEO_PATH=./records
WEBHOOK_URL=https://api.company.com/interview-done
```

## 5.4 Start server
``` bash
npm start
```

## 5.5 Production (Nginx reverse proxy)
``` nginx
location / {
    proxy_pass http://localhost:3000;
}
```
# 6. DATABASE SCHEMA
``` sql
CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64) UNIQUE NOT NULL,
    candidate_name VARCHAR(255),
    email VARCHAR(255),
    expires_at TIMESTAMP,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE interview_results (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64) REFERENCES tokens(token),
    question_number INTEGER NOT NULL,
    video_path TEXT NOT NULL,
    duration INTEGER,
    filesize BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64),
    event TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

# 7. API DOCUMENTATION (FULL)
## 7.1 Check token
POST /api/check-token
Request:
``` json
{ "token": "abc123" }
```

Response:
``` json
{
  "valid": true,
  "candidate": "Nguyen Van A",
  "expires_at": "2025-12-30T10:00:00Z"
}
```
## 7.2 Upload video
POST /api/upload-video

FormData:
``` makefile
token: abc123
question: 1
file: <blob>
```

Response:
``` json
{
  "status": "success",
  "video_path": "/records/abc123/1.webm"
}
```
## 7.3 Mark interview complete

POST /api/complete

Response:
``` json
{ "status": "ok" }
```

## 8. INTERVIEW FLOW DIAGRAM (ASCII)
``` text
[Start] 
   │
   ▼
[Token Login]──invalid──▶[Error Page]
   │valid
   ▼
[Show Question 1]
   │ Start Recording
   ▼
[Countdown Running]
   │ timeout or stop
   ▼
[Upload Video]
   │
   ▼
[Break 1: 5s] → [Break 2: 5s] → [Break 3: 3s]
   │
   ▼
[Next Question]
   │
   ▼
[Completed] → Send Email/Webhook → [Thank you]
```
# 9. USAGE GUIDE (FULL)

## 9.1 Ứng viên truy cập
- URL: `https://domain.com/token/abc123`
- Hệ thống kiểm tra token:
  - Nếu hợp lệ → vào trang intro
  - Nếu không → báo lỗi

## 9.2 Màn hình câu hỏi
- Hiển thị câu hỏi số X
- Nút **Start Recording**
- Hướng dẫn:
  - Giữ mắt nhìn camera
  - Nói rõ ràng
  - Không rời khung hình

## 9.3 Ghi hình
- Khi bấm **Start**:
  - Camera bật
  - Countdown chạy
  - Tự động stop khi hết giờ

## 9.4 Upload video
- Video upload ngay sau khi stop
- Nếu fail:
  - Retry 3 lần
  - Fail toàn bộ → báo lỗi

## 9.5 Break
- 5s → nút **Next**
- 5s → nút **Start Recording**
- 3s → tự động qua câu

## 9.6 Hoàn thành
- Gửi webhook → HR
- Hiển thị thông báo:
> “Bạn đã hoàn thành buổi phỏng vấn!”

---

# 10. SECURITY BEST PRACTICES
- Token ≥ 32 ký tự
- Token hết hạn 24–72h
- Không lưu video trong `/public`
- Sử dụng HTTPS
- Chặn CORS từ domain lạ
- Giới hạn file:
  - Max 300MB
  - Chỉ `webm`
- Upload cần:
  - Xác thực token
  - Kiểm tra `question_id` hợp lệ
