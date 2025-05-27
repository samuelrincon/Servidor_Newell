import requests
from bs4 import BeautifulSoup
import threading
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
import webbrowser
from collections import defaultdict
import os 

app = Flask(__name__)

# Global configuration
API_URL = "https://reports.intouchcx.com/reports/lib/getRealtimeManagementFull.asp"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "text/html, */*; q=0.01",
    "Referer": "https://reports.intouchcx.com/reports/custom/newellbrands/realtimemanagementfull.asp?threshold=180&tzoffset=est",
    "Origin": "https://reports.intouchcx.com"
}

PAYLOAD = {
    'split': '3900,3901,3902,3903,3904,3905,3906,3907,3908,3909,3910,3911,3912,3913,3914,3915,3916,3917,3918,3919,3920,3921,3922,3923,3924,3925,3926,3927,3928,3929,3930,3931,3932,3933,3934,3935,3936,3937,3938,3939,3940,3941,3942,3943,3944,3945,3946,3947,3948,3949,3950,3951,3952,3953,3954,3955,3956,3957,3958,3959,3960,3961,3962,3963,3964,3965,3966,3967,3968,3969,3970,3971,3972,3973',
    'firstSortCol': 'FullName',
    'firstSortDir': 'ASC',
    'secondSortCol': 'FullName',
    'secondSortDir': 'ASC',
    'reason': 'all',
    'state': 'all',
    'timezone': '1',
    'altSL': '',
    'threshold': '180',
    'altSLThreshold': '0',
    'acdAlert': '',
    'acwAlert': '',
    'holdAlert': '',
    'slAlert': '',
    'asaAlert': ''
}

# Make ALERT_TIMES mutable
ALERT_TIMES = {
    "Long Call": 360,
    "Extended Lunch": 3600,
    "Long ACW": 120,
    "Extended Break": 900,
    "IT Issue": 30,
    "Long Hold": 120
}

SKILLS_MAP = {
    '3900': 'Coleman (3900)',
    '3901': 'Contigo (3901)',
    '3902': 'Bubba (3902)',
    '3903': 'Avex (3903)',
    '3904': 'Margaritaville (3904)',
    '3905': 'MrCoffee (3905)',
    '3906': 'Martello (3906)',
    '3907': 'FoodSaver (3907)',
    '3908': 'Oster (3908)',
    '3909': 'lVillaWare (3909)',
    '3910': 'RapidBath (3910)',
    '3911': 'SkyBar (3911)',
    '3912': 'Sunbeam (3912)',
    '3913': 'SbExec (3913)',
    '3914': 'MagicChef (3914)',
    '3915': 'HGS English (3915)',
    '3916': 'HGS French (3916)',
    '3917': 'Order (3917)',
    '3918': 'HGS Spanish (3918)',
    '3919': 'Oster Spanish (3919)',
    '3920': 'Sunbeam French (3920)',
    '3921': 'X-acto (3921)',
    '3922': 'elmers/Krazy Glue (3922)',
    '3923': 'Loew Cornell (3923)',
    '3924': 'OfficeProducts (3924)',
    '3925': 'Rubbermaid (3925)',
    '3926': 'Calphalon (3926)',
    '3927': 'CalphalonRecall (3927)',
    '3928': 'OsterProfessional (3928)',
    '3929': 'O&R (3929)',
    '3930': 'Ball (3930)',
    '3931': 'Bernardin (English) (3931)',
    '3932': 'Bernardin (French) (3932)',
    '3933': 'Writting French (3933)',
    '3934': 'Rubbermaid French (3934)',
    '3935': 'O&R English (3935)',
    '3936': 'O&R French (3936)',
    '3937': 'O&R Spanish (3937)',
    '3938': 'O&R New Order (3938)',
    '3939': 'O&R Production Support (3939)',
    '3940': 'O&R Replacement Parts (3940)',
    '3941': 'O&R Warranty (3941)',
    '3942': 'O&R Other Product (3942)',
    '3943': 'Home Fragrance (3943)',
    '3944': 'O&R Fraud (3944)',
    '3945': 'APAC ANZ A&C (3945)',
    '3946': 'APAC ANZ A&C Recall (3946)',
    '3947': 'APAC ANZ Baby (3947)',
    '3948': 'Beverage Warranty (3948)',
    '3949': 'CTI Test (3949)',
    '3950': 'NB HomeFragrance Chesapeake (3950)',
    '3951': 'A&C 1 Escalations (3951)',
    '3952': 'A&C 2 Escalations (3952)',
    '3953': 'Beverages Escalations (3953)',
    '3954': 'Calphalon Escalations (3954)',
    '3955': 'Food Escalations (3955)',
    '3956': 'Home Fragrance Escalations (3956)',
    '3957': 'O&R Escalations (3957)',
    '3958': 'Writing Escalations (3958)',
    '3959': 'Oster Pro Escalations (3959)',
    '3960': 'APAC Escalations (3960)',
    '3961': 'A&C1 Redux (3961)',
    '3962': 'A&C2 Redux (3962)',
    '3963': 'Beverage Redux (3963)',
    '3964': 'Calphalon Redux (3964)',
    '3965': 'Food Redux (3965)',
    '3966': 'Home Fragrance Redux (3966)',
    '3967': 'O&R Redux (3967)',
    '3968': 'Oster Pro Redux (3968)',
    '3969': 'Writing Redux (3969)',
    '3970': 'A&C APAC Redux (3970)',
    '3971': 'Yankee Candle New Orders (3971)',
    '3972': 'Foodsaver French (3972)',
    '3973': 'Friday Collective (3973)'
}

