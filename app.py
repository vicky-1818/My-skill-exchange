from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import pymysql
from datetime import timedelta
import random

app = Flask(__name__)
app.secret_key = "skill_exchange_secret_key"
app.permanent_session_lifetime = timedelta(days=30)

# ---------------- MySQL Config ----------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Vicky2006"
DB_NAME = "skill_exchange"
DB_PORT = 3306

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

def login_required():
    return "user_id" in session

def admin_required():
    return session.get("role") == "admin"

# ---------------- Embedded CSS (Hybrid SaaS + Theme) ----------------
STYLE = """
<style>
body { font-family: 'Segoe UI', Arial; margin:0; transition:0.3s; background:url('https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1650&q=80') no-repeat center center fixed; background-size:cover; }
.navbar { background:#1f2937; color:white; padding:15px 25px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 10px rgba(0,0,0,0.1);}
.navbar .logo { font-weight:bold; font-size:20px; }
.navbar a { color:white; margin-left:15px; text-decoration:none; }
.sidebar { width:250px; background:#111827; color:white; position:fixed; top:0; left:0; height:100%; padding-top:80px; box-shadow:2px 0 5px rgba(0,0,0,0.1);}
.sidebar a { display:block; color:white; padding:15px 20px; text-decoration:none; border-left:4px solid transparent;}
.sidebar a:hover { background:#1f2937; border-left:4px solid #3b82f6;}
.main { margin-left:260px; padding:30px; transition:0.3s;}
.card { background:rgba(255,255,255,0.9); backdrop-filter:blur(10px); padding:25px; border-radius:12px; box-shadow:0 8px 20px rgba(0,0,0,0.1); margin-bottom:20px; transition:0.3s;}
.card:hover { transform:translateY(-3px); }
button { padding:8px 20px; background:linear-gradient(90deg,#3b82f6,#06b6d4); color:white; border:none; cursor:pointer; border-radius:8px; transition:0.3s;}
button:hover { opacity:0.9; }
input { padding:8px; width:80%; margin:5px 0; border-radius:5px; border:1px solid #ccc;}
table { width:100%; border-collapse:collapse; }
th, td { padding:10px; text-align:left; border-bottom:1px solid #e5e7eb;}
.theme-toggle { cursor:pointer; font-size:18px; margin-bottom:10px; display:inline-block;}
.dark-theme body { background:#121212; color:#eee; background-image:none;}
.dark-theme .card { background:rgba(20,20,20,0.8); color:#eee; }
.success { color:#16a34a; }
.error { color:#dc2626; }
</style>
"""

