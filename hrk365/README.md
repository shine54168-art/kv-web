# HiReKing（HRK365）— 官方網站

新加坡獵頭品牌 HiReKing 的台灣官網，網域 hrk365.com。純靜態網站，無需伺服器，可直接部署於 GitHub Pages。

- 中文（預設）：`/`
- 英文：`/en/`
- 共 16 個頁面 × 2 種語言 = 32 個獨立網址，各自有 canonical 與 hreflang 標記。

---

## 目錄結構

```
_src/config.json        全站設定：品牌、聯絡資訊、導覽列、頁尾
_src/pages/*.json       每一頁的內容（中英文成對）
tools/build.py          建置腳本：把 JSON 組成靜態 HTML
assets/css/site.css     設計系統（顏色、字級、元件）
assets/js/site.js       導覽列、手機選單、FAQ 展開、捲動動畫
index.html, about/, …   建置產生的頁面（請勿手動編輯）
```

## 改內容

1. 編輯 `_src/pages/` 底下對應的 JSON 檔（**不要**直接改根目錄的 `.html`，下次建置會被覆蓋）
2. 執行建置：

```bash
python3 tools/build.py
```

3. 本機預覽：

```bash
python3 -m http.server 8000
# 開 http://localhost:8000
```

4. commit 建置後的 HTML 一起推上去（GitHub Pages 直接讀檔，不跑建置）

### 頁面內容的寫法

每個 JSON 由 `blocks` 陣列組成，每個 block 是一個版面區塊。可用的型別：

| type | 用途 |
|---|---|
| `hero` / `pagehero` | 首頁大圖 / 內頁標題區 |
| `cards` | 卡片格（`cols` 指定 2 或 3 欄） |
| `split` | 左文字右面板的兩欄區塊（`reverse` 可左右對調） |
| `steps` | 編號流程 |
| `stats` | 數字統計 |
| `table` | 比較表格 |
| `faq` | 可展開的問答（會自動產生 FAQ 結構化資料） |
| `quotes` | 客戶推薦 |
| `posts` | 文章卡片 |
| `contact` | 聯絡表單＋聯絡資訊 |
| `rich` | 自由 HTML 段落 |
| `cta` | 行動呼籲橫幅 |

所有文字都寫成 `{"zh": "中文", "en": "English"}`，建置時自動分流到兩個語言版本。

---

## 上線前必須補齊的資料

以下項目目前是佔位內容，**上線前務必替換**（在網站上以 `待補` 標籤標示）：

| 位置 | 待補內容 |
|---|---|
| `_src/config.json` → `contact` | 電話、地址、LINE ID、正式 email |
| `_src/config.json` → `contact.form_endpoint` | 表單接收端點（見下方） |
| `_src/config.json` → `brand.licence` | **私立就業服務機構許可證字號**（法定必須揭示） |
| `_src/config.json` → `brand.legal_name` / `parent` | 台灣公司登記全名、新加坡母公司名稱 |
| `_src/pages/about.json` | 顧問團隊介紹、公司統編、成立日期 |
| `_src/pages/index.json` → `stats` | 實績數字（目前為 `—`，沒有依據的數字不放） |
| `_src/pages/index.json` → `quotes` | 客戶推薦（需經客戶書面同意才可刊登） |
| `assets/img/logo-mark.svg` | **目前是暫用的 SVG 替身**，請換成正式 logo（見下方） |
| `assets/img/og-banner.png` | 社群分享圖（用 LinkedIn banner 那張即可，1200×630 以上） |
| `assets/img/` | 團隊照片 |

> **法規提醒**：依台灣《就業服務法》，私立就業服務機構須揭示許可證字號與收費標準。上線前請確認相關資訊已完整刊登。

### Logo 檔案

網站的 logo 目前是一個暫用的 SVG（`assets/img/logo-mark.svg`），只是把 HR 疊字與銅金漸層做了近似。**請用正式檔案覆蓋它**：

1. 把透明背景版的 logo 存成 `assets/img/logo-mark.svg`（向量最佳）或 `logo-mark.png`
2. 若用 PNG，記得同步修改 `_src/config.json` 的 `brand.logo` 副檔名，再重新建置
3. 深色底版本目前不需要另外準備：導覽列是白底、頁尾是深底，透明背景的銅金 logo 兩邊都清楚

### 聯絡表單

目前 `form_endpoint` 是空的，此時表單會**改用信件模式**：使用者按送出會開啟自己的郵件軟體，內容自動帶入並寄到 `contact.email`。這在純靜態網站上一定收得到，缺點是使用者必須有設定好的郵件軟體。

要改成直接收表單，填入 `form_endpoint` 即可自動切換：

- [Formspree](https://formspree.io/)：免費方案即可收信，把產生的網址填入 `config.json`
- Google Forms / Typeform：改為導向外部表單
- 若日後需要寫入資料庫或 CRM，就得改成有後端的架構（本站目前為純靜態）

---

## 部署到 GitHub Pages

1. 把這個資料夾的內容放到獨立 repo 的根目錄
2. Settings → Pages → Source 選 `Deploy from a branch`，分支選 `main`、目錄選 `/ (root)`
3. Custom domain 填 `hrk365.com`（`CNAME` 檔已內建）
4. 到網域註冊商設定 DNS：
   - `A` 記錄指向 `185.199.108.153`、`185.199.109.153`、`185.199.110.153`、`185.199.111.153`
   - `CNAME` 記錄 `www` 指向 `<github-username>.github.io`
5. 回 Pages 設定勾選 `Enforce HTTPS`

## SEO

- `sitemap.xml` 與 `robots.txt` 由建置腳本自動產生
- 首頁含 Organization 結構化資料；有 FAQ 的頁面自動輸出 FAQPage 結構化資料
- 上線後記得到 Google Search Console 提交 sitemap
