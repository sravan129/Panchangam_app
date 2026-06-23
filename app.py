from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import swisseph as swe
from astral import LocationInfo
from astral.sun import sun
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
swe.set_sid_mode(swe.SIDM_LAHIRI)
IST = ZoneInfo("Asia/Kolkata")
CITIES = {
    "hyderabad": ("హైదరాబాద్", 17.385, 78.4867),
    "vijayawada": ("విజయవాడ", 16.5062, 80.648),
    "visakhapatnam": ("విశాఖపట్నం", 17.6868, 83.2185),
    "tirupati": ("తిరుపతి", 13.6288, 79.4192),
    "warangal": ("వరంగల్", 17.9689, 79.5941),
}
TITHIS = ["శుక్ల పాడ్యమి","శుక్ల విదియ","శుక్ల తదియ","శుక్ల చవితి","శుక్ల పంచమి","శుక్ల షష్ఠి","శుక్ల సప్తమి","శుక్ల అష్టమి","శుక్ల నవమి","శుక్ల దశమి","శుక్ల ఏకాదశి","శుక్ల ద్వాదశి","శుక్ల త్రయోదశి","శుక్ల చతుర్దశి","పౌర్ణమి","కృష్ణ పాడ్యమి","కృష్ణ విదియ","కృష్ణ తదియ","కృష్ణ చవితి","కృష్ణ పంచమి","కృష్ణ షష్ఠి","కృష్ణ సప్తమి","కృష్ణ అష్టమి","కృష్ణ నవమి","కృష్ణ దశమి","కృష్ణ ఏకాదశి","కృష్ణ ద్వాదశి","కృష్ణ త్రయోదశి","కృష్ణ చతుర్దశి","అమావాస్య"]
NAKSHATRAS = ["అశ్విని","భరణి","కృత్తిక","రోహిణి","మృగశిర","ఆరుద్ర","పునర్వసు","పుష్యమి","ఆశ్లేష","మఖ","పుబ్బ","ఉత్తర","హస్త","చిత్త","స్వాతి","విశాఖ","అనూరాధ","జ్యేష్ఠ","మూల","పూర్వాషాఢ","ఉత్తరాషాఢ","శ్రవణం","ధనిష్ఠ","శతభిషం","పూర్వాభాద్ర","ఉత్తరాభాద్ర","రేవతి"]
YOGAS = ["విష్కంభ","ప్రీతి","ఆయుష్మాన్","సౌభాగ్య","శోభన","అతిగండ","సుకర్మ","ధృతి","శూల","గండ","వృద్ధి","ధ్రువ","వ్యాఘాత","హర్షణ","వజ్ర","సిద్ధి","వ్యతీపాత","వరీయాన్","పరిఘ","శివ","సిద్ధ","సాధ్య","శుభ","శుక్ల","బ్రహ్మ","ఇంద్ర","వైధృతి"]
WEEKDAYS = ["సోమవారం","మంగళవారం","బుధవారం","గురువారం","శుక్రవారం","శనివారం","ఆదివారం"]
MONTHS = ["","జనవరి","ఫిబ్రవరి","మార్చి","ఏప్రిల్","మే","జూన్","జూలై","ఆగస్టు","సెప్టెంబర్","అక్టోబర్","నవంబర్","డిసెంబర్"]

def jd(moment):
    utc = moment.astimezone(ZoneInfo("UTC"))
    return swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60 + utc.second / 3600)

def angle(moment, kind):
    j = jd(moment)
    ay = swe.get_ayanamsa_ut(j)
    flags = swe.FLG_MOSEPH | swe.FLG_SPEED
    sl = (swe.calc_ut(j, swe.SUN, flags)[0][0] - ay) % 360
    ml = (swe.calc_ut(j, swe.MOON, flags)[0][0] - ay) % 360
    if kind in ("tithi", "karana"): return (ml - sl) % 360
    if kind == "nakshatra": return ml
    return (sl + ml) % 360

def index(moment, kind, width): return int(angle(moment, kind) // width)

def boundary(moment, kind, width, direction):
    target, inside, outside = index(moment, kind, width), moment, moment
    for _ in range(20):
        outside += timedelta(hours=3 * direction)
        if index(outside, kind, width) != target: break
        inside = outside
    lo, hi = sorted((inside, outside))
    for _ in range(32):
        mid = lo + (hi - lo) / 2
        same = index(mid, kind, width) == target
        if direction > 0:
            if same: lo = mid
            else: hi = mid
        else:
            if same: hi = mid
            else: lo = mid
    return hi if direction > 0 else lo

def fmt(moment): return moment.astimezone(IST).strftime("%I:%M %p").lstrip("0")

def karana_name(i):
    if i == 0: return "కింస్తుఘ్న"
    if i >= 57: return ["శకుని","చతుష్పాద","నాగవ"][i - 57]
    return ["బవ","బాలవ","కౌలవ","తైతుల","గరజ","వణిజ","విష్టి"][(i - 1) % 7]

def element(ref, kind, width, names=None):
    i = index(ref, kind, width)
    return {"name": karana_name(i) if kind == "karana" else names[i], "start": fmt(boundary(ref, kind, width, -1)), "end": fmt(boundary(ref, kind, width, 1))}

def period(rise, setting, segment):
    unit = (setting - rise) / 8
    return {"start": fmt(rise + unit * segment), "end": fmt(rise + unit * (segment + 1))}

@app.get("/")
def home(): return render_template("index.html", cities=CITIES)

@app.get("/api/panchangam")
def panchangam():
    try:
        selected = date.fromisoformat(request.args.get("date", date.today().isoformat()))
        city = request.args.get("city", "hyderabad")
        name, lat, lon = CITIES.get(city, CITIES["hyderabad"])
        solar = sun(LocationInfo(name, "India", "Asia/Kolkata", lat, lon).observer, date=selected, tzinfo=IST)
        rise, setting, weekday = solar["sunrise"], solar["sunset"], selected.weekday()
        ref = rise + timedelta(minutes=1)
        return jsonify({
            "dateLabel": f"{selected.day} {MONTHS[selected.month]} {selected.year}, {WEEKDAYS[weekday]}",
            "location": name, "sunrise": fmt(rise), "sunset": fmt(setting),
            "tithi": element(ref, "tithi", 12, TITHIS),
            "nakshatra": element(ref, "nakshatra", 360/27, NAKSHATRAS),
            "yoga": element(ref, "yoga", 360/27, YOGAS),
            "karana": element(ref, "karana", 6),
            "rahuKalam": period(rise, setting, [1,6,4,5,3,2,7][weekday]),
            "yamagandam": period(rise, setting, [3,2,1,0,6,5,4][weekday]),
            "gulika": period(rise, setting, [5,4,3,2,1,0,6][weekday]),
        })
    except ValueError as exc: return jsonify({"error": str(exc)}), 400

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)