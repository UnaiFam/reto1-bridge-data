# main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import pandas as pd
import numpy as np
import os, re, json, ast
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ==============================
# Cargar .env y configurar Mongo
# ==============================
load_dotenv()

MONGO_URI   = os.getenv("DB_URL")
DB_NAME     = os.getenv("DB_NAME", "Prueba1")
# ¡OJO! En Atlas tu colección era "Electricos" (mayúscula). Por defecto la ponemos así:
COL_FUEL    = os.getenv("COL_FUEL", "Combustible")
COL_EV      = os.getenv("COL_EV", "Electricos")
COL_TOLL    = os.getenv("COL_TOLL", "Peaje")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coll_fuel = db[COL_FUEL]
coll_ev   = db[COL_EV]
coll_toll = db[COL_TOLL]

# ==============================
# FastAPI + CORS
# ==============================
app = FastAPI(title="API KPIs: Combustible, EV, Peaje")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Utilidades
# ==============================
def _to_num_eur(x):
    if x is None or (isinstance(x, float) and pd.isna(x)): return np.nan
    s = str(x).strip().replace("€","").replace("\xa0"," ").strip()
    s = re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", s)  # 1.234,56 -> 1234,56
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")  # 1234,56 -> 1234.56
    s = re.sub(r"[^\d.\-]", "", s)
    try: return float(s)
    except: return np.nan

def _fix_jsonish(s):
    s = re.sub(r"(?<!\\)'", '"', str(s))
    return s.replace("None","null").replace("True","true").replace("False","false")

def parse_lineas(x):
    if isinstance(x, list): return x
    if isinstance(x, dict): return [x]
    if x is None or (isinstance(x, float) and pd.isna(x)): return []
    s = _fix_jsonish(x)
    for fn in (json.loads, lambda t: ast.literal_eval(t)):
        try:
            out = fn(s)
            if isinstance(out, dict): return [out]
            if isinstance(out, list): return out
        except Exception:
            continue
    return []

dias_map = {
    "Monday":"Lunes","Tuesday":"Martes","Wednesday":"Miércoles","Thursday":"Jueves",
    "Friday":"Viernes","Saturday":"Sábado","Sunday":"Domingo"
}

def _ser(d):
    out = {}
    for k, v in d.items():
        out[k] = v.to_dict(orient="records") if isinstance(v, pd.DataFrame) else v
    return out

# ==============================
# Filtros Mongo por fechas
# ==============================
def _build_filter_fechas_cabecera(start_date: str|None, end_date: str|None):
    f = {}
    if start_date or end_date:
        rango = {}
        if start_date: rango["$gte"] = start_date
        if end_date:   rango["$lte"] = end_date
        f["fechaEmision"] = rango
    return f

def _build_filter_fechas_toll(start_date: str|None, end_date: str|None):
    f = {}
    if start_date or end_date:
        rango = {}
        if start_date: rango["$gte"] = start_date
        if end_date:
            dt = datetime.fromisoformat(end_date) + timedelta(days=1) - timedelta(seconds=1)
            rango["$lte"] = dt.isoformat()
        f["fechaHora"] = rango
    return f

def load_df_mongo(collection, filtros: dict) -> pd.DataFrame:
    try:
        data = list(collection.find(filtros))
    except Exception as e:
        print("Error Mongo:", repr(e))
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    return df