# ---------------- Embedded JS ----------------
SCRIPT = """
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<script>
function toggleTheme(){ document.body.classList.toggle('dark-theme'); }

async function fetchSkills(){
  const res=await fetch("/api/get_skills");
  const data=await res.json();
  if(data.status==="success"){
    renderSkills("offeredList", data.offered);
    renderSkills("learnList", data.learn);
    renderSkills("recommendList", data.recommend);
    renderMatches("matchList", data.match);
  }
}

function renderSkills(containerId, skills){
  const container=document.getElementById(containerId);
  if(!container) return;
  container.innerHTML="";
  skills.forEach(s=>{
    const div=document.createElement("div");
    div.className="card";
    div.innerHTML=s;
    container.appendChild(div);
  });
}

function renderMatches(containerId, users){
  const container=document.getElementById(containerId);
  if(!container) return;
  container.innerHTML="";

  users.forEach(u=>{
    const div=document.createElement("div");
    div.className="card";

    let skills = u.skills.join(", ");

    div.innerHTML = `
      <b>${u.name}</b><br>
      Match Skills: ${skills}<br>
      <button onclick="sendRequest(${u.id}, '${u.skills[0]}')">
        Request Exchange
      </button>
    `;

    container.appendChild(div);
  });
}

async function addSkill(type){
  const input=document.getElementById(type+"Input");
  const skill=input.value.trim();
  if(!skill) return;
  const res=await fetch("/api/add_skill",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({skill_name:skill,skill_type:type})});
  const data=await res.json();
  alert(data.message);
  if(data.status==="success"){ input.value=""; fetchSkills(); }
}

async function removeSkill(type,skill){
  if(!confirm("Remove this skill?")) return;
  const res=await fetch("/api/remove_skill",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({skill_name:skill,skill_type:type})});
  const data=await res.json();
  alert(data.message);
  if(data.status==="success") fetchSkills();
}

async function editSkill(type,oldSkill){
  const newSkill=prompt("Enter new skill name:", oldSkill);
  if(!newSkill) return;
  const res=await fetch("/api/edit_skill",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({old_skill:oldSkill,new_skill:newSkill,skill_type:type})});
  const data=await res.json();
  alert(data.message);
  if(data.status==="success") fetchSkills();
}

async function sendRequest(receiverId, skill){
  const res = await fetch("/api/send_request", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      receiver_id: receiverId,
      skill: skill
    })
  });

  const data = await res.json();
  alert(data.message);
}

async function updateRequest(id, status){
  const res = await fetch("/api/update_request", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({request_id:id, status:status})
  });

  const data = await res.json();
  alert(data.message);
  location.reload();
}

let reportedUserId = null;

function openReport(id){
    reportedUserId = id;
    document.getElementById("reportBox").style.display = "block";
}

function closeReport(){
    document.getElementById("reportBox").style.display = "none";
}

async function submitReport(){
    const issue = document.getElementById("issue").value;
    const desc = document.getElementById("desc").value;
    const file = document.getElementById("evidence").files[0];

    const formData = new FormData();
    formData.append("reported_user_id", reportedUserId);
    formData.append("issue_type", issue);
    formData.append("description", desc);
    formData.append("evidence", file);

    const res = await fetch("/api/report_user", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    alert(data.message);
    closeReport();
}

window.onload=function(){ fetchSkills(); }
</script>
"""

# ---------------- BASE TEMPLATE ----------------
def base_template(content):
    return STYLE + SCRIPT + content

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    if login_required(): return redirect(url_for("skills_page"))
    return redirect(url_for("login"))

