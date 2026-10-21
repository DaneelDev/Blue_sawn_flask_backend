## EN version:
# 🏪 Online Store: Flask Backend (`server.py`)

A Flask-based backend for an online store: it encrypts personal data, works with PostgreSQL, and sends email verification codes.

---

## 🔐 Key Features

- **AES‑GCM Encryption** — names, phone numbers, and addresses are stored in encrypted form.  
- **SQL Injection Protection** — only parameterized queries are used; a whitelist of columns is applied for sorting.  
- **Email Verification** — one-time 6‑digit code sent via Yandex SMTP.  
- **Transactions** — `commit`/`rollback` ensures no “partial” records are left in the database.  

---

## 🚀 How to Run

1. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate

   pip install flask flask-cors psycopg2-binary cryptography python-dotenv
   ```

2. **Create a `.env` file in the same folder as `server.py`:**
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
   SMTP_USER=your_email@yandex.ru
   SMTP_PASS=your_app_password
   PORT=3001
   ```
   > `ENCRYPTION_KEY` must be exactly 64 hexadecimal characters (32 bytes). For SMTP, use an app password, not your main email password.

3. **Start the server:**
   ```bash
   python server.py
   ```
   The server will be available at `http://0.0.0.0:3001`.

---

## 🌐 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/products` | Products with category filtering and safe sorting (whitelisted columns). |
| `POST` | `/orders` | Create an order; personal data is encrypted before saving. |
| `POST` | `/send-email` | Send a verification code to the provided email. |
| `POST` | `/verify-code` | Verify a one-time code. |
| `GET` | `/users?email=...` | Get user data (personal data is decrypted on the backend). |
| `POST` | `/users` | Create or update a user; personal data is encrypted. |

---

## RU version:
🏪 Магазин: Flask Backend (`server.py`)

Бэкенд интернет‑магазина на Flask: шифрует персональные данные, работает с PostgreSQL, отправляет коды подтверждения на email.

🔐 Главные фишки

- **AES‑GCM шифрование** — имена, телефоны и адреса хранятся в зашифрованном виде.
- **Защита от SQL‑инъекций** — только параметризованные запросы; для сортировки — белый список колонок.
- **Верификация по email** — одноразовый 6‑значный код, отправка через Yandex SMTP.
- **Транзакции** — `commit`/`rollback`, чтобы не было «половинчатых» записей.

🚀 Как запустить

1. **Создай виртуальное окружение и установи зависимости:**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install flask flask-cors psycopg2-binary cryptography python-dotenv
```

2. **Создай `.env` в папке с `server.py`:**
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
SMTP_USER=your_email@yandex.ru
SMTP_PASS=your_app_password
PORT=3001
```
> `ENCRYPTION_KEY` — ровно 64 HEX‑символа (32 байта). Для SMTP используй пароль приложения.

3. **Запусти сервер:**
```bash
python server.py
```
Сервер будет доступен на `http://0.0.0.0:3001`.


🌐 Эндпоинты

| Метод | Путь | Что делает |
|-------|------|------------|
| `GET` | `/products` | Товары с фильтрацией по категории и безопасной сортировкой. |
| `POST` | `/orders` | Создание заказа; персональные данные шифруются перед сохранением. |
| `POST` | `/send-email` | Отправка кода подтверждения на email. |
| `POST` | `/verify-code` | Проверка одноразового кода. |
| `GET` | `/users?email=...` | Получение данных пользователя (данные расшифровываются на бэкенде). |
| `POST` | `/users` | Создание/обновление пользователя; персональные данные шифруются. |