# ==============================
# Normalización temporal
# ==============================
def add_time_cols_fuel_ev(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "fechaEmision" not in df.columns:
        df["fechaEmision"] = pd.NaT
    df["fechaEmision"] = pd.to_datetime(df["fechaEmision"], errors="coerce")
    df["horaEmision"]  = df.get("horaEmision", "00:00:00")
    df["dt"] = pd.to_datetime(
        df["fechaEmision"].astype(str) + " " + df["horaEmision"].fillna("00:00:00"),
        errors="coerce"
    )
    df["mes"]  = df["dt"].dt.to_period("M").astype(str)
    df["hora"] = df["dt"].dt.hour
    df["dia_semana"] = df["dt"].dt.day_name().map(dias_map)
    return df

def add_time_cols_toll(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "fechaHora" not in df.columns:
        df["fechaHora"] = pd.NaT
    df["fechaHora"] = pd.to_datetime(df["fechaHora"], errors="coerce")
    df["mes"]  = df["fechaHora"].dt.to_period("M").astype(str)
    df["hora"] = df["fechaHora"].dt.hour
    df["dia_semana"] = df["fechaHora"].dt.day_name().map(dias_map)
    df["is_weekend"] = df["dia_semana"].isin(["Sábado","Domingo"])
    return df

# ==============================
# Explode líneas
# ==============================
def explode_fuel_lines(df_fuel: pd.DataFrame) -> pd.DataFrame:
    if df_fuel.empty: return pd.DataFrame()
    rows = []
    for _, r in df_fuel.iterrows():
        lineas = r.get("lineas_parsed") or parse_lineas(r.get("lineas"))
        for li in (lineas or []):
            litros = li.get("litros")
            ppu    = li.get("precioPorLitro") or li.get("precio_unitario") or li.get("precio")
            importe_li = li.get("importe")
            try: l = float(litros) if litros is not None else np.nan
            except: l = np.nan
            try: p = float(ppu) if ppu is not None else np.nan
            except: p = np.nan
            if pd.isna(p) and importe_li is not None and pd.notna(l) and l > 0:
                try: p = float(importe_li)/l
                except: pass
            importe = (l*p) if (pd.notna(l) and pd.notna(p)) else np.nan
            rows.append({
                "idTicket": r.get("idTicket"),
                "idUsuario": r.get("idUsuario"),
                "empresaTransporte": r.get("empresaNombre"),
                "dt": r.get("dt"), "mes": r.get("mes"), "hora": r.get("hora"), "dia_semana": r.get("dia_semana"),
                "producto": li.get("producto"),
                "litros": l, "precio_litro": p, "importe_linea": importe,
                "baseImponible": r.get("baseImponible"), "iva": r.get("iva"), "total": r.get("total"),
                "metodoPago": r.get("metodoPago"),
            })
    df_lines = pd.DataFrame(rows)
    for c in ["litros","precio_litro","importe_linea","baseImponible","iva","total"]:
        if c in df_lines.columns: df_lines[c] = pd.to_numeric(df_lines[c], errors="coerce")
    return df_lines

def explode_ev_lines(df_ev: pd.DataFrame) -> pd.DataFrame:
    if df_ev.empty: return pd.DataFrame()
    rows = []
    for _, r in df_ev.iterrows():
        lineas = r.get("lineas_parsed") or parse_lineas(r.get("lineas"))
        for li in (lineas or []):
            kwh_raw = li.get("kwh") or li.get("energia") or li.get("energia_kwh")
            ppu_raw = li.get("precio_kwh") or li.get("precioUnitario") or li.get("precio_unitario") or li.get("precio")
            importe_li = li.get("importe") or li.get("importeLinea") or li.get("importe_linea")
            try: k = float(kwh_raw) if kwh_raw is not None else np.nan
            except: k = np.nan
            try: p = float(ppu_raw) if ppu_raw is not None else np.nan
            except: p = np.nan
            if pd.isna(p) and (importe_li is not None) and pd.notna(k) and k > 0:
                try: p = float(importe_li) / k
                except: pass
            importe = (k * p) if (pd.notna(k) and pd.notna(p)) else np.nan
            rows.append({
                "idTicket": r.get("idTicket"),
                "idUsuario": r.get("idUsuario"),
                "empresaTransporte": r.get("empresaNombre"),
                "dt": r.get("dt"), "mes": r.get("mes"), "hora": r.get("hora"), "dia_semana": r.get("dia_semana"),
                "producto": li.get("producto"),
                "kwh": k, "precio_kwh": p, "importe_linea": importe,
                "baseImponible": r.get("baseImponible"), "iva": r.get("iva"), "total": r.get("total"),
                "metodoPago": r.get("metodoPago"),
                "tipoCorriente": li.get("tipoCorriente") or li.get("tarifa") or r.get("estacion_tarifa"),
                "potenciaKW": li.get("potenciaKW") or li.get("potenciaMaxKW") or li.get("power_kw") or r.get("estacion_potencia_max_kw"),
            })
    df_lines = pd.DataFrame(rows)
    for c in ["kwh","precio_kwh","importe_linea","baseImponible","iva","total","potenciaKW"]:
        if c in df_lines.columns: df_lines[c] = pd.to_numeric(df_lines[c], errors="coerce")
    return df_lines

# ==============================
# KPIs
# ==============================
def _dias_mediana(series_dt):
    s = pd.to_datetime(pd.Series(series_dt).dropna()).sort_values().unique()
    if len(s) < 2: return np.nan
    d = np.diff(s).astype("timedelta64[D]").astype(float)
    return float(np.median(d))

def kpis_usuario_fuel(df_tickets: pd.DataFrame, df_lines: pd.DataFrame):
    if df_tickets.empty or df_lines.empty: return {}
    gasto_usuario_mes = df_tickets.groupby(["idUsuario","mes"])["total"].sum().reset_index()
    tickets_usuario_mes = df_tickets.groupby(["idUsuario","mes"])["idTicket"].nunique().reset_index(name="tickets")
    litros_usuario_mes = df_lines.groupby(["idUsuario","mes"])["litros"].sum().reset_index()
    litros_ticket_usuario = df_lines.groupby(["idUsuario","idTicket"])["litros"].sum().reset_index()
    litros_medio_ticket_usuario = litros_ticket_usuario.groupby("idUsuario")["litros"].mean().reset_index(name="litros_medio_ticket")
    precio_usuario_marca = (
        df_lines.assign(w=df_lines["litros"])
        .groupby(["idUsuario","empresaTransporte"])
        .apply(lambda x: (x["precio_litro"].mul(x["w"]).sum())/x["w"].sum())
        .rename("eur_l").reset_index()
    )
    metodos_usuario = df_tickets.groupby(["idUsuario","metodoPago"])["idTicket"].nunique().reset_index(name="tickets")
    metodos_usuario_mes = df_tickets.groupby(["idUsuario","mes","metodoPago"])["idTicket"].nunique().reset_index(name="tickets")
    metodos_usuario_mes["pct"] = 100 * metodos_usuario_mes["tickets"] / metodos_usuario_mes.groupby(["idUsuario","mes"])["tickets"].transform("sum")
    dias_mediana = df_tickets.groupby("idUsuario")["dt"].apply(_dias_mediana).reset_index(name="dias_mediana")
    anomalias_usuario = (
        df_lines[(df_lines["precio_litro"] < 0.8) | (df_lines["precio_litro"] > 3.0)]
        .groupby("idUsuario")["idTicket"].nunique().reset_index(name="tickets_anomalos")
    )
    gasto_dia_semana = df_tickets.groupby(["idUsuario","dia_semana"])["total"].sum().reset_index()
    return {
        "gasto_usuario_mes": gasto_usuario_mes,
        "tickets_usuario_mes": tickets_usuario_mes,
        "litros_usuario_mes": litros_usuario_mes,
        "litros_medio_ticket_usuario": litros_medio_ticket_usuario,
        "precio_usuario_marca": precio_usuario_marca,
        "metodos_usuario": metodos_usuario,
        "metodos_usuario_mes": metodos_usuario_mes,
        "dias_mediana": dias_mediana,
        "anomalias_usuario": anomalias_usuario,
        "gasto_dia_semana": gasto_dia_semana,
    }

def kpis_empresa_fuel(df_tickets: pd.DataFrame, df_lines: pd.DataFrame):
    if df_tickets.empty or df_lines.empty: return {}
    gasto_mes_emp = df_tickets.groupby(["empresaNombre","mes"])["total"].sum().reset_index().rename(columns={"empresaNombre":"empresa"})
    gasto_total_emp = df_tickets.groupby("empresaNombre")["total"].sum().reset_index().rename(columns={"empresaNombre":"empresa","total":"gasto_total_periodo"})
    vehiculos_emp   = df_tickets.groupby("empresaNombre")["idUsuario"].nunique().reset_index().rename(columns={"empresaNombre":"empresa","idUsuario":"num_vehiculos"})
    gasto_medio_veh = df_tickets.groupby(["empresaNombre","idUsuario"])["total"].sum().groupby("empresaNombre").mean().reset_index().rename(columns={"empresaNombre":"empresa","total":"gasto_medio_por_vehiculo"})
    ranking_veh     = df_tickets.groupby(["empresaNombre","idUsuario"])["total"].sum().reset_index().rename(columns={"empresaNombre":"empresa","total":"gasto_usuario"})
    litros_mes_emp  = df_lines.groupby(["empresaTransporte","mes"])["litros"].sum().reset_index().rename(columns={"empresaTransporte":"empresa"})
    litros_veh_emp  = df_lines.groupby(["empresaTransporte","idUsuario"])["litros"].sum().reset_index().rename(columns={"empresaTransporte":"empresa"})
    precio_global_emp = (
        df_lines.assign(w=df_lines["litros"])
        .groupby("empresaTransporte").apply(lambda x: (x["precio_litro"].mul(x["w"]).sum())/x["w"].sum())
        .reset_index(name="eur_l").rename(columns={"empresaTransporte":"empresa"})
    )
    return {
        "gasto_mes_emp": gasto_mes_emp,
        "gasto_total_emp": gasto_total_emp,
        "vehiculos_emp": vehiculos_emp,
        "gasto_medio_veh": gasto_medio_veh,
        "ranking_veh": ranking_veh,
        "litros_mes_emp": litros_mes_emp,
        "litros_veh_emp": litros_veh_emp,
        "precio_global_emp": precio_global_emp,
    }

def kpis_usuario_ev(df_tickets: pd.DataFrame, df_lines: pd.DataFrame):
    if df_tickets.empty or df_lines.empty: return {}
    gasto_usuario_mes = df_tickets.groupby(["idUsuario","mes"])["total"].sum().reset_index()
    tickets_usuario_mes = df_tickets.groupby(["idUsuario","mes"])["idTicket"].nunique().reset_index(name="tickets")
    kwh_usuario_mes = df_lines.groupby(["idUsuario","mes"])["kwh"].sum().reset_index()
    kwh_ticket_usuario = df_lines.groupby(["idUsuario","idTicket"])["kwh"].sum().reset_index()
    kwh_medio_ticket_usuario = kwh_ticket_usuario.groupby("idUsuario")["kwh"].mean().reset_index(name="kwh_medio_ticket")
    precio_usuario_cpo = (
        df_lines.assign(w=df_lines["kwh"])
        .groupby(["idUsuario","empresaTransporte"])
        .apply(lambda x: (x["precio_kwh"].mul(x["w"]).sum())/x["w"].sum())
        .rename("eur_kwh").reset_index()
    )
    metodos_usuario = df_tickets.groupby(["idUsuario","metodoPago"])["idTicket"].nunique().reset_index(name="tickets")
    metodos_usuario_mes = df_tickets.groupby(["idUsuario","mes","metodoPago"])["idTicket"].nunique().reset_index(name="tickets")
    metodos_usuario_mes["pct"] = 100 * metodos_usuario_mes["tickets"] / metodos_usuario_mes.groupby(["idUsuario","mes"])["tickets"].transform("sum")
    dias_mediana = df_tickets.groupby("idUsuario")["dt"].apply(_dias_mediana).reset_index(name="dias_mediana")
    anomalias_usuario = (
        df_lines[(df_lines["precio_kwh"] < 0.20) | (df_lines["precio_kwh"] > 1.50)]
        .groupby("idUsuario")["idTicket"].nunique().reset_index(name="tickets_anomalos")
    )
    gasto_dia_semana = df_tickets.groupby(["idUsuario","dia_semana"])["total"].sum().reset_index()
    return {
        "gasto_usuario_mes": gasto_usuario_mes,
        "tickets_usuario_mes": tickets_usuario_mes,
        "kwh_usuario_mes": kwh_usuario_mes,
        "kwh_medio_ticket_usuario": kwh_medio_ticket_usuario,
        "precio_usuario_cpo": precio_usuario_cpo,
        "metodos_usuario": metodos_usuario,
        "metodos_usuario_mes": metodos_usuario_mes,
        "dias_mediana": dias_mediana,
        "anomalias_usuario": anomalias_usuario,
        "gasto_dia_semana": gasto_dia_semana,
    }

def kpis_empresa_ev(df_tickets: pd.DataFrame, df_lines: pd.DataFrame):
    if df_tickets.empty or df_lines.empty: return {}
    gasto_mes_emp = df_tickets.groupby(["empresaNombre","mes"])["total"].sum().reset_index().rename(columns={"empresaNombre":"empresa"})
    gasto_total_emp = df_tickets.groupby("empresaNombre")["total"].sum().reset_index().rename(columns={"empresaNombre":"empresa","total":"gasto_total_periodo"})
    vehiculos_emp   = df_tickets.groupby("empresaNombre")["idUsuario"].nunique().reset_index().rename(columns={"empresaNombre":"empresa","idUsuario":"num_vehiculos"})
    gasto_medio_veh = df_tickets.groupby(["empresaNombre","idUsuario"])["total"].sum().groupby("empresaNombre").mean().reset_index().rename(columns={"empresaNombre":"empresa","total":"gasto_medio_por_vehiculo"})
    ranking_veh     = df_tickets.groupby(["empresaNombre","idUsuario"])["total"].sum().reset_index().rename(columns={"empresaNombre":"empresa","total":"gasto_usuario"})
    kwh_mes_emp  = df_lines.groupby(["empresaTransporte","mes"])["kwh"].sum().reset_index().rename(columns={"empresaTransporte":"empresa"})
    kwh_veh_emp  = df_lines.groupby(["empresaTransporte","idUsuario"])["kwh"].sum().reset_index().rename(columns={"empresaTransporte":"empresa"})
    precio_global_emp = (
        df_lines.assign(w=df_lines["kwh"])
        .groupby("empresaTransporte").apply(lambda x: (x["precio_kwh"].mul(x["w"]).sum())/x["w"].sum())
        .reset_index(name="eur_kwh").rename(columns={"empresaTransporte":"empresa"})
    )
    return {
        "gasto_mes_emp": gasto_mes_emp,
        "gasto_total_emp": gasto_total_emp,
        "vehiculos_emp": vehiculos_emp,
        "gasto_medio_veh": gasto_medio_veh,
        "ranking_veh": ranking_veh,
        "kwh_mes_emp": kwh_mes_emp,
        "kwh_veh_emp": kwh_veh_emp,
        "precio_global_emp": precio_global_emp,
    }

def kpis_usuario_toll(df: pd.DataFrame):
    if df.empty: return {}
    dfu = df.copy()
    if "idTicket" not in dfu.columns:
        if "referencia" in dfu.columns: dfu["idTicket"] = dfu["referencia"].astype(str)
        else:
            dfu = dfu.reset_index().rename(columns={"index":"idTicket"})
            dfu["idTicket"] = dfu["idTicket"].astype(str)
    if "importe" not in dfu.columns:
        cand = [c for c in dfu.columns if any(p in c.lower() for p in ["importe","total","precio","coste","amount","valor","pago"])]
        if cand:
            ser = pd.to_numeric(dfu[cand[0]], errors="coerce")
            ser = ser.where(ser.notna(), dfu[cand[0]].apply(_to_num_eur))
            dfu["importe"] = ser
        else:
            dfu["importe"] = np.nan
    gasto_usuario_mes = dfu.groupby(["idUsuario","mes"])["importe"].sum().reset_index().rename(columns={"importe":"gasto_mes"})
    tickets_usuario_mes = dfu.groupby(["idUsuario","mes"])["idTicket"].nunique().reset_index().rename(columns={"idTicket":"tickets"})
    usuario_autopista_mes = (
        dfu.groupby(["idUsuario","mes","autopista"])["importe"]
        .agg(gasto_autopista_mes="sum", tickets_autopista_mes="count").reset_index()
    )
    usuario_autopista_mes["coste_medio_ticket"] = usuario_autopista_mes["gasto_autopista_mes"] / usuario_autopista_mes["tickets_autopista_mes"].replace(0, pd.NA)
    usuario_autopista_mes["pct_gasto_usuario_mes"] = (
        100 * usuario_autopista_mes["gasto_autopista_mes"] /
        usuario_autopista_mes.groupby(["idUsuario","mes"])["gasto_autopista_mes"].transform("sum")
    )
    metodos_usuario_mes = dfu.groupby(["idUsuario","mes","formaPago"])["idTicket"].nunique().reset_index(name="tickets")
    metodos_usuario_mes["pct"] = 100 * metodos_usuario_mes["tickets"] / metodos_usuario_mes.groupby(["idUsuario","mes"])["tickets"].transform("sum")
    dias_mediana = dfu.groupby("idUsuario")["fechaHora"].apply(_dias_mediana).reset_index(name="dias_mediana")
    pct_finde_usuario = dfu.groupby("idUsuario")["is_weekend"].mean().mul(100).reset_index(name="pct_finde")
    return {
        "gasto_usuario_mes": gasto_usuario_mes,
        "tickets_usuario_mes": tickets_usuario_mes,
        "usuario_autopista_mes": usuario_autopista_mes,
        "metodos_usuario_mes": metodos_usuario_mes,
        "dias_mediana": dias_mediana,
        "pct_finde_usuario": pct_finde_usuario,
    }

def kpis_empresa_toll(df: pd.DataFrame):
    if df.empty: return {}
    dfe = df.copy()
    dfe["empresa"] = dfe.get("empresaNombre", "EMPRESA_UNICA")
    if "idTicket" not in dfe.columns:
        if "referencia" in dfe.columns: dfe["idTicket"] = dfe["referencia"].astype(str)
        else:
            dfe = dfe.reset_index().rename(columns={"index":"idTicket"})
            dfe["idTicket"] = dfe["idTicket"].astype(str)
    gasto_mes_emp = dfe.groupby(["empresa","mes"])["importe"].sum().reset_index().rename(columns={"importe":"gasto_mes"})
    tickets_mes_emp = dfe.groupby(["empresa","mes"])["idTicket"].nunique().reset_index().rename(columns={"idTicket":"tickets_mes"})
    emp_autopista_mes = dfe.groupby(["empresa","mes","autopista"])["importe"].agg(gasto_autopista_mes="sum", tickets_autopista_mes="count").reset_index()
    emp_autopista_mes["coste_medio_ticket"] = emp_autopista_mes["gasto_autopista_mes"] / emp_autopista_mes["tickets_autopista_mes"].replace(0, pd.NA)
    emp_autopista_mes["pct_gasto_empresa_mes"] = (
        100 * emp_autopista_mes["gasto_autopista_mes"] /
        emp_autopista_mes.groupby(["empresa","mes"])["gasto_autopista_mes"].transform("sum")
    )
    met_emp_mes = dfe.groupby(["empresa","mes","formaPago"])["idTicket"].nunique().reset_index(name="tickets")
    met_emp_mes["pct"] = 100 * met_emp_mes["tickets"] / met_emp_mes.groupby(["empresa","mes"])["tickets"].transform("sum")
    gasto_total_emp = dfe.groupby("empresa")["importe"].sum().reset_index().rename(columns={"importe":"gasto_total_periodo"})
    vehiculos_emp = dfe.groupby("empresa")["idUsuario"].nunique().reset_index().rename(columns={"idUsuario":"num_vehiculos"})
    gasto_medio_veh = dfe.groupby(["empresa","idUsuario"])["importe"].sum().groupby("empresa").mean().reset_index().rename(columns={"importe":"gasto_medio_por_vehiculo"})
    pct_finde_emp = dfe.groupby("empresa")["is_weekend"].mean().mul(100).reset_index().rename(columns={"is_weekend":"pct_finde"})
    return {
        "gasto_mes_emp": gasto_mes_emp,
        "tickets_mes_emp": tickets_mes_emp,
        "emp_autopista_mes": emp_autopista_mes,
        "met_emp_mes": met_emp_mes,
        "gasto_total_emp": gasto_total_emp,
        "vehiculos_emp": vehiculos_emp,
        "gasto_medio_veh": gasto_medio_veh,
        "pct_finde_emp": pct_finde_emp,
    }

# ==============================
# Endpoints
# ==============================
@app.get("/health")
def health():
    """Comprobación rápida."""
    try:
        return {
            "db": DB_NAME,
            "collections": {
                COL_FUEL: coll_fuel.estimated_document_count(),
                COL_EV:   coll_ev.estimated_document_count(),
                COL_TOLL: coll_toll.estimated_document_count()
            }
        }
    except Exception as e:
        return {"status": "degraded", "error": repr(e)}

@app.get("/debug/peek")
def debug_peek(n: int = 3):
    """Echa un vistazo rápido a columnas y recuentos."""
    info = {}
    for name, coll in [(COL_FUEL, coll_fuel), (COL_EV, coll_ev), (COL_TOLL, coll_toll)]:
        df = load_df_mongo(coll, {})
        info[name] = {
            "docs": len(df),
            "cols": list(df.columns),
            "sample": df.head(n).to_dict(orient="records")
        }
    return info

@app.get("/kpis/combustible")
def ep_kpis_combustible(
    start_date: str|None = Query(None, description="YYYY-MM-DD (fechaEmision)"),
    end_date:   str|None = Query(None, description="YYYY-MM-DD (fechaEmision)"),
    empresa:    str|None = Query(None),
    idUsuario:  str|None = Query(None),
):
    try:
        filt = _build_filter_fechas_cabecera(start_date, end_date)
        if empresa:   filt["empresaNombre"] = empresa
        if idUsuario: filt["idUsuario"] = idUsuario

        df = load_df_mongo(coll_fuel, filt)
        if df.empty: return {"usuario": {}, "empresa": {}}

        df = add_time_cols_fuel_ev(df)
        df["lineas_parsed"] = df.get("lineas", pd.Series([[]]*len(df))).apply(parse_lineas)
        df_lines = explode_fuel_lines(df)
        if df_lines.empty: return {"usuario": {}, "empresa": {}}

        return {"usuario": _ser(kpis_usuario_fuel(df, df_lines)),
                "empresa": _ser(kpis_empresa_fuel(df, df_lines))}
    except Exception as e:
        print("ERROR /kpis/combustible:", repr(e))
        return {"usuario": {}, "empresa": {}}

@app.get("/kpis/ev")
def ep_kpis_ev(
    start_date: str|None = Query(None, description="YYYY-MM-DD (fechaEmision)"),
    end_date:   str|None = Query(None, description="YYYY-MM-DD (fechaEmision)"),
    empresa:    str|None = Query(None),
    idUsuario:  str|None = Query(None),
):
    try:
        filt = _build_filter_fechas_cabecera(start_date, end_date)
        if empresa:   filt["empresaNombre"] = empresa
        if idUsuario: filt["idUsuario"] = idUsuario

        df = load_df_mongo(coll_ev, filt)
        if df.empty: return {"usuario": {}, "empresa": {}}

        df = add_time_cols_fuel_ev(df)
        df["lineas_parsed"] = df.get("lineas", pd.Series([[]]*len(df))).apply(parse_lineas)
        df_lines = explode_ev_lines(df)
        if df_lines.empty: return {"usuario": {}, "empresa": {}}

        return {"usuario": _ser(kpis_usuario_ev(df, df_lines)),
                "empresa": _ser(kpis_empresa_ev(df, df_lines))}
    except Exception as e:
        print("ERROR /kpis/ev:", repr(e))
        return {"usuario": {}, "empresa": {}}

@app.get("/kpis/peaje")
def ep_kpis_peaje(
    start_date: str|None = Query(None, description="YYYY-MM-DD (fechaHora)"),
    end_date:   str|None = Query(None, description="YYYY-MM-DD (fechaHora)"),
    empresa:    str|None = Query(None),
    idUsuario:  str|None = Query(None),
):
    try:
        filt = _build_filter_fechas_toll(start_date, end_date)
        if empresa:   filt["empresaNombre"] = empresa
        if idUsuario: filt["idUsuario"] = idUsuario

        df = load_df_mongo(coll_toll, filt)
        if df.empty: return {"usuario": {}, "empresa": {}}

        if "importe" not in df.columns:
            cand_imp = [c for c in df.columns if any(p in c.lower() for p in ["importe","total","precio","coste","amount","valor","pago"])]
            if cand_imp:
                ser = pd.to_numeric(df[cand_imp[0]], errors="coerce")
                ser = ser.where(ser.notna(), df[cand_imp[0]].apply(_to_num_eur))
                df["importe"] = ser
            else:
                df["importe"] = np.nan

        df = add_time_cols_toll(df)

        return {"usuario": _ser(kpis_usuario_toll(df)),
                "empresa": _ser(kpis_empresa_toll(df))}
    except Exception as e:
        print("ERROR /kpis/peaje:", repr(e))
        return {"usuario": {}, "empresa": {}}

@app.get("/")
def root():
    return {"message": "API KPIs lista. Endpoints: /kpis/combustible, /kpis/ev, /kpis/peaje", "health": "/health", "debug": "/debug/peek"}