# ----- LOGIN -----
@app.route("/login", methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        password=request.form["password"].strip()
        conn=get_db_connection(); cur=conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s",(email,password))
        user=cur.fetchone(); conn.close()
        if not user: error="Invalid credentials!"
        else:
            session.permanent=True
            session["user_id"]=user["id"]
            session["user_name"]=user["name"]
            session["user_email"]=user["email"]
            session["role"]=user.get("role","user")
            return redirect(url_for("skills_page"))
    return render_template_string(base_template(f"""
    <div class='main'>
      <div class='card'>
        <h1>Login</h1>
        <div class='error'>{error}</div>
        <form method='POST'>
          <input type='email' name='email' placeholder='Email' required>
          <input type='password' name='password' placeholder='Password' required>
          <button type='submit'>Login</button>
        </form>
        <p>New user? <a href='/register'>Register here</a></p>
      </div>
    </div>
    """))

# ----- REGISTER -----
@app.route("/register", methods=["GET","POST"])
def register():
    error=""
    if request.method=="POST":
        name=request.form["name"].strip()
        email=request.form["email"].strip().lower()
        password=request.form["password"].strip()
        conn=get_db_connection(); cur=conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s",(email,))
        if cur.fetchone(): error="Email already registered!"
        else: 
            cur.execute("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,'user')",(name,email,password))
            conn.commit(); conn.close(); 
            return redirect(url_for("login"))
        conn.close()
    return render_template_string(base_template(f"""
    <div class='main'>
      <div class='card'>
        <h1>Register</h1>
        <div class='error'>{error}</div>
        <form method='POST'>
          <input name='name' placeholder='Full Name' required>
          <input name='email' type='email' placeholder='Email' required>
          <input name='password' type='password' placeholder='Password' required>
          <button type='submit'>Register</button>
        </form>
        <p>Already registered? <a href='/login'>Login here</a></p>
      </div>
    </div>
    """))

# ----- LOGOUT -----
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ----- USER DASHBOARD / SKILLS -----
@app.route("/skills")
def skills_page():
    if not login_required(): return redirect(url_for("login"))
    return render_template_string(base_template(f"""
    <div class='sidebar'>
      <a href='/skills'>Dashboard</a>
      <a href='/search'>Search Users</a>
      <a href='/my_profile'>My Profile</a>
      <a href='/requests'>Requests</a>
      <a href='/messages'>Messages</a>
      <a href='/tests'>Skill Test</a>
      <a href='/logout'>Logout</a>
    </div>
    <div class='main'>
      <div class='theme-toggle' onclick='toggleTheme()'>🌓 Toggle Theme</div>
      <div class='card'>
        <h2>Welcome, {session['user_name']}</h2>
        <h3>Your Skills Offered</h3>
        <div id='offeredList'></div>
        <input id='offeredInput' placeholder='Add skill offered'><button onclick="addSkill('offered')">Add</button>
        <h3>Skills You Want to Learn</h3>
        <div id='learnList'></div>
        <input id='learnInput' placeholder='Add skill to learn'><button onclick="addSkill('learn')">Add</button>
        <h3>AI Skill Recommendations</h3>
        <div id='recommendList'></div>
        <h3>Smart User Matches</h3>
        <div id='matchList'></div>
      </div>
    </div>
    """))

# ----- PUBLIC PROFILE VIEW -----
@app.route("/profile/<int:user_id>")
def profile_page(user_id):
    conn=get_db_connection(); cur=conn.cursor()
    cur.execute("SELECT id,name,email FROM users WHERE id=%s",(user_id,))
    user=cur.fetchone()
    if not user: conn.close(); return "User not found",404
    cur.execute("SELECT skill_name FROM skills WHERE user_id=%s AND skill_type='offered'",(user_id,))
    offered=[r["skill_name"] for r in cur.fetchall()]
    cur.execute("SELECT skill_name FROM skills WHERE user_id=%s AND skill_type='learn'",(user_id,))
    learn=[r["skill_name"] for r in cur.fetchall()]
    conn.close()
    return render_template_string(base_template(f"""
    <div class='sidebar'>
      <a href='/skills'>Dashboard</a>
      <a href='/search'>Search Users</a>
      <a href='/my_profile'>My Profile</a>
      <a href='/logout'>Logout</a>
    </div>
    <div class='main'>
      <div class='card'>
        <h2>{user['name']}'s Profile</h2>
        <p>Email: {user['email']}</p>
        <h3>Skills Offered</h3>
        <ul>{"".join([f"<li>{s}</li>" for s in offered])}</ul>
        <h3>Skills To Learn</h3>
        <ul>{"".join([f"<li>{s}</li>" for s in learn])}</ul>
      </div>
    </div>
    """))

# ----- MY PROFILE LINK -----
@app.route("/my_profile")
def my_profile():
    if not login_required(): return redirect(url_for("login"))
    return redirect(url_for("profile_page", user_id=session["user_id"]))

# ---------------- API ENDPOINTS ----------------
@app.route("/api/get_skills")
def api_get_skills():
    if not login_required(): return jsonify({"status":"error","message":"Not logged in"}),401
    user_id=session["user_id"]
    conn=get_db_connection(); cur=conn.cursor()
    cur.execute("SELECT skill_name FROM skills WHERE user_id=%s AND skill_type='offered'",(user_id,))
    offered=[r["skill_name"] for r in cur.fetchall()]
    cur.execute("SELECT skill_name FROM skills WHERE user_id=%s AND skill_type='learn'",(user_id,))
    learn=[r["skill_name"] for r in cur.fetchall()]
    
    # Dynamic AI recommendation
    cur.execute("SELECT id,name FROM users WHERE id!=%s",(user_id,))
    other_users=cur.fetchall()
    recommendations=set(); matches=[]
    for u in other_users:
        cur.execute("SELECT skill_name FROM skills WHERE user_id=%s AND skill_type='offered'",(u["id"],))
        u_offered=[s["skill_name"] for s in cur.fetchall()]
        for s in u_offered:
            if s not in offered:
                recommendations.add(s)
        match_skills=list(set(u_offered)&set(learn))
        if match_skills: matches.append({"id":u["id"],"name":u["name"],"skills":match_skills})
    conn.close()
    return jsonify({"status":"success","offered":offered,"learn":learn,"recommend":list(recommendations)[:5],"match":matches[:5]})

@app.route("/api/add_skill",methods=["POST"])
def api_add_skill():
    if not login_required(): return jsonify({"status":"error","message":"Not logged in"}),401
    data=request.get_json(); skill=data.get("skill_name","").strip(); type=data.get("skill_type","").strip()
    if not skill or type not in ["offered","learn"]: return jsonify({"status":"error","message":"Invalid"}),400
    conn=get_db_connection(); cur=conn.cursor()
    try: cur.execute("INSERT INTO skills(user_id,skill_name,skill_type) VALUES(%s,%s,%s)",(session["user_id"],skill,type)); conn.commit()
    except: conn.close(); return jsonify({"status":"error","message":"Already exists"}),400
    conn.close(); return jsonify({"status":"success","message":"Added"})

@app.route("/api/remove_skill",methods=["POST"])
def api_remove_skill():
    if not login_required(): return jsonify({"status":"error","message":"Not logged in"}),401
    data=request.get_json(); skill=data.get("skill_name","").strip(); type=data.get("skill_type","").strip()
    conn=get_db_connection(); cur=conn.cursor()
    cur.execute("DELETE FROM skills WHERE user_id=%s AND skill_name=%s AND skill_type=%s",(session["user_id"],skill,type)); conn.commit(); conn.close()
    return jsonify({"status":"success","message":"Removed"})

@app.route("/api/edit_skill",methods=["POST"])
def api_edit_skill():
    if not login_required(): return jsonify({"status":"error","message":"Not logged in"}),401
    data=request.get_json(); old_skill=data.get("old_skill","").strip(); new_skill=data.get("new_skill","").strip(); type=data.get("skill_type","").strip()
    if not old_skill or not new_skill or type not in ["offered","learn"]: return jsonify({"status":"error","message":"Invalid"}),400
    conn=get_db_connection(); cur=conn.cursor()
    try:
        cur.execute("UPDATE skills SET skill_name=%s WHERE user_id=%s AND skill_name=%s AND skill_type=%s",(new_skill,session["user_id"],old_skill,type))
        conn.commit()
    except:
        conn.close(); return jsonify({"status":"error","message":"Error"}),400
    conn.close(); return jsonify({"status":"success","message":"Updated"})

# ----- SEARCH USERS -----
@app.route("/search")
def search():
    if not login_required(): return redirect(url_for("login"))
    query=request.args.get("q","")
    conn=get_db_connection(); cur=conn.cursor()
    cur.execute("SELECT id,name,email FROM users WHERE name LIKE %s OR email LIKE %s",('%'+query+'%','%'+query+'%'))
    users=cur.fetchall(); conn.close()
    return render_template_string(base_template(f"""
<div class='sidebar'>
  <a href='/skills'>Dashboard</a>
  <a href='/search'>Search Users</a>
  <a href='/my_profile'>My Profile</a>
  <a href='/logout'>Logout</a>
</div>

<div class='main'>
  <div class='card'>
    <h2>Search Users</h2>

    <form method='get'>
      <input name='q' placeholder='Search by name or email' value='{query}'>
      <button type='submit'>Search</button>
    </form>

    <ul>
    {"".join([f"""
    <li>
      <b>{u['name']}</b> ({u['email']}) <br>

      <a href='/profile/{u['id']}'>
        <button>View Profile</button>
      </a>

      <button onclick="sendRequest({u['id']}, prompt('Enter skill you want'))">
        Send Request
      </button>

      <a href='/chat/{u['id']}'>
        <button>Message</button>
      </a>

      <button onclick="openReport({u['id']})">
        Report
      </button>
    </li>
    """ for u in users])}
    </ul>

  </div>
</div>

<!-- REPORT POPUP -->
<div id="reportBox" style="display:none; position:fixed; top:20%; left:30%; background:white; padding:20px; border-radius:10px;">
  <h3>Report User</h3>

  <select id="issue">
    <option>Academic cheating</option>
    <option>Fake skill claims</option>
    <option>Abuse / harassment</option>
    <option>Fraud / scam</option>
    <option>Inappropriate behavior</option>
    <option>Spam</option>
    <option>Misleading information</option>
    <option>Other</option>
  </select><br><br>

  <textarea id="desc" placeholder="Describe issue"></textarea><br><br>

  <input type="file" id="evidence"><br><br>

  <button onclick="submitReport()">Submit</button>
  <button onclick="closeReport()">Cancel</button>
</div>

"""))



@app.route("/api/send_request", methods=["POST"])
def send_request():
    if not login_required():
        
        return jsonify({"status":"error"}),401
    
    data = request.get_json()
    receiver_id = data.get("receiver_id")
    skill = data.get("skill")
    print("Sender:", session["user_id"], "Receiver:", receiver_id)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO requests(sender_id, receiver_id, skill_requested) VALUES(%s,%s,%s)",
        (session["user_id"], receiver_id, skill)
    )
    conn.commit()
    conn.close()

    return jsonify({"status":"success","message":"Request sent"})


