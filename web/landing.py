_LANDING_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>AdReel — AI Video Ads in Minutes</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  :root { --bg: #000; --text: #fff; --text2: rgba(255,255,255,.56); --sep: rgba(255,255,255,.08); }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
  }

  /* ── Gradient text ── */
  .grad {
    background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,.72) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .grad-blue {
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* ── Noise / glow bg ── */
  .hero-glow {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,.18) 0%, transparent 70%),
      radial-gradient(ellipse 60% 40% at 80% 50%, rgba(168,85,247,.10) 0%, transparent 60%);
    pointer-events: none;
  }

  /* ── Nav ── */
  nav {
    position: fixed; top: 0; left: 0; right: 0; z-index: 100;
    backdrop-filter: saturate(180%) blur(20px);
    -webkit-backdrop-filter: saturate(180%) blur(20px);
    background: rgba(0,0,0,.72);
    border-bottom: 1px solid var(--sep);
  }
  .nav-inner {
    max-width: 1100px; margin: 0 auto;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px; height: 52px;
  }
  .nav-logo { font-size: 17px; font-weight: 600; letter-spacing: -.3px; }
  .btn-try {
    background: #fff; color: #000;
    font-size: 13px; font-weight: 600;
    padding: 7px 18px; border-radius: 980px;
    border: none; cursor: pointer;
    transition: opacity .2s;
  }
  .btn-try:hover { opacity: .85; }

  /* ── Hero ── */
  .hero {
    position: relative;
    min-height: 100svh;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center;
    padding: 120px 24px 80px;
    overflow: hidden;
  }
  .eyebrow {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase;
    color: rgba(255,255,255,.5);
    border: 1px solid rgba(255,255,255,.12);
    padding: 5px 14px; border-radius: 980px;
    margin-bottom: 28px;
    background: rgba(255,255,255,.04);
  }
  .eyebrow-dot { width: 6px; height: 6px; border-radius: 50%; background: #30d158; flex-shrink: 0; }
  h1 {
    font-size: clamp(44px, 7vw, 80px);
    font-weight: 700;
    line-height: 1.06;
    letter-spacing: -.03em;
    max-width: 820px;
    margin-bottom: 22px;
  }
  .hero-sub {
    font-size: clamp(17px, 2vw, 21px);
    color: var(--text2);
    max-width: 520px;
    line-height: 1.55;
    font-weight: 400;
    margin-bottom: 48px;
  }

  /* ── URL input ── */
  .url-form {
    display: flex; gap: 10px; align-items: center;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.14);
    border-radius: 14px;
    padding: 6px 6px 6px 18px;
    width: 100%; max-width: 540px;
    transition: border-color .2s, box-shadow .2s;
  }
  .url-form:focus-within {
    border-color: rgba(255,255,255,.35);
    box-shadow: 0 0 0 3px rgba(255,255,255,.06);
  }
  .url-input {
    flex: 1; background: transparent; border: none; outline: none;
    color: #fff; font-size: 15px; font-weight: 400;
    min-width: 0;
  }
  .url-input::placeholder { color: rgba(255,255,255,.3); }
  .btn-generate {
    background: #fff; color: #000;
    font-size: 14px; font-weight: 600;
    padding: 10px 22px; border-radius: 10px;
    border: none; cursor: pointer; white-space: nowrap;
    transition: opacity .15s, transform .15s;
    flex-shrink: 0;
  }
  .btn-generate:hover { opacity: .88; transform: scale(.98); }
  .btn-generate:active { transform: scale(.96); }
  .url-hint {
    margin-top: 12px;
    font-size: 12px; color: rgba(255,255,255,.28);
  }

  /* ── Demo videos section ── */
  .demos {
    max-width: 1100px; margin: 0 auto;
    padding: 0 24px 120px;
  }
  .demos-label {
    text-align: center;
    font-size: 12px; font-weight: 500; letter-spacing: .08em; text-transform: uppercase;
    color: rgba(255,255,255,.3);
    margin-bottom: 52px;
  }
  .phones {
    display: flex; gap: 28px; justify-content: center; align-items: flex-end;
    flex-wrap: wrap;
  }

  /* iPhone mockup */
  .phone-wrap {
    display: flex; flex-direction: column; align-items: center; gap: 16px;
    flex: 0 0 auto;
  }
  .phone-wrap.center-phone { transform: translateY(-28px); }

  .phone-frame {
    position: relative;
    width: 200px; height: 433px;
    border-radius: 36px;
    background: #1c1c1e;
    border: 2px solid rgba(255,255,255,.14);
    overflow: hidden;
    box-shadow:
      0 40px 80px rgba(0,0,0,.7),
      0 0 0 .5px rgba(255,255,255,.04) inset,
      0 2px 4px rgba(255,255,255,.06) inset;
  }
  .phone-wrap.center-phone .phone-frame {
    width: 230px; height: 498px;
    border-radius: 40px;
    box-shadow:
      0 60px 100px rgba(0,0,0,.8),
      0 0 60px rgba(99,102,241,.15),
      0 0 0 .5px rgba(255,255,255,.06) inset;
  }

  /* Notch */
  .phone-frame::before {
    content: '';
    position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
    width: 80px; height: 22px;
    background: #000; border-radius: 12px;
    z-index: 10;
  }

  .phone-video {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
  }

  /* Reflection overlay */
  .phone-frame::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,.06) 0%, transparent 50%);
    pointer-events: none; z-index: 5;
  }

  .phone-label {
    font-size: 13px; color: rgba(255,255,255,.45); font-weight: 500;
    text-align: center; max-width: 180px; line-height: 1.4;
  }

  /* ── How it works ── */
  .how {
    border-top: 1px solid var(--sep);
    padding: 100px 24px;
    text-align: center;
  }
  .how-inner { max-width: 900px; margin: 0 auto; }
  .how h2 {
    font-size: clamp(32px, 5vw, 54px);
    font-weight: 700; letter-spacing: -.025em;
    margin-bottom: 14px;
  }
  .how-sub { font-size: 17px; color: var(--text2); margin-bottom: 64px; }
  .steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
  @media (max-width: 640px) { .steps { grid-template-columns: 1fr; } }
  .step {
    background: rgba(255,255,255,.04);
    border: 1px solid var(--sep);
    border-radius: 18px;
    padding: 28px 24px;
    text-align: left;
  }
  .step-num {
    font-size: 12px; font-weight: 600; letter-spacing: .1em;
    color: rgba(255,255,255,.3); text-transform: uppercase;
    margin-bottom: 12px;
  }
  .step-icon { font-size: 28px; margin-bottom: 14px; }
  .step h3 { font-size: 17px; font-weight: 600; margin-bottom: 8px; letter-spacing: -.01em; }
  .step p { font-size: 14px; color: var(--text2); line-height: 1.6; }

  /* ── Bottom CTA ── */
  .bottom-cta {
    border-top: 1px solid var(--sep);
    padding: 100px 24px;
    text-align: center;
  }
  .bottom-cta h2 {
    font-size: clamp(32px, 5vw, 52px);
    font-weight: 700; letter-spacing: -.025em;
    margin-bottom: 18px;
  }
  .bottom-cta p { font-size: 17px; color: var(--text2); margin-bottom: 40px; }

  /* ── Footer ── */
  footer {
    border-top: 1px solid var(--sep);
    padding: 28px 24px;
    text-align: center;
    font-size: 12px; color: rgba(255,255,255,.25);
  }

  /* ── Fade-in animation ── */
  .fade-up {
    opacity: 0; transform: translateY(24px);
    transition: opacity .7s ease, transform .7s ease;
  }
  .fade-up.visible { opacity: 1; transform: translateY(0); }
  .fade-up:nth-child(2) { transition-delay: .1s; }
  .fade-up:nth-child(3) { transition-delay: .2s; }
