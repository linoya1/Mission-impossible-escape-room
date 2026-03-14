// prelude.js — 2 clicks, validate eyes via face-api.js
// Multi-pass detection + forgiving ellipse per eye

if (typeof window.faceapi === "undefined") {
  console.error("face-api failed to load. Check the CDN script tag.");
  const statusEl = document.getElementById("status");
  if (statusEl) statusEl.textContent = "AI unavailable — face-api not loaded.";
} else {
(async () => {
  const MODEL_URL = (window.FACE_MODELS || "/static/models").replace(/\/+$/, "");
  const DEBUG = false; // true = draw ellipses for debug

  const statusEl  = document.getElementById("status");
  const hintEl    = document.getElementById("hint");
  const sysStatus = document.getElementById("sys-status");
  const sceneImg  = document.getElementById("scene-img");
  const canvas    = document.getElementById("overlay-canvas");
  const systemImg = document.getElementById("system-working");
  const revealImg = document.getElementById("corridor-reveal");
  const nextBtn   = document.getElementById("next-room-btn");
  const ctx       = canvas.getContext("2d");

  const fitCanvas = () => {
    canvas.width = sceneImg.clientWidth;
    canvas.height = sceneImg.clientHeight;
    Object.assign(canvas.style,{width:canvas.width+"px",height:canvas.height+"px"});
  };
  const clearOverlay = () => ctx.clearRect(0,0,canvas.width,canvas.height);
  const drawCross = (x,y,color="#ffc628") => {
    ctx.save(); ctx.lineWidth=2; ctx.strokeStyle=color;
    ctx.beginPath(); ctx.moveTo(x-10,y); ctx.lineTo(x+10,y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x,y-10); ctx.lineTo(x,y+10); ctx.stroke();
    ctx.restore();
  };
  const dist = (a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  const centroid = pts => {
    const s = pts.reduce((acc,p)=>({x:acc.x+p.x,y:acc.y+p.y}),{x:0,y:0});
    return {x:s.x/pts.length,y:s.y/pts.length};
  };
  const drawEllipse = (cx,cy,rx,ry,color="#49f")=>{
    if(!DEBUG) return;
    ctx.save(); ctx.lineWidth=2; ctx.strokeStyle=color;
    ctx.beginPath(); ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2); ctx.stroke();
    ctx.restore();
  };
  const withinEyeEllipse = (p, c, eyeW) => {
    const rx = Math.max(14, eyeW*1.10);
    const ry = Math.max(12, eyeW*0.85);
    const nx = (p.x-c.x)/rx, ny=(p.y-c.y)/ry;
    return nx*nx + ny*ny <= 1;
  };

  if (!sceneImg.complete) await new Promise(r=>sceneImg.onload=r);
  fitCanvas(); window.addEventListener("resize", fitCanvas);

  // load models
  statusEl.textContent = "Loading AI models…";
  try {
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
    try { await faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL); }
    catch { await faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL); }
  } catch (e) {
    console.error("[face-api] load failed", e);
    statusEl.textContent = "AI unavailable — models failed to load.";
    return;
  }

  // detect multi-pass
  statusEl.textContent = "Analyzing scene…";
  const passes = [
    { inputSize: 640, scoreThreshold: 0.12 },
    { inputSize: 512, scoreThreshold: 0.10 },
    { inputSize: 416, scoreThreshold: 0.08 },
  ];
  let detRaw = null;
  for (const p of passes) {
    try {
      const d = await faceapi
        .detectSingleFace(sceneImg,new faceapi.TinyFaceDetectorOptions(p))
        .withFaceLandmarks();
      if (d && d.landmarks) { detRaw = d; break; }
    } catch {}
  }
  if (!detRaw) {
    statusEl.textContent = "AI couldn’t confirm eye positions. Try again.";
    hintEl.style.display = "inline";
  }

  const det = detRaw ? faceapi.resizeResults(detRaw,{width:canvas.width,height:canvas.height}) : null;

  // compute eyes
  let eyeL=null, eyeR=null, eyeW=30;
  let tol = Math.max(14, Math.round(canvas.width*0.028));

  if (det && det.landmarks) {
    const re = det.landmarks.getRightEye();
    const le = det.landmarks.getLeftEye();
    eyeR = centroid(re); eyeL = centroid(le);
    const reW = dist(re[0],re[3]);
    const leW = dist(le[0],le[3]);
    eyeW = Math.max(reW, leW);
    tol = Math.max(tol, Math.round(eyeW*1.6));
    if (DEBUG) {
      drawEllipse(eyeR.x, eyeR.y, Math.max(14,eyeW*1.10),Math.max(12,eyeW*0.85));
      drawEllipse(eyeL.x, eyeL.y, Math.max(14,eyeW*1.10),Math.max(12,eyeW*0.85));
    }
  }

  hintEl.style.display="inline"; clearOverlay();

  // clicks
  const picks=[];
  canvas.addEventListener("click", (ev)=>{
    if(picks.length>=2) return;
    if(!(eyeL&&eyeR)) { statusEl.textContent="AI couldn’t confirm eye positions."; return; }
    const r=canvas.getBoundingClientRect();
    const p={x:ev.clientX-r.left,y:ev.clientY-r.top};
    picks.push(p);
    drawCross(p.x,p.y,picks.length===1?"#ffc628":"#4fd1c5");
    if(picks.length===1){statusEl.textContent="Good. Pick the second point."; return;}

    const a=picks[0], b=picks[1];
    const within=(pt,c)=>dist(pt,c)<=tol;
    const zone=(pt,c)=>withinEyeEllipse(pt,c,Math.max(24,eyeW));

    const ok=((within(a,eyeL)||zone(a,eyeL))&&(within(b,eyeR)||zone(b,eyeR)))||
             ((within(a,eyeR)||zone(a,eyeR))&&(within(b,eyeL)||zone(b,eyeL)));

    if(!ok){statusEl.textContent="These points aren’t on the eyes. Try again."; picks.length=0; setTimeout(clearOverlay,120); return;}

    // success
    hintEl.style.display="none";
    sysStatus.textContent="Projection running";
    systemImg.style.display="block"; systemImg.classList.add("pulse");

    const flash=document.createElement("div");
    Object.assign(flash.style,{position:"fixed",inset:0,background:"rgba(180,255,160,0.12)",pointerEvents:"none",transition:"opacity 550ms ease-out"});
    document.body.appendChild(flash);
    setTimeout(()=>flash.style.opacity="0",60);

    setTimeout(()=>{
      flash.remove(); clearOverlay();
      if(revealImg) revealImg.style.display="block";
      if(nextBtn) nextBtn.style.display="inline-block";
      statusEl.textContent="Guard’s LED reflects the corridor — proceed.";
      sysStatus.textContent="Projection locked";
      fetch("/prelude/event",{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({event:"prelude_reveal_points_validated",success:true})
      }).catch(()=>{});
    },700);
  });
})();
}