@app.route("/requests")
def view_requests():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT r.id, r.sender_id, u.name, r.skill_requested, r.status
    FROM requests r
    JOIN users u ON r.sender_id = u.id
    WHERE r.receiver_id = %s
""", (session["user_id"],))

    requests = cur.fetchall()
    conn.close()

    return render_template_string(base_template(f"""
<div class='sidebar'>
  <a href='/skills'>Dashboard</a>
  <a href='/requests'>Requests</a>
  <a href='/logout'>Logout</a>
</div>

<div class='main'>
  <div class='card'>
    <h2>Incoming Requests</h2>
    <ul>
    {"".join([
f"""
<li>
  {r['name']} wants {r['skill_requested']} ({r['status']})

  <button onclick="updateRequest({r['id']}, 'accepted')">Accept</button>
  <button onclick="updateRequest({r['id']}, 'rejected')">Reject</button>

  {"<a href='/chat/" + str(r["sender_id"]) + "'><button>Chat</button></a>" if r['status']=="accepted" else ""}
</li>
"""
for r in requests
])}
    </ul>
  </div>
</div>
"""))


@app.route("/api/update_request", methods=["POST"])
def update_request():
    if not login_required():
        return jsonify({"status":"error"}),401

    data = request.get_json()
    request_id = data.get("request_id")
    status = data.get("status")  # accepted / rejected

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE requests SET status=%s WHERE id=%s", (status, request_id))
    conn.commit()
    conn.close()

    return jsonify({"status":"success","message":"Updated"})

#send messages
@app.route("/api/send_message", methods=["POST"])
def send_message():
    if not login_required():
        return jsonify({"status":"error"}), 401

    data = request.get_json()
    receiver_id = data.get("receiver_id")
    message = data.get("message")

    if not receiver_id or not message:
        return jsonify({"status":"error","message":"Missing data"}),400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO messages (sender_id, receiver_id, message, status)
        VALUES (%s, %s, %s, 'sent')
    """, (session["user_id"], receiver_id, message))

    conn.commit()
    conn.close()

    return jsonify({"status":"success","message":"Message sent"})

