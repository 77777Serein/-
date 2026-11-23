# 天氣預測

繁體中文、手機與桌面皆可使用的臺北市天氣預報網站。後端以 Flask 提供首頁與同來源 API 代理，前端使用原生 JavaScript 顯示天氣，不直接呼叫第三方服務。

## 專案結構與資料流

```text
app.py                 Flask 進入點與 API 代理
templates/index.html   響應式首頁、CSS 與原生 JavaScript
tests/test_app.py      unittest 單元測試
requirements.txt       Flask、requests 執行依賴
.python-version        指定 Python 3.12
```

資料流：瀏覽器 → `/api/天氣預報` → Flask → Open-Meteo 官方 HTTPS API → Flask 驗證資料 → 瀏覽器。網站查詢固定的臺北市座標，按「換一張」會載入並輪播不同預報日期。服務不使用資料庫、背景工作或本機永久資料。

## 本機執行

需要 Python 3.12。以下命令在專案根目錄執行。

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run
```

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run
```

在瀏覽器開啟 `http://127.0.0.1:5000/`。Flask 開發伺服器僅供本機開發，部署時由 Vercel 執行 `app.py` 中的 `app` 物件。

## 測試與端點驗證

```bash
python -m unittest discover -s tests -v
```

本機啟動後可在另一個終端驗證：

```bash
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/api/%E5%A4%A9%E6%B0%A3%E9%A0%90%E5%A0%B1
```

健康檢查預期為 `{"ok":true}`；預報端點需能連上 Open-Meteo 才會回傳即時資料。

## 推送至 GitHub

在 GitHub 建立空白 repository，將下方 `YOUR-USERNAME` 與 `YOUR-REPOSITORY` 換成自己的值：

```bash
git init
git add .
git commit -m "建立天氣預測網站"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

## 部署至 Vercel

1. 在 Vercel 匯入剛推送的 GitHub repository。
2. Framework Preset 選擇 Flask（若介面要求選擇）；Root Directory 保持專案根目錄。
3. 不要設定自訂 Build Command 或把 `flask run`、`python app.py` 設為建置指令。Vercel 會依根目錄 `app.py` 的 `app` 物件部署 Python Flask 應用，`.python-version` 指定 Python 3.12。
4. 此專案目前不需要密鑰。如日後加入需要的密鑰，請放在 Vercel Project Settings 的 Environment Variables，不要提交到 Git。
5. 部署完成後使用 Vercel 網址檢查首頁、`/api/health` 與 `/api/天氣預報`。

本專案沒有使用舊式 `@vercel/python` `builds` / `rewrites` 設定。GitHub 推送與 Vercel 部署成功與否，必須在各平台實際操作後確認。
