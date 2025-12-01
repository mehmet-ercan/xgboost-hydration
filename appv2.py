from flask import Flask, render_template, request, jsonify
from pathlib import Path
import json
import joblib
import pandas as pd
from feature_engineering import fe_transform

# ============================================================
# FLASK SETUP
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))

# ============================================================
# MODEL VE SAMPLE DATA YÜKLEME
# ============================================================
try:
    model = joblib.load(BASE_DIR / "hydrate_model_pipeline.pkl")
except Exception as e:
    print("\nModel dosyası yüklenirken hata oluştu!\n")
    print(str(e))
    input("\nHata mesajını okuduktan sonra Enter tuşuna basarak çıkabilirsiniz...")
    raise SystemExit

try:
    with open(BASE_DIR / "data_sample.json", "r", encoding="utf-8") as f:
        sample_input = json.load(f)
except Exception as e:
    print("\nÖrnek veri dosyası (data_sample.json) okunurken hata oluştu!\n")
    print(str(e))
    input("\nHata mesajını okuduktan sonra Enter tuşuna basarak çıkabilirsiniz...")
    raise SystemExit

# Feature isimleri (sadece ham kolonlar - 16 adet)
feature_names = list(sample_input.keys())
defaults = sample_input

# ============================================================
# WEB FORM ENDPOINT
# ============================================================
@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    user_values = defaults.copy()

    if request.method == "POST":
        try:
            user_inputs = {}

            for f in feature_names:
                if f == "H2O":
                    user_values[f] = 0.07
                    user_inputs[f] = 0.07
                    continue

                val = request.form.get(f, "")
                if val == "":
                    user_values[f] = float(defaults[f])
                    user_inputs[f] = float(defaults[f])
                else:
                    user_values[f] = float(val)
                    user_inputs[f] = float(val)

            input_df = pd.DataFrame([user_inputs])
            y_pred = model.predict(input_df)[0]
            prediction = round(float(y_pred), 2)  # ← 2 ondalık

        except Exception as e:
            prediction = f"Hata: {e}"

    return render_template(
        "index.html",
        feature_names=feature_names,
        defaults=defaults,
        prediction=prediction,
        user_values=user_values
    )

# ============================================================
# API: FEATURE SCHEMA
# ============================================================
@app.route("/api/feature-schema", methods=["GET"])
def feature_schema():
    return jsonify(
        {
            "feature_names": feature_names,
            "defaults": defaults,
            "note": "POST /api/predict endpoint'ine bu alanlari gonderin. "
                    "Eksik alanlar varsayilanlarla doldurulur.",
        }
    )

# ============================================================
# API: PREDICT
# ============================================================
@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        payload = request.get_json(force=True)
        if payload is None:
            return jsonify({"error": "JSON bekleniyor."}), 400
            
        feats = payload.get("features", payload)
        used = {}
        missing = []
        
        for name in feature_names:
            raw = feats.get(name)
            if raw is None or raw == "":
                used[name] = float(defaults[name])
                missing.append(name)
            else:
                try:
                    used[name] = float(raw)
                except:
                    used[name] = float(defaults[name])
        
        input_df = pd.DataFrame([used])
        y_pred = model.predict(input_df)[0]
        
        resp = {
            "prediction": round(float(y_pred), 2),  # ← 2 ondalık
            "units": "C",
            "used_features": used
        }
        if missing:
            resp["filled_with_defaults"] = missing
            
        return jsonify(resp)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/curve", methods=["GET", "POST"])
def curve():
    curve_data = None
    user_values = defaults.copy()
    
    if request.method == "POST":
        try:
            # Kullanıcıdan değerleri al
            p_min = float(request.form.get("p_min", 10))
            p_max = float(request.form.get("p_max", 100))
            n_points = int(request.form.get("n_points", 20))
            
            # Kompozisyon değerlerini al
            comp_inputs = {}
            for f in feature_names:
                if f == "Pc":
                    continue  # Pc'yi döngüde hesaplayacağız
                elif f == "H2O":
                    comp_inputs[f] = 0.07
                    user_values[f] = 0.07
                else:
                    val = request.form.get(f, "")
                    if val == "":
                        comp_inputs[f] = float(defaults[f])
                        user_values[f] = float(defaults[f])
                    else:
                        comp_inputs[f] = float(val)
                        user_values[f] = float(val)
            
            # Basınç aralığını oluştur
            pressures = []
            step = (p_max - p_min) / (n_points - 1)
            for i in range(n_points):
                pressures.append(p_min + i * step)
            
            # Her basınç için tahmin yap
            temperatures = []
            for p in pressures:
                input_data = comp_inputs.copy()
                input_data["Pc"] = p
                input_df = pd.DataFrame([input_data])
                temp = model.predict(input_df)[0]
                temperatures.append(float(temp))
            
            curve_data = {
                "pressures": pressures,
                "temperatures": temperatures,
                "p_min": p_min,
                "p_max": p_max,
                "n_points": n_points
            }
            
        except Exception as e:
            curve_data = {"error": str(e)}
    
    return render_template(
        "curve.html",
        feature_names=[f for f in feature_names if f != "Pc"],  # Pc'yi çıkar
        defaults=defaults,
        user_values=user_values,
        curve_data=curve_data
    )

@app.route("/api/predict-curve", methods=["POST"])
def api_predict_curve():
    try:
        payload = request.get_json(force=True)
        
        p_min = float(payload.get("p_min", 10))
        p_max = float(payload.get("p_max", 100))
        n_points = int(payload.get("n_points", 20))
        composition = payload.get("composition", {})
        
        # Kompozisyonu defaults ile doldur
        comp = defaults.copy()
        for key, val in composition.items():
            if key != "Pc":
                comp[key] = float(val)
        
        # Basınç aralığı
        pressures = []
        step = (p_max - p_min) / (n_points - 1)
        for i in range(n_points):
            pressures.append(p_min + i * step)
        
        # Tahminler
        temperatures = []
        for p in pressures:
            comp["Pc"] = p
            input_df = pd.DataFrame([comp])
            temp = model.predict(input_df)[0]
            temperatures.append(float(temp))
        
        return jsonify({
            "pressures": pressures,
            "temperatures": temperatures,
            "p_min": p_min,
            "p_max": p_max,
            "n_points": n_points
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# CORS (OPSIYONEL)
# ============================================================
try:
    from flask_cors import CORS
    CORS(app)
except Exception:
    # flask-cors yoksa sorun değil
    pass

# ============================================================
# SUNUCU BAŞLATMA
# ============================================================
if __name__ == "__main__":
    try:
        from waitress import serve
        # PRODUCTION için:
        # serve(app, host="0.0.0.0", port=5000)
        
        # DEVELOPMENT için:
        app.run(debug=True, use_reloader=False)
    except Exception as e:
        print("\nUygulama başlatılırken bir hata oluştu!\n")
        print(str(e))
        input("\nHata mesajını okuduktan sonra Enter tuşuna basarak çıkabilirsiniz...")