import os

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/api/report_user", methods=["POST"])
def report_user():
    if not login_required():
        return jsonify({"status":"error"}), 401

    reporter_id = session["user_id"]
    reported_user_id = request.form.get("reported_user_id")
    issue = request.form.get("issue_type")
    desc = request.form.get("description")

    file = request.files.get("evidence")
    filename = ""

    if file:
        filename = f"{random.randint(1000,9999)}_{file.filename}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO reports 
        (reporter_id, reported_user_id, issue_type, description, evidence)
        VALUES (%s, %s, %s, %s, %s)
    """, (reporter_id, reported_user_id, issue, desc, filename))

    conn.commit()
    conn.close()

    return jsonify({"status":"success","message":"Report submitted"})


#receive messages
@app.route("/api/get_messages/<int:user_id>")
def get_messages(user_id):
    if not login_required():
        return jsonify({"status":"error"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT sender_id, receiver_id, message, status, created_at
        FROM messages
        WHERE 
        (sender_id=%s AND receiver_id=%s)
        OR 
        (sender_id=%s AND receiver_id=%s)
        ORDER BY created_at ASC
    """, (session["user_id"], user_id, user_id, session["user_id"]))

    messages = cur.fetchall()

    # mark seen
    cur.execute("""
        UPDATE messages
        SET status='seen'
        WHERE receiver_id=%s AND sender_id=%s
    """, (session["user_id"], user_id))

    conn.commit()
    conn.close()

    return jsonify({"status":"success","messages":messages})

