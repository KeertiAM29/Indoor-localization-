"use strict";

const POLL_MS       = 1000;
const SPARKLINE_LEN = 40;

const ZONE_POS = {
  "Room101":  {left:"13%",top:"28%"},
  "Room102":  {left:"36%",top:"28%"},
  "Room103":  {left:"60%",top:"28%"},
  "Room104":  {left:"85%",top:"28%"},
  "Corridor": {left:"44%",top:"50%"},
  "UNKNOWN":  {left:"44%",top:"50%"},
};

const sparkA = [], sparkB = [];
let logItems = [], prevConn = null, prevState = null, prevLoc = null;

const el = id => document.getElementById(id);
const dom = {
  demoPill:     el("demoPill"),
  banner:       el("disconnectedBanner"),
  bannerText:   el("bannerText"),
  bannerRetry:  el("bannerRetry"),
  statusChip:   el("statusChip"),
  chipDot:      el("chipDot"),
  chipValue:    el("chipValue"),
  sysDot:       el("sysDot"),
  sysStatusText:el("sysStatusText"),
  cardA:el("cardA"),valA:el("valA"),unitA:el("unitA"),subA:el("subA"),
  cardB:el("cardB"),valB:el("valB"),unitB:el("unitB"),subB:el("subB"),
  cardLoc:el("cardLoc"),valLoc:el("valLoc"),subLoc:el("subLoc"),
  cardConf:el("cardConf"),valConf:el("valConf"),accLabel:el("accLabel"),
  sparkA:el("sparkA"),sparkB:el("sparkB"),
  liveBadge:el("liveBadge"),liveDot:el("liveDot"),liveBadgeText:el("liveBadgeText"),
  liveHere:el("liveHere"),liveRoom:el("liveRoom"),liveAcc:el("liveAcc"),liveTime:el("liveTime"),
  radarR1:el("radarR1"),radarR2:el("radarR2"),radarR3:el("radarR3"),radarCenter:el("radarCenter"),
  activityList:el("activityList"),
  fpLocation:el("fpLocation"),
};

function now12(){
  const d=new Date(),pad=n=>String(n).padStart(2,"0");
  const h=d.getHours(),ampm=h>=12?"PM":"AM",h12=h%12||12;
  return `${pad(h12)}:${pad(d.getMinutes())}:${pad(d.getSeconds())} ${ampm}`;
}

function addLog(msg,dotClass="act-dot--purple"){
  logItems.unshift({time:now12(),msg,dotClass});
  if(logItems.length>60)logItems.pop();
  dom.activityList.innerHTML=logItems.map(e=>`
    <div class="activity-item">
      <div class="act-time">${e.time}</div>
      <div class="act-dot ${e.dotClass}"></div>
      <div class="act-content"><div class="act-content__title">${e.msg}</div></div>
    </div>`).join("");
}

function drawSparkline(canvas,data,color){
  const ctx=canvas.getContext("2d"),W=canvas.width,H=canvas.height,pad=4;
  ctx.clearRect(0,0,W,H);
  if(data.length<2)return;
  const min=Math.min(...data)-5,max=Math.max(...data)+5,range=max-min||1;
  const toX=i=>pad+(i/(SPARKLINE_LEN-1))*(W-2*pad);
  const toY=v=>H-pad-((v-min)/range)*(H-2*pad);
  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,color+"44");grad.addColorStop(1,color+"00");
  ctx.beginPath();
  data.forEach((v,i)=>{const xi=toX(i+(SPARKLINE_LEN-data.length));i===0?ctx.moveTo(xi,toY(v)):ctx.lineTo(xi,toY(v));});
  ctx.lineTo(toX(SPARKLINE_LEN-1),H);ctx.lineTo(toX(SPARKLINE_LEN-data.length),H);
  ctx.closePath();ctx.fillStyle=grad;ctx.fill();
  ctx.beginPath();
  data.forEach((v,i)=>{const xi=toX(i+(SPARKLINE_LEN-data.length));i===0?ctx.moveTo(xi,toY(v)):ctx.lineTo(xi,toY(v));});
  ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.shadowColor=color;ctx.shadowBlur=4;ctx.stroke();ctx.shadowBlur=0;
}

