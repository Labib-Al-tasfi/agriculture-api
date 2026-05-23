# Agriculture Database API

FastAPI-based REST API for the Agriculture DB Data Scientist Assessment.  
Connects to a MySQL database, processes data using pandas & exposes 8 analytical endpoints across 2 reports.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Database | MySQL |
| DB Connection | SQLAlchemy + PyMySQL |
| Data Processing | Python + pandas |
| API Framework | FastAPI |
| API Server | Uvicorn |
| Python Version | 3.11+ |

---

## Project Structure

```
agriculture_api/
├── main.py                  #FastAPI app entry point
├── database.py              #DB connection & data loading
├── validators.py            #Filter validation logic
├── routers/
│   ├── farms.py             #Endpoints 1–4 (Farm Performance)
│   └── crops_markets.py     #Endpoints 5–8 (Crop & Market Intelligence)
├── requirements.txt
├── .env.example             #Template for credentials (Safe for sharing)
├── .env                     #Actual credentials (Don't commit)
├── .gitignore
└── Dockerfile
```

---

## Setup & Run

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/agriculture-api.git
cd agriculture-api
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up credentials

Copy `.env.example` to `.env` and fill in your database credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
HOST=your_db_host
PORT=3306
DB=agriculture_db
USER=your_username
PASSWORD=your_password
```

### 5. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Interactive docs (Swagger UI):** http://localhost:8000/docs
- **Alternative docs (ReDoc):** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/

---

## API Endpoints

### Report 1 — Farm Performance

| Method | Endpoint | Description |
|---|---|---|
| GET | `/farms/summary` | All farms — revenue, cost, profit, loss % |
| GET | `/farms/top` | Top N farms ranked by profit / revenue / yield |
| GET | `/farms/loss-analysis` | Post-harvest loss by region, season, crop |
| GET | `/farms/{farm_id}/performance` | Single farm detail by crop & market |

### Report 2 — Crop & Market Intelligence

| Method | Endpoint | Description |
|---|---|---|
| GET | `/crops/yield-efficiency` | Actual vs benchmark yield per crop |
| GET | `/crops/seasonal-trend` | Revenue trends by season and year |
| GET | `/markets/price-comparison` | Price comparison across market channels |
| GET | `/crops/quality-breakdown` | Grade distribution + pesticide residue |

---

## Filter Reference

| Filter | Accepted Values |
|---|---|
| `region` | Dhaka, Chittagong, Sylhet, Rajshahi, Khulna, Rangpur, Barisal, Mymensingh |
| `farm_type` | Small, Medium, Large, Commercial |
| `crop_category` | Cereal, Vegetable, Fruit, Pulse, Oilseed, Cash Crop, Spice |
| `season` | Spring, Summer, Autumn, Winter |
| `market_type` | Local, Wholesale, Export, Retail, Government Procurement |
| `price_tier` | Low, Medium, High, Premium |
| `quality_grade` | A, B, C, D |
| `pesticide_residue` | None, Trace, Low, High |
| `water_requirement` | Low, Medium, High |
| `year` | 2022, 2023, 2024 |
| `quarter` | 1, 2, 3, 4 |
| `metric` | profit, revenue, yield |

Invalid filter values return **HTTP 422** with a clear error message.

---

## Run with Docker (Optional)

```bash
docker build -t agriculture-api .
docker run -p 8000:8000 --env-file .env agriculture-api
```

---

## Notes

- `.env` is excluded from version control via `.gitignore`
- Data is loaded from `vw_harvest_full` view at startup and cached in memory
- All monetary values are in BDT (Bangladeshi Taka)
