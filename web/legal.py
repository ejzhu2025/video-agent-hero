"""web/legal.py — Privacy Policy and Terms of Service pages."""

_SHARED_STYLE = """
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #000;
    color: rgba(255,255,255,.85);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
    line-height: 1.7;
    padding: 60px 24px 120px;
  }
  .wrap { max-width: 720px; margin: 0 auto; }
  h1 { font-size: 36px; font-weight: 700; letter-spacing: -.03em; margin-bottom: 8px; color: #fff; }
  .updated { font-size: 13px; color: rgba(255,255,255,.35); margin-bottom: 48px; }
  h2 { font-size: 18px; font-weight: 600; margin: 36px 0 10px; color: #fff; }
  p, li { font-size: 15px; color: rgba(255,255,255,.65); }
  ul { padding-left: 20px; margin-top: 8px; }
  li { margin-bottom: 6px; }
  a { color: #C9A84C; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .back { display: inline-block; margin-bottom: 40px; font-size: 14px; color: rgba(255,255,255,.4); }
  .back:hover { color: #fff; }
</style>
"""

PRIVACY_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Privacy Policy — AdReel</title>
{_SHARED_STYLE}
</head>
<body>
<div class="wrap">
  <a href="/" class="back">← AdReel</a>
  <h1>Privacy Policy</h1>
  <p class="updated">Last updated: March 21, 2026</p>

  <h2>1. Overview</h2>
  <p>AdReel Studio ("AdReel", "we", "us") operates adreel.studio. This policy explains what data we collect, how we use it, and your rights.</p>

  <h2>2. Data We Collect</h2>
  <ul>
    <li><strong>Account data:</strong> Email address and name when you sign in via Google OAuth.</li>
    <li><strong>Usage data:</strong> Projects you create, briefs you submit, and videos you generate.</li>
    <li><strong>Brand URLs:</strong> URLs you submit for ad generation (scraped to extract publicly available brand information).</li>
    <li><strong>Payment data:</strong> Handled entirely by Stripe. We do not store card numbers.</li>
    <li><strong>Log data:</strong> IP address, browser type, and request timestamps for security and debugging.</li>
  </ul>

  <h2>3. How We Use Your Data</h2>
  <ul>
    <li>To generate AI video ads based on your briefs and brand inputs.</li>
    <li>To manage your account, credits, and project history.</li>
    <li>To improve our AI models and service quality.</li>
    <li>To send transactional emails (e.g. credit receipts). We do not send marketing emails without consent.</li>
  </ul>

  <h2>4. Third-Party Services</h2>
  <p>We use the following services to operate AdReel:</p>
  <ul>
    <li><strong>Anthropic</strong> — AI text generation (prompts and briefs are sent to Anthropic's API).</li>
    <li><strong>fal.ai / Replicate</strong> — Video generation (prompts are sent to these services).</li>
    <li><strong>Google OAuth</strong> — Authentication.</li>
    <li><strong>Stripe</strong> — Payment processing.</li>
    <li><strong>TikTok API</strong> — Video publishing to TikTok (only when you authorize it).</li>
  </ul>

  <h2>5. Data Retention</h2>
  <p>Generated videos and project data are retained for 90 days after your last activity. You may request earlier deletion by contacting us.</p>

  <h2>6. Your Rights</h2>
  <p>You may request access to, correction of, or deletion of your personal data at any time by emailing <a href="mailto:hello@adreel.studio">hello@adreel.studio</a>.</p>

  <h2>7. Cookies</h2>
  <p>We use a single HTTP-only session cookie for authentication. We do not use tracking or advertising cookies.</p>

  <h2>8. Children</h2>
  <p>AdReel is not directed to children under 13. We do not knowingly collect data from children.</p>

  <h2>9. Changes</h2>
  <p>We may update this policy. Continued use of AdReel after changes constitutes acceptance.</p>

  <h2>10. Contact</h2>
  <p>Questions? Email <a href="mailto:hello@adreel.studio">hello@adreel.studio</a>.</p>
</div>
</body>
</html>"""

TERMS_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Terms of Service — AdReel</title>
{_SHARED_STYLE}
</head>
<body>
<div class="wrap">
  <a href="/" class="back">← AdReel</a>
  <h1>Terms of Service</h1>
  <p class="updated">Last updated: March 21, 2026</p>

  <h2>1. Acceptance</h2>
  <p>By using AdReel Studio at adreel.studio ("Service"), you agree to these Terms. If you do not agree, do not use the Service.</p>

  <h2>2. Description</h2>
  <p>AdReel is an AI-powered video ad generation platform. You submit a brand brief; our system produces a short-form video advertisement.</p>

  <h2>3. Accounts and Credits</h2>
  <ul>
    <li>You must sign in via Google OAuth to use the Service.</li>
    <li>Credits are purchased in advance and consumed per video generated.</li>
    <li>Credits are non-refundable once a generation has started.</li>
    <li>Unused credits expire 12 months after purchase.</li>
  </ul>

  <h2>4. Acceptable Use</h2>
  <p>You agree not to use AdReel to:</p>
  <ul>
    <li>Generate content that is illegal, deceptive, or defamatory.</li>
    <li>Infringe third-party intellectual property rights.</li>
    <li>Submit brand URLs you do not have permission to advertise.</li>
    <li>Attempt to reverse-engineer or circumvent the Service.</li>
    <li>Resell or redistribute generated videos without attribution.</li>
  </ul>

  <h2>5. Intellectual Property</h2>
  <p>You own the videos generated using your account, subject to the licenses of the underlying AI services (Anthropic, fal.ai, Replicate). AdReel retains no ownership over your output.</p>

  <h2>6. Brand Content</h2>
  <p>When you submit a brand URL, you represent that you have the right to create advertising content for that brand. AdReel is not responsible for unauthorized use of third-party brand assets.</p>

  <h2>7. Disclaimers</h2>
  <p>The Service is provided "as is." We make no warranties regarding video quality, uptime, or fitness for a particular purpose. AI-generated content may contain errors.</p>

  <h2>8. Limitation of Liability</h2>
  <p>AdReel's liability is limited to the amount you paid in the 3 months preceding a claim. We are not liable for indirect or consequential damages.</p>

  <h2>9. Termination</h2>
  <p>We may suspend or terminate accounts that violate these Terms at our discretion.</p>

  <h2>10. Governing Law</h2>
  <p>These Terms are governed by the laws of the State of California, USA.</p>

  <h2>11. Contact</h2>
  <p>Questions? Email <a href="mailto:hello@adreel.studio">hello@adreel.studio</a>.</p>
</div>
</body>
</html>"""