</style>
</head>
<body>

<!-- Nav -->
<nav>
  <div class="nav-inner">
    <div class="nav-logo">🎬 AdReel</div>
    <button class="btn-try" onclick="goToApp()">Open App</button>
  </div>
</nav>

<!-- Hero -->
<section class="hero">
  <div class="hero-glow"></div>

  <div class="eyebrow">
    <span class="eyebrow-dot"></span>
    AI-Powered Video Ads
  </div>

  <h1 class="grad">
    From product photo<br>to viral video ad.
  </h1>

  <p class="hero-sub">
    Paste a product URL or describe what you're selling.
    AdReel writes the script, generates cinematic shots, and exports
    a broadcast-ready vertical video — in minutes.
  </p>

  <!-- URL input -->
  <div class="url-form" id="hero-form">
    <input
      class="url-input"
      id="hero-url"
      type="url"
      placeholder="Paste a product URL to get started…"
      autocomplete="off"
      spellcheck="false"
    />
    <button class="btn-generate" onclick="handleGenerate()">Generate →</button>
  </div>
  <p class="url-hint">No credit card required · First video free</p>
</section>

<!-- Demo videos -->
<section class="demos">
  <p class="demos-label">Made with AdReel</p>
  <div class="phones">

    <div class="phone-wrap fade-up">
      <div class="phone-frame">
        <video class="phone-video" src="/demos/demo_skincare.mp4"
          autoplay muted loop playsinline></video>
      </div>
      <p class="phone-label">Skincare serum<br>product launch</p>
    </div>

    <div class="phone-wrap center-phone fade-up">
      <div class="phone-frame">
        <video class="phone-video" src="/demos/demo_face_cream.mp4"
          autoplay muted loop playsinline></video>
      </div>
      <p class="phone-label">Face cream<br>product launch</p>
    </div>

    <div class="phone-wrap fade-up">
      <div class="phone-frame">
        <video class="phone-video" src="/demos/demo_beverage.mp4"
          autoplay muted loop playsinline></video>
      </div>
      <p class="phone-label">Lifestyle beverage<br>social campaign</p>
    </div>

  </div>