@app.route("/api/chat_list")
def chat_list():
    if not login_required():
        return jsonify({"status": "error"}), 401

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        u.id, u.name,
        m.message,
        m.created_at
    FROM users u
    JOIN messages m ON (
        (m.sender_id = u.id AND m.receiver_id = %s) OR
        (m.receiver_id = u.id AND m.sender_id = %s)
    )
    ORDER BY m.created_at DESC
    """, (user_id, user_id))

    data = cur.fetchall()
    conn.close()

    return jsonify({"status": "success", "data": data})


#chat ui
@app.route("/chat/<int:user_id>")
def chat(user_id):
    if not login_required():
        return redirect(url_for("login"))

    return render_template_string(base_template("""
    <div class='sidebar'>
      <a href='/skills'>Dashboard</a>
      <a href='/logout'>Logout</a>
    </div>

    <div class='main'>
      <div class='card' style='height:80vh; display:flex; flex-direction:column;'>

        <h3>Chat</h3>

        <div id='chatBox' style='flex:1; overflow-y:auto; padding:10px;'></div>

        <div style='display:flex; gap:10px;'>
          <input id='msgInput' placeholder='Type message...' style='flex:1;'>
          <button onclick='sendMsg()'>Send</button>
        </div>

      </div>
    </div>

    <script>
    const receiverId = """ + str(user_id) + """;
    const currentUser = """ + str(session["user_id"]) + """;

    async function loadMessages(){
        const res = await fetch("/api/get_messages/" + receiverId);
        const data = await res.json();

        const box = document.getElementById("chatBox");
        box.innerHTML = "";

        data.messages.forEach(function(m){
            const wrapper = document.createElement("div");
            const bubble = document.createElement("div");

            const isMe = (m.sender_id == currentUser);

            wrapper.style.display = "flex";
            wrapper.style.justifyContent = isMe ? "flex-end" : "flex-start";

            bubble.style.background = isMe ? "#3b82f6" : "#e5e7eb";
            bubble.style.color = isMe ? "white" : "black";
            bubble.style.padding = "10px";
            bubble.style.borderRadius = "10px";
            bubble.style.margin = "5px";
            bubble.style.maxWidth = "60%";

            let statusIcon = "";
            if(isMe){
                if(m.status === "seen") statusIcon = " ✓✓";
                else statusIcon = " ✓";
            }

            bubble.innerHTML =
    "<b>" + m.message + "</b>" +
    "<br><small>" + m.created_at + statusIcon + "</small>";

            wrapper.appendChild(bubble);
            box.appendChild(wrapper);
        });

        box.scrollTop = box.scrollHeight;
    }

    async function sendMsg(){
        const input = document.getElementById("msgInput");
        const msg = input.value.trim();
        if(!msg) return;

        await fetch("/api/send_message", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                receiver_id: receiverId,
                message: msg
            })
        });

        input.value="";
        loadMessages();
    }

    setInterval(loadMessages, 2000);
    loadMessages();
    </script>
    """))





# ui entry point
@app.route("/messages")
def messages_page():
    if not login_required():
        return redirect(url_for("login"))

    return render_template_string(base_template("""
    <div class='sidebar'>
      <a href='/skills'>Dashboard</a>
      <a href='/messages'>Messages</a>
      <a href='/logout'>Logout</a>
    </div>

    <div class='main'>
      <div class='card'>
        <h2>Messages</h2>
        <div id="chatList"></div>
      </div>
    </div>

    <script>
    async function loadChats(){
        const res = await fetch("/api/chat_list");
        const data = await res.json();

        const box = document.getElementById("chatList");
        box.innerHTML = "";

        data.data.forEach(c => {
            const div = document.createElement("div");
            div.className = "card";

            div.innerHTML = `
                <b>${c.name}</b><br>
                ${c.message}<br>
                <small>${c.created_at}</small><br>
                <a href="/chat/${c.id}">
                    <button>Open Chat</button>
                </a>
            `;

            box.appendChild(div);
        });
    }

    loadChats();
    </script>
    """))

#test
@app.route("/tests")
def tests_page():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tests")
    tests = cur.fetchall()
    conn.close()

    return render_template_string(base_template(f"""
    <div class='sidebar'>
      <a href='/skills'>Dashboard</a>
      <a href='/tests'>Skill Test</a>
      <a href='/logout'>Logout</a>
    </div>

    <div class='main'>
      <div class='card'>
        <h2>Available Tests</h2>
        <ul>
        {"".join([f"""
        <li>
          {t['skill_name']}
          <a href='/start_test/{t['id']}'>
            <button>Start Test</button>
          </a>
        </li>
        """ for t in tests])}
        </ul>
      </div>
    </div>
    """))
    

#start test page 
@app.route("/start_test/<int:test_id>")
def start_test(test_id):
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM questions WHERE test_id=%s", (test_id,))
    questions = cur.fetchall()
    conn.close()

    return render_template_string(base_template(f"""
    <div class='main'>
      <div class='card'>
        <h2>Test</h2>

        <form method="POST" action="/submit_test/{test_id}">
        {"".join([f"""
          <p><b>{q['question']}</b></p>
          <input type="radio" name="q{q['id']}" value="1"> {q['option1']}<br>
          <input type="radio" name="q{q['id']}" value="2"> {q['option2']}<br>
          <input type="radio" name="q{q['id']}" value="3"> {q['option3']}<br>
          <input type="radio" name="q{q['id']}" value="4"> {q['option4']}<br>
          <hr>
        """ for q in questions])}

        <button type="submit">Submit Test</button>
        </form>
      </div>
    </div>
    """))



#submit test
@app.route("/submit_test/<int:test_id>", methods=["POST"])
def submit_test(test_id):
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM questions WHERE test_id=%s", (test_id,))
    questions = cur.fetchall()

    score = 0

    for q in questions:
        user_ans = request.form.get(f"q{q['id']}")
        if user_ans and int(user_ans) == q['correct_option']:
            score += 1

    status = "PASS" if score >= 12 else "FAIL"

    cur.execute("""
        INSERT INTO results (user_id, test_id, score, status)
        VALUES (%s, %s, %s, %s)
    """, (session["user_id"], test_id, score, status))

    conn.commit()
    conn.close()

    return f"<h2>Your Score: {score}</h2><h3>{status}</h3><a href='/tests'>Back</a>"







# ---------------- RUN ----------------
if __name__=="__main__":
    app.run(debug=True)