function applyOnline(d){
  // Demo pill
  if(d.mode==="DEMO"){
    dom.demoPill.style.display="flex";
    dom.banner.classList.remove("hidden");
    dom.bannerText.textContent="Demo Mode — simulated data. Connect ESP32 for live data.";
    dom.bannerRetry.textContent="● Demo active";
  } else {
    dom.demoPill.style.display="none";
    dom.banner.classList.add("hidden");
  }

  dom.statusChip.className="status-chip online";
  dom.chipDot.className="status-chip__dot online";
  dom.chipValue.className="status-chip__value online";
  dom.chipValue.textContent=d.system_state==="TRACKING"?"TRACKING":"ONLINE";

  dom.sysDot.className="sys-dot online";
  dom.sysStatusText.className="sys-value online";
  dom.sysStatusText.textContent="ONLINE";

  [dom.cardA,dom.cardB,dom.cardLoc,dom.cardConf].forEach(c=>c.classList.remove("dimmed"));

  dom.valA.textContent=d.beaconA!==null?d.beaconA:"—";
  dom.unitA.textContent=d.beaconA!==null?" dBm":"";
  dom.subA.textContent=d.beaconA_status||"—";

  dom.valB.textContent=d.beaconB!==null?d.beaconB:"—";
  dom.unitB.textContent=d.beaconB!==null?" dBm":"";
  dom.subB.textContent=d.beaconB_status||"—";

  dom.valLoc.textContent=d.location!=="UNKNOWN"?d.location:"—";
  dom.subLoc.textContent=d.location!=="UNKNOWN"?"Building A · Floor 1":"Detecting…";

  dom.valConf.textContent=d.confidence>0?`${d.confidence}%`:"—";
  dom.accLabel.textContent=d.accuracy_label||"—";
  dom.accLabel.className=d.confidence>=85?"mcard__sub mcard__sub--green":"mcard__sub";

  dom.liveBadge.className="live-badge online";
  dom.liveDot.className="live-dot active";
  dom.liveBadgeText.textContent="LIVE";
  dom.liveHere.textContent="You are here";
  dom.liveRoom.textContent=d.location!=="UNKNOWN"?d.location:"Detecting…";
  dom.liveAcc.textContent=d.confidence>0?`${d.confidence}%`:"—";
  dom.liveTime.textContent=now12();

  dom.radarCenter.classList.remove("offline");
  [dom.radarR1,dom.radarR2,dom.radarR3].forEach(r=>r.classList.remove("paused"));

  if(d.location&&d.location!=="UNKNOWN"){
    const pos=ZONE_POS[d.location]||ZONE_POS["Corridor"];
    dom.fpLocation.style.left=pos.left;
    dom.fpLocation.style.top=pos.top;
    dom.fpLocation.style.display="flex";
    document.querySelectorAll(".fp-room").forEach(r=>r.classList.remove("fp-room--active"));
    const zone=document.getElementById(`zone-${d.location}`);
    if(zone)zone.classList.add("fp-room--active");
  }

  if(d.beaconA!==null){sparkA.push(d.beaconA);if(sparkA.length>SPARKLINE_LEN)sparkA.shift();}
  if(d.beaconB!==null){sparkB.push(d.beaconB);if(sparkB.length>SPARKLINE_LEN)sparkB.shift();}
  drawSparkline(dom.sparkA,sparkA,"#3b82f6");
  drawSparkline(dom.sparkB,sparkB,"#6366f1");
}

async function poll(){
  let d;
  try{
    const res=await fetch("/data",{cache:"no-store"});
    if(!res.ok)throw new Error();
    d=await res.json();
  }catch{
    dom.chipValue.textContent="SERVER ERROR";
    return;
  }

  const conn=d.connection,state=d.system_state;

  if(conn==="ONLINE"||state==="TRACKING"||state==="WAITING"){
    applyOnline(d);
    if(prevConn==="DISCONNECTED"||prevConn==="IDLE")addLog("✓ ESP32 connected — ONLINE","act-dot--green");
    if(prevState!=="TRACKING"&&state==="TRACKING")addLog("✓ Tracking started","act-dot--green");
    if(prevLoc!==null&&prevLoc!==d.location&&d.location!=="UNKNOWN")addLog(`→ Moved to ${d.location}`,"act-dot--purple");
  } else {
    // Disconnected — but demo simulation will take over from server
    // so this state is brief only on first load
    dom.statusChip.className="status-chip offline";
    dom.chipDot.className="status-chip__dot offline";
    dom.chipValue.className="status-chip__value offline";
    dom.chipValue.textContent="CONNECTING…";
    dom.sysDot.className="sys-dot offline";
    dom.sysStatusText.className="sys-value offline";
    dom.sysStatusText.textContent="OFFLINE";
    dom.radarCenter.classList.add("offline");
    [dom.radarR1,dom.radarR2,dom.radarR3].forEach(r=>r.classList.add("paused"));
    dom.liveBadge.className="live-badge offline";
    dom.liveDot.className="live-dot inactive";
    dom.liveBadgeText.textContent="OFFLINE";
    dom.fpLocation.style.display="none";
  }

  prevConn=conn;prevState=state;prevLoc=d.location;
}

addLog("Dashboard initialised","act-dot--purple");
poll();
setInterval(poll,POLL_MS);