</section>

<!-- How it works -->
<section class="how">
  <div class="how-inner">
    <h2 class="grad">How it works</h2>
    <p class="how-sub">Three steps. No editing skills needed.</p>
    <div class="steps">
      <div class="step">
        <div class="step-num">Step 01</div>
        <div class="step-icon">🔗</div>
        <h3>Describe your product</h3>
        <p>Paste a URL or describe your product in a sentence. Upload a photo for best results.</p>
      </div>
      <div class="step">
        <div class="step-num">Step 02</div>
        <div class="step-icon">🤖</div>
        <h3>AI writes & shoots</h3>
        <p>Our agent plans the storyboard, generates cinematic AI video clips with your product, and scores it with music.</p>
      </div>
      <div class="step">
        <div class="step-num">Step 03</div>
        <div class="step-icon">📲</div>
        <h3>Export & post</h3>
        <p>Download a ready-to-post 9:16 MP4. Modify any scene with a single message.</p>
      </div>
    </div>
  </div>
</section>

<!-- Bottom CTA -->
<section class="bottom-cta">
  <h2>Ready to make your<br><span class="grad-blue">first ad?</span></h2>
  <p>Paste your product URL below and watch the magic happen.</p>

  <div class="url-form" style="max-width:480px; margin:0 auto;">
    <input
      class="url-input"
      id="bottom-url"
      type="url"
      placeholder="https://your-product-url.com"
      autocomplete="off"
      spellcheck="false"
    />
    <button class="btn-generate" onclick="handleGenerateBottom()">Generate →</button>
  </div>
</section>

<!-- Footer -->
<footer>
  <p>© 2026 AdReel · Built with AI · <a href="/app" style="color:inherit;text-decoration:underline">Open App</a></p>
</footer>

<script>
  function goToApp(url) {
    if (url) {
      window.location.href = '/app?url=' + encodeURIComponent(url);
    } else {
      window.location.href = '/app';
    }
  }

  function handleGenerate() {
    const url = document.getElementById('hero-url').value.trim();
    goToApp(url);
  }

  function handleGenerateBottom() {
    const url = document.getElementById('bottom-url').value.trim();
    goToApp(url);
  }

  // Enter key on both inputs
  document.getElementById('hero-url').addEventListener('keydown', e => {
    if (e.key === 'Enter') handleGenerate();
  });
  document.getElementById('bottom-url').addEventListener('keydown', e => {
    if (e.key === 'Enter') handleGenerateBottom();
  });

  // Scroll fade-in
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
  }, { threshold: 0.15 });
  document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
</script>

</body>
</html>
"""