# Variables globales para almacenar datos
current_data = {
    'agents': [],
    'alerts': [],
    'aux_status': [],
    'queue_data': [],
    'total_calls': 0,
    'active_skills': set(),
    'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'queue_metrics': {}
}

# Add route to update alert times
@app.route('/update_alert_times', methods=['POST'])
def update_alert_times():
    global ALERT_TIMES
    new_times = request.json
    for key, value in new_times.items():
        if key in ALERT_TIMES:
            try:
                ALERT_TIMES[key] = int(value)
            except ValueError:
                return jsonify({'error': f'Invalid value for {key}'}), 400
    return jsonify({'success': True, 'new_times': ALERT_TIMES})

def time_to_seconds(time_str):
    try:
        parts = list(map(int, time_str.split(":")))
        if len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        return 0
    except (ValueError, AttributeError):
        return 0

def fetch_data():
    try:
        response = requests.post(API_URL, data=PAYLOAD, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching data: {str(e)}")
        return None

def parse_data(html_content):
    if not html_content:
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    agents = []
    alerts = []
    aux_status = []
    queue_data = []
    total_calls = 0
    active_skills = set()
    queue_metrics = {}
    
    # Parse queue metrics first
    queue_rows = soup.find_all('tr', class_='data')
    for row in queue_rows:
        skill_cell = row.find('td', colspan='3', class_='nowrap')
        if skill_cell and 'Skill Name' not in skill_cell.get_text():
            skill_name = skill_cell.get_text(strip=True)
            skill_id = ""
            if "(" in skill_name and ")" in skill_name:
                skill_id = skill_name.split("(")[-1].split(")")[0].strip()
            
            if skill_id in SKILLS_MAP:
                cells = skill_cell.find_all_next('td', limit=20)
                if len(cells) >= 16:
                    calls_in_queue = cells[0].get_text(strip=True)
                    offered = cells[1].get_text(strip=True)
                    answered = cells[2].get_text(strip=True)
                    transfers = cells[3].get_text(strip=True)
                    true_abn = cells[4].get_text(strip=True)
                    short_abn = cells[5].get_text(strip=True)
                    oldest_call = cells[6].get_text(strip=True)
                    max_delay = cells[7].get_text(strip=True)
                    asa = cells[8].get_text(strip=True)
                    aqt = cells[9].get_text(strip=True)
                    service_level = cells[10].get_text(strip=True)
                    rt_sl = cells[11].get_text(strip=True)
                    staffed = cells[12].get_text(strip=True)
                    available = cells[13].get_text(strip=True)
                    acw = cells[14].get_text(strip=True)
                    acd = cells[15].get_text(strip=True)
                    aux = cells[16].get_text(strip=True)
                    other = cells[17].get_text(strip=True)
                    
                    if calls_in_queue.isdigit():
                        total_calls += int(calls_in_queue)
                    
                    queue_metrics[skill_id] = {
                        'offered': offered,
                        'answered': answered,
                        'transfers': transfers,
                        'true_abn': true_abn,
                        'short_abn': short_abn,
                        'asa': asa,
                        'aqt': aqt,
                        'service_level': service_level,
                        'acw': acw,
                        'acd': acd,
                        'aux': aux,
                        'other': other
                    }
                    
                    queue_data.append({
                        'skill_id': skill_id,
                        'skill_name': SKILLS_MAP[skill_id],
                        'calls_in_queue': calls_in_queue,
                        'staffed': staffed,
                        'available': available,
                        'oldest_call': oldest_call,
                        'rt_sl': rt_sl
                    })
    
    # Parse agent data
    rows = soup.find_all('tr', class_='data')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 9:
            avaya_id = cols[0].text.strip()
            full_name = cols[1].text.strip()
            state = cols[2].text.strip().upper()
            reason_code = cols[3].text.strip().upper()
            active_call = cols[4].text.strip()
            call_duration = cols[5].text.strip()
            skill_name = cols[6].text.strip()
            time_in_state = cols[7].text.strip()

            # Extract skill ID
            skill_id = ""
            if "(" in skill_name and ")" in skill_name:
                skill_id = skill_name.split("(")[-1].split(")")[0].strip()
                active_skills.add(skill_id)

            call_duration_sec = time_to_seconds(call_duration)
            time_in_state_sec = time_to_seconds(time_in_state)

            # Check for alerts
            alert = None
            alert_time = None
            
            if state == "ACD" and call_duration_sec > ALERT_TIMES["Long Call"]:
                alert = "Long Call"
                alert_time = call_duration
            elif "LUNCH" in reason_code and time_in_state_sec > ALERT_TIMES["Extended Lunch"]:
                alert = "Extended Lunch"
                alert_time = time_in_state
            elif state == "ACW" and time_in_state_sec > ALERT_TIMES["Long ACW"]:
                alert = "Long ACW"
                alert_time = time_in_state
            elif state == "AUX" and "BREAK" in reason_code and time_in_state_sec > ALERT_TIMES["Extended Break"]:
                alert = "Extended Break"
                alert_time = time_in_state
            elif state == "AUX" and "IT ISSUE" in reason_code and time_in_state_sec > ALERT_TIMES["IT Issue"]:
                alert = "IT Issue"
                alert_time = time_in_state
            elif state == "AUX" and "DEFAULT" in reason_code:
                alert = "Default Detected"
                alert_time = time_in_state
            elif state == "OTHER (HOLD)" and time_in_state_sec > ALERT_TIMES["Long Hold"]:
                alert = "Long Hold"
                alert_time = time_in_state

            if alert:
                alerts.append({
                    'type': alert,
                    'avaya_id': avaya_id,
                    'name': full_name,
                    'time': alert_time,
                    'skill': skill_name
                })

            # Check for AUX status
            aux_codes = ["EMAIL 1", "EMAIL 2", "CSR LEVEL II", "QUALITY COACHING",
                       "TL INTERN", "FLOOR SUPPORT", "CHAT", "BRAND SPECIALIST", "PERFORMANCE ANALYST",
                        "BACK OFFICE", "TRAINING", "OUTBOUND/CALLBACK", "PROJECT WORK", "RESEARCH"]
            if state == "AUX" and reason_code in aux_codes:
                aux_status.append({
                    'reason': reason_code,
                    'avaya_id': avaya_id,
                    'name': full_name,
                    'time': time_in_state,
                    'skill': skill_name
                })

            agents.append({
                'avaya_id': avaya_id,
                'name': full_name,
                'state': state,
                'reason': reason_code,
                'active_call': active_call,
                'call_duration': call_duration,
                'skill': skill_name,
                'time_in_state': time_in_state,
                'skill_id': skill_id
            })
    
    return {
        'agents': agents,
        'alerts': alerts,
        'aux_status': aux_status,
        'queue_data': sorted(queue_data, key=lambda x: x['skill_name']),
        'queue_data_with_calls': sorted(queue_data, key=lambda x: x['skill_name']),
        'total_calls': total_calls,
        'active_skills': active_skills,
        'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'queue_metrics': queue_metrics
    }

def update_data():
    while True:
        html_content = fetch_data()
        if html_content:
            data = parse_data(html_content)
            if data:
                current_data.update(data)
        time.sleep(15)

# Iniciar el hilo de actualización de datos
update_thread = threading.Thread(target=update_data, daemon=True)
update_thread.start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newell Brands Voice Monitoring</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #6A0DAD;
            --primary-light: #8A2BE2;
            --secondary-color: #0056A7;
            --alert-color: #FF5252;
            --aux-color: #9370DB;
            --background: #F6F0FF;
            --card-bg: #FFFFFF;
            --text-dark: #333333;
            --text-light: #FFFFFF;
            --border-radius: 8px;
            --box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background-color: var(--background);
            color: var(--text-dark);
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
            color: var(--text-light);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--box-shadow);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo {
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: 1px;
            background: linear-gradient(to right, #FFFFFF, #E0E0E0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .newell-logo {
            font-size: 1.5rem;
            font-weight: 600;
            background: linear-gradient(to right, #FFFFFF, #B3E5FC);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius);
            border: 2px solid rgba(255, 255, 255, 0.3);
        }
        
        .container {
            padding: 2rem;
            max-width: 1800px;
            margin: 0 auto;
        }
        
        .dashboard-title {
            text-align: center;
            color: var(--primary-color);
            margin-bottom: 2rem;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .notification {
            background-color: var(--alert-color);
            color: var(--text-light);
            padding: 1rem;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 600;
            border-radius: var(--border-radius);
            display: none;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .tabs {
            display: flex;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--primary-color);
        }
        
        .tab {
            padding: 0.8rem 1.5rem;
            cursor: pointer;
            background-color: #D0B5FF;
            margin-right: 0.5rem;
            border-radius: var(--border-radius) var(--border-radius) 0 0;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .tab:hover {
            background-color: var(--primary-light);
            color: white;
        }
        
        .tab.active {
            background-color: var(--primary-color);
            color: white;
        }
        
        .tab-content {
            display: none;
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .tab-content.active {
            display: block;
        }
        
        .card {
            background-color: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 2rem;
            background-color: var(--card-bg);
            box-shadow: var(--box-shadow);
            border-radius: var(--border-radius);
            overflow: hidden;
        }
        
        th, td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        th {
            background-color: var(--primary-color);
            color: var(--text-light);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.5px;
        }
        
        tr:nth-child(even) {
            background-color: rgba(214, 188, 255, 0.2);
        }
        
        tr:hover {
            background-color: rgba(214, 188, 255, 0.3);
        }
        
        .calls-warning {
            background-color: rgba(255, 82, 82, 0.2) !important;
        }
        
        .sl-warning {
            background-color: rgba(255, 82, 82, 0.4) !important;
        }
        
        .both-warning {
            background-color: rgba(255, 82, 82, 0.6) !important;
            color: white;
        }
        
        .button-container {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }
        
        .button {
            background-color: var(--primary-color);
            color: var(--text-light);
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: var(--border-radius);
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .button:hover {
            background-color: var(--primary-light);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        .button:active {
            transform: translateY(0);
        }
        
        .button.alert {
            background-color: var(--alert-color);
        }
        
        .button.aux {
            background-color: var(--aux-color);
        }
        
        .button.secondary {
            background-color: var(--secondary-color);
        }
        
        .alert-window {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: var(--card-bg);
            padding: 2rem;
            border-radius: var(--border-radius);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            width: 80%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            display: none;
        }
        
        .alert-window h2 {
            color: var(--alert-color);
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .alert-window h2 svg {
            width: 1.5rem;
            height: 1.5rem;
        }
        
        .alert-item {
            margin-bottom: 1rem;
            padding: 1rem;
            background-color: rgba(255, 82, 82, 0.1);
            border-radius: var(--border-radius);
            border-left: 4px solid var(--alert-color);
        }
        
        .aux-item {
            border-left: 4px solid var(--aux-color);
            background-color: rgba(147, 112, 219, 0.1);
        }
        
        .close-button {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text-dark);
        }
        
        .last-updated {
            text-align: right;
            font-style: italic;
            color: #666;
            font-size: 0.9rem;
            margin-top: 1rem;
        }
        
        .overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 999;
            display: none;
        }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
            background-color: var(--alert-color);
            color: white;
            margin-left: 0.5rem;
        }
        
        .aux-badge {
            background-color: var(--aux-color);
        }
        
        .skill-tag {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: var(--border-radius);
            background-color: rgba(106, 13, 173, 0.1);
            color: var(--primary-color);
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }
        
        .settings-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: var(--card-bg);
            padding: 2rem;
            border-radius: var(--border-radius);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            width: 80%;
            max-width: 600px;
            display: none;
        }
        
        .settings-form {
            display: grid;
            gap: 1rem;
        }
        
        .form-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            align-items: center;
            gap: 1rem;
        }
        
        .form-group label {
            font-weight: 600;
        }
        
        .form-group input {
            padding: 0.5rem;
            border: 1px solid #ccc;
            border-radius: var(--border-radius);
            font-size: 1rem;
        }
        
        .save-button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 0.8rem;
            border-radius: var(--border-radius);
            cursor: pointer;
            font-weight: 600;
            margin-top: 1rem;
            width: 100%;
        }
        
        .save-button:hover {
            background-color: var(--primary-light);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header {
                flex-direction: column;
                gap: 1rem;
                padding: 1rem;
            }
            
            .logo-container {
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .button-container {
                flex-direction: column;
            }
            
            table {
                display: block;
                overflow-x: auto;
            }
            
            .alert-window {
                width: 95%;
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-container">
            <div class="logo">Int
ouchCX</div>
            <div class="newell-logo">Newell Brands</div>
        </div>
        <div class="last-updated">Last updated: {{ last_update }}</div>
    </div>
    
    <div class="container">
        <h1 class="dashboard-title">Voice Monitoring Dashboard</h1>
        
        <div class="notification" id="queue-notification">
            ⚠️ {{ total_calls }} calls in queue! Click 'View Queue' for details.
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('agents')">Agent Dashboard</div>
            <div class="tab" onclick="switchTab('queue')">Queue Dashboard</div>
        </div>
        
        <div class="tab-content active" id="agents-tab">
            <div class="button-container">
                <button class="button alert" onclick="showAlerts()">
    View Alerts
    {% if alert_count > 0 %}<span class="badge">{{ alert_count }}</span>{% endif %}
</button>
<button class="button aux" onclick="showAuxStatus()">
    View AUX Status
    {% if aux_count > 0 %}<span class="badge aux-badge">{{ aux_count }}</span>{% endif %}
</button>
                <button class="button" onclick="showQueue()">View Queue</button>
                <button class="button secondary" onclick="showSettings()">Settings</button>
            </div>
            
            <div class="card">
                <h2>Agent Status</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Avaya ID</th>
                            <th>Full Name</th>
                            <th>State</th>
                            <th>Reason Code</th>
                            <th>Active Call</th>
                            <th>Call Duration</th>
                            <th>Skill Name</th>
                            <th>Time in State</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for agent in agents %}
                        <tr>
                            <td>{{ agent.avaya_id }}</td>
                            <td>{{ agent.name }}</td>
                            <td>{{ agent.state }}</td>
                            <td>{{ agent.reason }}</td>
                            <td>{{ agent.active_call }}</td>
                            <td>{{ agent.call_duration }}</td>
                            <td>{{ agent.skill }}</td>
                            <td>{{ agent.time_in_state }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="tab-content" id="queue-tab">
            <div class="button-container">
                <button class="button" onclick="switchView('main')">Main View</button>
                <button class="button" onclick="switchView('agents')">Agents View</button>
                <button class="button secondary" onclick="copySlaData()">Copy SLA Data</button>
                <button class="button" onclick="switchTab('agents')">Back to Agent Dashboard</button>
            </div>
            
            <div class="card" id="main-view">
                <h2>Queue Status - Main View</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Skill Name</th>
                            <th>Calls in Queue</th>
                            <th>Offered</th>
                            <th>Answered</th>
                            <th>Transfers</th>
                            <th>True Abn</th>
                            <th>Short Abn</th>
                            <th>Oldest Call</th>
                            <th>Max Delay</th>
                            <th>ASA</th>
                            <th>AQT</th>
                            <th>Service Level %</th>
                            <th>RT SL %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for skill in queue_data %}
                        {% set calls_int = skill.calls_in_queue|int %}
                        {% set sl_value = skill.rt_sl|replace('%','')|float if skill.rt_sl.endswith('%') else 0 %}
                        <tr class="{% if calls_int > 0 and sl_value < 80 %}both-warning{% elif calls_int > 0 %}calls-warning{% elif sl_value < 80 %}sl-warning{% endif %}">
                            <td>{{ skill.skill_name }}</td>
                            <td>{% if calls_int > 0 %}⚠️{{ skill.calls_in_queue }}⚠️{% else %}{{ skill.calls_in_queue }}{% endif %}</td>
                            <td>{{ queue_metrics[skill.skill_id].offered if skill.skill_id in queue_metrics else '0' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].answered if skill.skill_id in queue_metrics else '0' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].transfers if skill.skill_id in queue_metrics else '0' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].true_abn if skill.skill_id in queue_metrics else '0' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].short_abn if skill.skill_id in queue_metrics else '0' }}</td>
                            <td>{{ skill.oldest_call }}</td>
                            <td>00:00</td>
                            <td>{{ queue_metrics[skill.skill_id].asa if skill.skill_id in queue_metrics else '00:00' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].aqt if skill.skill_id in queue_metrics else '00:00' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].service_level if skill.skill_id in queue_metrics else '100.00%' }}</td>
                            <td>{{ skill.rt_sl }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="card" id="agents-view" style="display: none;">
                <h2>Queue Status - Agents View</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Skill Name</th>
                            <th>Staffed</th>
                            <th>Available</th>
                            <th>ACW</th>
                            <th>ACD</th>
                            <th>AUX</th>
                            <th>Other</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for skill in queue_data %}
                        <tr>
                            <td>{{ skill.skill_name }}</td>
                            <td>{{ skill.staffed }}</td>
                            <td>{{ skill.available }}</td>
                            <td>{{ queue_metrics[skill.skill_id].acw if skill.skill_id in queue_metrics else '0' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].acd if skill.skill_id in queue_metrics else '0' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].aux if skill.skill_id in queue_metrics else '0' }}</td>
                            <td>{{ queue_metrics[skill.skill_id].other if skill.skill_id in queue_metrics else '0' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Alert Window -->
    <div class="overlay" id="overlay" onclick="hideAllWindows()"></div>
    
    <div class="alert-window" id="alerts-window">
        <button class="close-button" onclick="hideAlerts()">&times;</button>
        <h2>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            ACTIVE ALERTS
        </h2>
        {% if alerts %}
            {% for alert_type, alert_list in alerts_by_type.items() %}
                <div style="margin-bottom: 1.5rem;">
                    <div style="font-weight: 600; color: var(--alert-color); font-size: 1.2rem; margin-bottom: 0.5rem;">
                        {{ alert_type.upper() }}
                    </div>
                    {% for alert in alert_list %}
                        <div class="alert-item">
                            <strong>{{ alert.avaya_id }} - {{ alert.name }}</strong> ({{ alert.time }})
                            <div class="skill-tag">{{ alert.skill }}</div>
                        </div>
                    {% endfor %}
                </div>
            {% endfor %}
        {% else %}
            <div style="text-align: center; padding: 2rem; color: #666;">
                No active alerts at the moment.
            </div>
        {% endif %}
    </div>
    
    <!-- AUX Window -->
    <div class="alert-window" id="aux-window">
        <button class="close-button" onclick="hideAuxStatus()">&times;</button>
        <h2>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            AUX STATUS
        </h2>
        {% if aux_status %}
            {% for reason, aux_list in aux_by_reason.items() %}
                <div style="margin-bottom: 1.5rem;">
                    <div style="font-weight: 600; color: var(--aux-color); font-size: 1.2rem; margin-bottom: 0.5rem;">
                        {{ reason }}
                    </div>
                    {% for aux in aux_list %}
                        <div class="alert-item aux-item">
                            <strong>{{ aux.avaya_id }} - {{ aux.name }}</strong> ({{ aux.time }})
                            <div class="skill-tag">{{ aux.skill }}</div>
                        </div>
                    {% endfor %}
                </div>
            {% endfor %}
        {% else %}
            <div style="text-align: center; padding: 2rem; color: #666;">
                No agents in AUX status.
            </div>
        {% endif %}
    </div>
    
    <!-- Settings Modal -->
    <div class="settings-modal" id="settings-modal">
        <button class="close-button" onclick="hideSettings()">&times;</button>
        <h2 style="margin-bottom: 1.5rem;">Alert Settings</h2>
        <form class="settings-form" id="alert-settings-form">
            <div class="form-group">
                <label for="long-call">Long Call (seconds)</label>
                <input type="number" id="long-call" name="Long Call" value="{{ alert_times['Long Call'] }}">
            </div>
            <div class="form-group">
                <label for="extended-lunch">Extended Lunch (seconds)</label>
                <input type="number" id="extended-lunch" name="Extended Lunch" value="{{ alert_times['Extended Lunch'] }}">
            </div>
            <div class="form-group">
                <label for="long-acw">Long ACW (seconds)</label>
                <input type="number" id="long-acw" name="Long ACW" value="{{ alert_times['Long ACW'] }}">
            </div>
            <div class="form-group">
                <label for="extended-break">Extended Break (seconds)</label>
                <input type="number" id="extended-break" name="Extended Break" value="{{ alert_times['Extended Break'] }}">
            </div>
            <div class="form-group">
                <label for="it-issue">IT Issue (seconds)</label>
                <input type="number" id="it-issue" name="IT Issue" value="{{ alert_times['IT Issue'] }}">
            </div>
            <div class="form-group">
                <label for="long-hold">Long Hold (seconds)</label>
                <input type="number" id="long-hold" name="Long Hold" value="{{ alert_times['Long Hold'] }}">
            </div>
            <button type="submit" class="save-button">Save Changes</button>
        </form>
    </div>
    
    <script>
        // Store current view state
        let currentView = 'main';
        
        // Tab and view switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            if (tabName === 'agents') {
                document.querySelector('.tab:nth-child(1)').classList.add('active');
                document.getElementById('agents-tab').classList.add('active');
            } else {
                document.querySelector('.tab:nth-child(2)').classList.add('active');
                document.getElementById('queue-tab').classList.add('active');
                // Restore the previous view in queue tab
                switchView(currentView);
            }
        }
        
        function switchView(viewName) {
            currentView = viewName;
            if (viewName === 'main') {
                document.getElementById('main-view').style.display = 'block';
                document.getElementById('agents-view').style.display = 'none';
            } else {
                document.getElementById('main-view').style.display = 'none';
                document.getElementById('agents-view').style.display = 'block';
            }
        }
        
        // Alert and AUX windows
        function showAlerts() {
            document.getElementById('alerts-window').style.display = 'block';
            document.getElementById('overlay').style.display = 'block';
        }
        
        function hideAlerts() {
            document.getElementById('alerts-window').style.display = 'none';
            document.getElementById('overlay').style.display = 'none';
        }
        
        function showAuxStatus() {
            document.getElementById('aux-window').style.display = 'block';
            document.getElementById('overlay').style.display = 'block';
        }
        
        function hideAuxStatus() {
            document.getElementById('aux-window').style.display = 'none';
            document.getElementById('overlay').style.display = 'none';
        }
        
        function showSettings() {
            document.getElementById('settings-modal').style.display = 'block';
            document.getElementById('overlay').style.display = 'block';
        }
        
        function hideSettings() {
            document.getElementById('settings-modal').style.display = 'none';
            document.getElementById('overlay').style.display = 'none';
        }
        
        function hideAllWindows() {
            hideAlerts();
            hideAuxStatus();
            hideSettings();
        }
        
        function showQueue() {
            switchTab('queue');
        }
        
        // Copy SLA data to clipboard
        function copySlaData() {
            let lowSlaSkills = [];
            
            // Get skills with SLA < 80%
            {% for skill in queue_data %}
                {% set sl_value = skill.rt_sl|replace('%','')|float if skill.rt_sl.endswith('%') else 0 %}
                {% if sl_value < 80 %}
                    lowSlaSkills.push("- {{ skill.skill_name }} = {{ skill.rt_sl }}");
                {% endif %}
            {% endfor %}
            
            let textToCopy;
            if (lowSlaSkills.length > 0) {
                textToCopy = "Voice - Queue\\n\\n" +
                             "Team, this is our current SLA view and listed you'll find the impacted skills so far:\\n\\n" +
                             lowSlaSkills.join("\\n") + 
                             "\\n\\nThe other skills are on target.";
            } else {
                textToCopy = "Voice - Queue\\n\\n" +
                             "Team, all skills are currently meeting the SLA target of 80% or above.";
            }
            
            navigator.clipboard.writeText(textToCopy)
                .then(() => {
                    alert("SLA data has been copied to clipboard!");
                })
                .catch(err => {
                    alert("Failed to copy data: " + err);
                });
        }
        
        // Show queue notification if there are calls in queue
        if ({{ total_calls }} > 0) {
            document.getElementById('queue-notification').style.display = 'block';
        }
        
        // Add form submission handler
        document.getElementById('alert-settings-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {};
            const inputs = this.querySelectorAll('input');
            inputs.forEach(input => {
                formData[input.name] = input.value;
            });
            
            fetch('/update_alert_times', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Settings updated successfully!');
                    hideSettings();
                    // Refresh the page to show updated alerts
                    refreshData();
                } else {
                    alert('Error updating settings: ' + data.error);
                }
            })
            .catch(error => {
                alert('Error updating settings: ' + error);
            });
        });
        
        // Auto-refresh only the current view without changing tabs
        function refreshData() {
    const activeTab = document.querySelector('.tab.active').textContent.trim();
    const currentQueueView = document.getElementById('agents-view').style.display === 'none' ? 'main' : 'agents';
    
    fetch(window.location.href, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'text/html',
        },
        cache: 'no-store'
    })
    .then(response => response.text())
    .then(html => {
        const parser = new DOMParser();
        const newDoc = parser.parseFromString(html, 'text/html');
        
        // Update header and notification first
        const newHeader = newDoc.querySelector('.last-updated');
        if (newHeader) {
            document.querySelector('.last-updated').textContent = newHeader.textContent;
        }
        
        const newNotification = newDoc.getElementById('queue-notification');
        if (newNotification) {
            document.getElementById('queue-notification').style.display = newNotification.style.display;
            document.getElementById('queue-notification').textContent = newNotification.textContent;
        }
        
        // Update button counts
        const newAlertButton = newDoc.querySelector('.button.alert');
        const newAuxButton = newDoc.querySelector('.button.aux');
        if (newAlertButton) {
            const alertButton = document.querySelector('.button.alert');
            alertButton.innerHTML = newAlertButton.innerHTML;
        }
        if (newAuxButton) {
            const auxButton = document.querySelector('.button.aux');
            auxButton.innerHTML = newAuxButton.innerHTML;
        }
        
        if (activeTab.includes('Agent')) {
            // Update agents tab
            const newContent = newDoc.getElementById('agents-tab');
            if (newContent) {
                document.getElementById('agents-tab').innerHTML = newContent.innerHTML;
            }
            
            // Update alerts and aux windows if they're open
            if (document.getElementById('alerts-window').style.display === 'block') {
                const newAlertsWindow = newDoc.getElementById('alerts-window');
                document.getElementById('alerts-window').innerHTML = newAlertsWindow.innerHTML;
            }
            
            if (document.getElementById('aux-window').style.display === 'block') {
                const newAuxWindow = newDoc.getElementById('aux-window');
                document.getElementById('aux-window').innerHTML = newAuxWindow.innerHTML;
            }
        } else {
            // Update queue tab
            const newContent = newDoc.getElementById('queue-tab');
            if (newContent) {
                document.getElementById('queue-tab').innerHTML = newContent.innerHTML;
                // Restore current view
                switchView(currentQueueView);
            }
        }
    })
    .catch(error => console.error('Error refreshing data:', error));
}
        
        // Refresh every 15 seconds
        setInterval(refreshData, 15000);
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            // Show queue notification if needed
            if ({{ total_calls }} > 0) {
                document.getElementById('queue-notification').style.display = 'block';
            }
            
            // Set initial view in queue tab
            switchView(currentView);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    # Organizar alertas por tipo
    alerts_by_type = defaultdict(list)
    for alert in current_data['alerts']:
        alerts_by_type[alert['type']].append(alert)
    
    # Organizar AUX por razón
    aux_by_reason = defaultdict(list)
    for aux in current_data['aux_status']:
        aux_by_reason[aux['reason']].append(aux)
    
    return render_template_string(HTML_TEMPLATE, 
        agents=current_data['agents'],
        alerts=current_data['alerts'],
        alerts_by_type=alerts_by_type,
        aux_status=current_data['aux_status'],
        aux_by_reason=aux_by_reason,
        queue_data=current_data['queue_data'],
        queue_data_with_calls=current_data['queue_data_with_calls'],
        queue_metrics=current_data['queue_metrics'],
        total_calls=current_data['total_calls'],
        alert_count=len(current_data['alerts']),
        aux_count=len(current_data['aux_status']),
        last_update=current_data['last_update'],
        alert_times=ALERT_TIMES  # Add alert times to template context
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
