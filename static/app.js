const uploadZone = document.getElementById('uploadZone');
const imageInput = document.getElementById('imageInput');
const uploadBtn = document.getElementById('uploadBtn');
const removeImg = document.getElementById('removeImg');
const previewWrap = document.getElementById('previewWrap');
const previewImg = document.getElementById('previewImg');
const analyzeBtn = document.getElementById('analyzeBtn');
const cityInput = document.getElementById('city');
const cropInput = document.getElementById('cropInput');
const resultsPanel = document.getElementById('resultsPanel');
const diseaseName = document.getElementById('diseaseName');
const severityBadge = document.getElementById('severityBadge');
const recommendationEl = document.getElementById('recommendation');
const confidenceFill = document.getElementById('confidenceFill');
const weatherContent = document.getElementById('weatherContent');
const marketContent = document.getElementById('marketContent');
const newAnalysis = document.getElementById('newAnalysis');
const navLogo = document.getElementById('navLogo');
const uploadLogo = document.getElementById('uploadLogo');

let selectedFile = null;

// Note: we require the user to type both city and crop — no selection dropdowns.

uploadZone.addEventListener('click', ()=> imageInput.click());
uploadBtn.addEventListener('click', (e)=>{ e.stopPropagation(); imageInput.click(); });

imageInput.addEventListener('change', (e)=>{
  if(e.target.files && e.target.files[0]){
    selectedFile = e.target.files[0];
    showPreview(selectedFile);
  }
});

function showPreview(file){
  const reader = new FileReader();
  reader.onload = function(evt){
    previewImg.src = evt.target.result;
    previewWrap.classList.remove('hidden');
  };
  reader.readAsDataURL(file);
}

removeImg.addEventListener('click', ()=>{
  selectedFile = null; imageInput.value = ''; previewImg.src=''; previewWrap.classList.add('hidden');
});

newAnalysis.addEventListener('click', ()=>{
  // reset UI
  selectedFile = null; imageInput.value = ''; previewImg.src=''; previewWrap.classList.add('hidden');
  cityInput.value=''; cropInput.value=''; resultsPanel.classList.add('hidden');
});

// Optional: Set logo images by providing URLs
// Example: navLogo.src = 'path/to/logo.png'; navLogo.style.display = 'block';
// Example: uploadLogo.src = 'path/to/logo.png'; uploadLogo.style.display = 'block';

function setSeverityBadge(sev){
  severityBadge.className = 'severity';
  if(!sev) { severityBadge.textContent='-'; return; }
  const s = (''+sev).toLowerCase();
  if(s.includes('high')||s.includes('severe')){ severityBadge.classList.add('high'); severityBadge.textContent='High Severity'; }
  else if(s.includes('medium')||s.includes('moderate')){ severityBadge.classList.add('medium'); severityBadge.textContent='Medium Severity'; }
  else { severityBadge.classList.add('low'); severityBadge.textContent='Low Severity'; }
}

async function doAnalyze(){
  if(!selectedFile){ alert('Please upload a leaf image'); return; }
  const city = cityInput.value.trim();
  const crop = cropInput.value.trim();
  if(!city){ alert('Please enter your location'); cityInput.focus(); return; }
  if(!crop){ alert('Please select a crop'); cropSelect.focus(); return; }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = 'Analyzing...';

  const fd = new FormData(); fd.append('image', selectedFile); fd.append('city', city); fd.append('crop', crop);

  try{
    const res = await fetch('/api/diagnose', { method:'POST', body: fd });
    if(!res.ok) throw new Error('Server ' + res.status);
    const data = await res.json();

    // populate results
    const v = data.vision_result || {};
    diseaseName.textContent = v.disease || 'Not detected';
    recommendationEl.textContent = v.recommendation || 'No recommendation available';
    setSeverityBadge(v.severity || (v.confidence>0.6? 'Medium':'Low'));
    const conf = Math.round((v.confidence||0)*100);
    confidenceFill.style.width = (conf)+'%';

    const w = data.weather || {};
    const precipText = (w.precipitation === null || w.precipitation === undefined) ? 'N/A' : (w.precipitation + ' mm');
    weatherContent.innerHTML = `<p><strong>${w.city || city}</strong></p>
      <p class="muted">${w.condition || 'N/A'}</p>
      <p>Temp: ${w.temperature ?? 'N/A'} °C · Humidity: ${w.humidity ?? 'N/A'}%</p>
      <p>Wind: ${w.wind_speed ?? 'N/A'} m/s · Precipitation: ${precipText}</p>`;

    const m = data.mandi_prices || {};
    let marketHtml = `<p><strong>${m.commodity || crop}</strong> · ${m.city || city} · ${m.date || ''}</p>`;
    if(Array.isArray(m.prices) && m.prices.length){
      marketHtml += '<ul>' + m.prices.map(p=>`<li>${p.market}: ₹${p.modal_price} (min ₹${p.min_price} — max ₹${p.max_price})</li>`).join('') + '</ul>';
    } else {
      marketHtml += `<div class="muted">Market data unavailable</div>`;
    }
    marketContent.innerHTML = marketHtml;

    resultsPanel.classList.remove('hidden');
  }catch(err){
    alert('Analysis failed: ' + err.message);
  }finally{
    analyzeBtn.disabled = false; analyzeBtn.textContent = 'Analyze Crop Health';
  }
}

analyzeBtn.addEventListener('click', doAnalyze);

