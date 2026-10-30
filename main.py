from flask import Flask, render_template_string

app = Flask(__name__)

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>RITESH | EXPLOITS LUDO - 30 Points</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body {
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: flex-start;
        font-family: 'Segoe UI', system-ui, sans-serif;
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        background-attachment: fixed;
        overflow-x: hidden;
        padding: 10px;
    }
    body::before {
        content: '';
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(circle at 20% 30%, rgba(255,215,0,0.15), transparent 40%),
                    radial-gradient(circle at 80% 70%, rgba(0,255,255,0.12), transparent 40%);
        pointer-events: none;
        z-index: 0;
    }
    .glass-container {
        position: relative;
        z-index: 1;
        width: 100%;
        max-width: 500px;
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.25);
        box-shadow: 0 25px 50px rgba(0,0,0,0.6),
                    inset 0 1px 0 rgba(255,255,255,0.4);
        padding: 1.2rem;
        color: #fff;
    }
    h1 {
        font-size: clamp(1.3rem, 5vw, 1.9rem);
        text-align: center;
        background: linear-gradient(45deg, #ffd700, #ffaa00, #fff8e7, #ffd700);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s infinite linear;
        letter-spacing: 1px;
    }
    @keyframes shine {
        0% { background-position: 0% 50%; }
        100% { background-position: 300% 50%; }
    }
    .subtitle {
        text-align: center;
        font-size: 0.8rem;
        color: #ffd700;
        margin-top: 4px;
        letter-spacing: 2px;
    }
    .players-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin: 1rem 0;
        position: relative;
    }
    .player-card {
        background: rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 0.7rem;
        text-align: center;
        border: 2px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: visible;
    }
    .player-card.active {
        border-color: #ffd700;
        box-shadow: 0 0 20px rgba(255,215,0,0.6), inset 0 0 12px rgba(255,215,0,0.15);
        transform: scale(1.03);
    }
    .player-card.winner {
        border-color: #00ff88;
        box-shadow: 0 0 25px rgba(0,255,136,0.7);
    }
    .player-card .name {
        font-weight: 700;
        font-size: 0.85rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .player-card .score {
        font-size: 1.4rem;
        font-weight: 900;
        color: #ffd700;
        text-shadow: 0 0 10px rgba(255,215,0,0.5);
    }
    .player-card .color-dot {
        display: inline-block;
        width: 10px; height: 10px;
        border-radius: 50%;
        margin-right: 5px;
        vertical-align: middle;
    }
    .progress-bar {
        height: 4px;
        background: rgba(0,0,0,0.4);
        border-radius: 2px;
        margin-top: 6px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #ffd700, #ffaa00);
        border-radius: 2px;
        transition: width 0.4s ease;
    }
    .turn-banner {
        text-align: center;
        font-size: 1.15rem;
        font-weight: 800;
        padding: 0.8rem;
        border-radius: 14px;
        background: linear-gradient(90deg, rgba(255,215,0,0.25), rgba(255,140,0,0.25));
        border: 2px solid rgba(255,215,0,0.5);
        margin: 0.6rem 0;
        animation: bannerPulse 1.5s infinite alternate;
    }
    @keyframes bannerPulse {
        from { box-shadow: 0 0 10px rgba(255,215,0,0.4); }
        to   { box-shadow: 0 0 25px rgba(255,215,0,0.9); }
    }
    .roll-announce {
        text-align: center;
        font-size: 1.1rem;
        font-weight: 800;
        padding: 0.6rem;
        border-radius: 12px;
        background: rgba(0,255,136,0.15);
        border: 1px solid rgba(0,255,136,0.5);
        color: #00ff88;
        margin: 0.5rem 0;
        min-height: 2.5rem;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: all 0.3s ease;
    }
    .roll-announce.big {
        animation: bigPop 0.6s ease;
        font-size: 1.4rem;
        background: rgba(255,215,0,0.2);
        border-color: #ffd700;
        color: #ffd700;
    }
    @keyframes bigPop {
        0%   { transform: scale(0.6); opacity: 0; }
        60%  { transform: scale(1.15); opacity: 1; }
        100% { transform: scale(1); }
    }
    .dice-area {
        text-align: center;
        margin: 1rem 0;
    }
    .dice-display {
        font-size: 4rem;
        margin: 0.3rem 0;
        min-height: 5rem;
        display: flex;
        justify-content: center;
        align-items: center;
        filter: drop-shadow(0 0 20px rgba(255,215,0,0.6));
    }
    .dice-display.rolling {
        animation: shake 0.15s infinite;
    }
    @keyframes shake {
        0% { transform: rotate(0deg) scale(1); }
        25% { transform: rotate(-12deg) scale(1.1); }
        50% { transform: rotate(0deg) scale(0.95); }
        75% { transform: rotate(12deg) scale(1.1); }
        100% { transform: rotate(0deg) scale(1); }
    }
    .dice-btn {
        font-size: 1.3rem;
        padding: 0.9rem 2.5rem;
        border-radius: 60px;
        border: none;
        background: linear-gradient(145deg, #ffd700, #b8860b);
        color: #1a1a2e;
        font-weight: 900;
        letter-spacing: 2px;
        cursor: pointer;
        box-shadow: 0 8px 25px rgba(255,215,0,0.45), inset 0 2px 5px rgba(255,255,255,0.6);
        transition: 0.15s;
        width: 100%;
        max-width: 300px;
    }
    .dice-btn:active { transform: scale(0.95); }
    .dice-btn:disabled {
        opacity: 0.35;
        cursor: not-allowed;
        box-shadow: none;
    }
    .log {
        background: rgba(0,0,0,0.35);
        border-radius: 14px;
        padding: 0.7rem;
        height: 80px;
        overflow-y: auto;
        font-size: 0.75rem;
        color: #ccc;
        margin-top: 0.8rem;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .log div { margin-bottom: 2px; }
    .winner-overlay {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.85);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 100;
        flex-direction: column;
        text-align: center;
        padding: 20px;
    }
    .winner-overlay.show { display: flex; animation: fadeIn 0.5s; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .winner-overlay h2 {
        font-size: 2.5rem;
        color: #ffd700;
        text-shadow: 0 0 30px rgba(255,215,0,0.8);
        animation: pulse 1s infinite alternate;
        margin-bottom: 1rem;
    }
    @keyframes pulse {
        from { transform: scale(1); }
        to { transform: scale(1.08); }
    }
    .winner-overlay p { font-size: 1.2rem; color: #fff; margin-bottom: 0.6rem; }
    .winner-gali {
        font-size: 1.1rem;
        color: #ff6b6b;
        font-weight: 800;
        margin-bottom: 1.5rem;
        background: rgba(255,0,0,0.15);
        padding: 0.7rem 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255,0,0,0.4);
        max-width: 90%;
    }
    .restart-btn {
        padding: 1rem 3rem;
        border-radius: 50px;
        border: none;
        background: linear-gradient(145deg, #ffd700, #b8860b);
        color: #1a1a2e;
        font-weight: 900;
        font-size: 1.1rem;
        cursor: pointer;
    }
    .setup-screen { text-align: center; }
    .setup-screen h2 { font-size: 1.1rem; margin: 1rem 0; color: #ffd700; }
    .name-input {
        width: 100%;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.2);
        background: rgba(0,0,0,0.35);
        color: white;
        font-size: 1rem;
        outline: none;
        margin-bottom: 8px;
    }
    .name-input:focus { border-color: #ffd700; }
    .start-btn {
        padding: 1rem 3rem;
        border-radius: 50px;
        border: none;
        background: linear-gradient(145deg, #00ff88, #008844);
        color: #001a0d;
        font-weight: 900;
        font-size: 1.1rem;
        cursor: pointer;
        margin-top: 1rem;
        width: 100%;
        box-shadow: 0 8px 25px rgba(0,255,136,0.4);
    }
    .sound-toggle {
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 50%;
        width: 40px; height: 40px;
        font-size: 1.2rem;
        cursor: pointer;
        color: white;
        z-index: 10;
    }
    #ytPlayer { position: absolute; width: 0; height: 0; overflow: hidden; opacity: 0; pointer-events: none; }

    /* Emoji burst */
    .emoji-burst {
        position: fixed;
        font-size: 2rem;
        pointer-events: none;
        z-index: 9999;
        animation: floatUp 1.4s ease-out forwards;
        will-change: transform, opacity;
    }
    @keyframes floatUp {
        0% {
            transform: translate(0, 0) scale(0.5) rotate(0deg);
            opacity: 0;
        }
        20% {
            opacity: 1;
            transform: translate(0, -10px) scale(1.2) rotate(10deg);
        }
        100% {
            transform: translate(var(--dx), var(--dy)) scale(0.6) rotate(var(--rot));
            opacity: 0;
        }
    }
</style>
</head>
<body>

<div id="ytPlayer">
    <div id="ytPlayerInner"></div>
</div>

<div class="glass-container">
    <button class="sound-toggle" id="soundToggle" onclick="toggleSound()" title="Sound On/Off">🔊</button>
    <h1>RITESH | EXPLOITS LUDO</h1>
    <div class="subtitle">🎯 TARGET: 30 POINTS</div>

    <div id="setupScreen" class="setup-screen">
        <h2>4 Players ke naam likhein</h2>
        <input class="name-input" id="p1" placeholder="Player 1 (Red)" value="Player 1">
        <input class="name-input" id="p2" placeholder="Player 2 (Green)" value="Player 2">
        <input class="name-input" id="p3" placeholder="Player 3 (Blue)" value="Player 3">
        <input class="name-input" id="p4" placeholder="Player 4 (Yellow)" value="Player 4">
        <button class="start-btn" onclick="startGame()">🚀 START GAME</button>
    </div>

    <div id="gameScreen" style="display:none;">
        <div class="players-row" id="playersRow"></div>
        <div class="turn-banner" id="turnBanner">Turn</div>
        <div class="roll-announce" id="rollAnnounce"></div>
        <div class="dice-area">
            <div class="dice-display" id="diceDisplay">🎲</div>
            <button class="dice-btn" id="rollBtn" onclick="rollDice()">🎲 ROLL DICE</button>
        </div>
        <div class="log" id="log"></div>
    </div>
</div>

<div class="winner-overlay" id="winnerOverlay">
    <h2>🏆 WINNER! 🏆</h2>
    <p id="winnerText"></p>
    <div class="winner-gali" id="winnerGali"></div>
    <button class="restart-btn" onclick="restartGame()">🔄 PLAY AGAIN</button>
</div>

<script>
    const COLORS = ['#ff4444', '#44ff44', '#4444ff', '#ffdd44'];
    const TARGET = 30;

    let players = [];
    let turn = 0;
    let gameOver = false;
    let audioCtx = null;
    let soundEnabled = true;
    let hindiVoice = null;

    // ================= YouTube Sound =================
    const YOUTUBE_VIDEO_ID = 'dQw4w9WgXcQ'; // <<<<<< change this if you want a specific sound

    let ytPlayer = null;
    let ytReady = false;
    let ytApiReady = false;

    (function loadYTApi() {
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        document.head.appendChild(tag);
    })();

    window.onYouTubeIframeAPIReady = function() {
        ytApiReady = true;
        createYTPlayer();
    };

    function createYTPlayer() {
        if (!ytApiReady || ytPlayer) return;
        ytPlayer = new YT.Player('ytPlayerInner', {
            height: '1', width: '1',
            videoId: YOUTUBE_VIDEO_ID,
            playerVars: { 'autoplay': 0, 'controls': 0, 'disablekb': 1, 'fs': 0, 'modestbranding': 1, 'rel': 0, 'playsinline': 1 },
            events: {
                'onReady': function(e) { ytReady = true; e.target.setVolume(100); },
                'onError': function() {}
            }
        });
    }

    function playYouTubeSound() {
        if (!soundEnabled) return;
        if (!ytPlayer || !ytReady) { setTimeout(playYouTubeSound, 500); return; }
        try {
            ytPlayer.seekTo(0, true);
            ytPlayer.unMute();
            ytPlayer.setVolume(100);
            ytPlayer.playVideo();
            setTimeout(() => { try { ytPlayer.pauseVideo(); } catch(e) {} }, 3000);
        } catch(e) {}
    }
    // =================================================

    // ============== Gali List (random per spin) ==============
    const SPIN_GALIS = [
        "Bhak Madharchod!",
        "Bhak saale!",
        "Madharchod, kya roll maara!",
        "Bhak bhosdi ke!",
        "Oye Madharchod, aage badh!",
        "Bhak chutiye!",
        "Saale Madharchod, spin maar!",
        "Bhak bhak bhak!",
        "Randi ke, spin toh dekh!",
        "Bhosdi ke, kya number aaya!",
        "Madharchod, tu toh gaya!",
        "Bhak, kya kismat hai teri!",
        "Saale, spin maar ke dikha!",
        "Chutiye, aage badh!",
        "Bhak Madharchod, haar gaya tu!"
    ];

    function getRandomGali() {
        return SPIN_GALIS[Math.floor(Math.random() * SPIN_GALIS.length)];
    }

    function initAudio() {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (audioCtx.state === 'suspended') audioCtx.resume();
    }

    function pickVoice() {
        if (!('speechSynthesis' in window)) return;
        const voices = window.speechSynthesis.getVoices();
        hindiVoice = voices.find(v => v.lang === 'hi-IN')
                  || voices.find(v => v.lang.startsWith('hi'))
                  || voices.find(v => v.name.toLowerCase().includes('hindi'))
                  || null;
    }
    if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = pickVoice;
        pickVoice();
    }

    function toggleSound() {
        soundEnabled = !soundEnabled;
        document.getElementById('soundToggle').textContent = soundEnabled ? '🔊' : '🔇';
        if (!soundEnabled) {
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
            if (ytPlayer && ytReady) { try { ytPlayer.pauseVideo(); } catch(e) {} }
        }
    }

    function speak(text) {
        if (!soundEnabled || !('speechSynthesis' in window)) return;
        try {
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(text);
            utter.rate = 1.0;
            utter.pitch = 1.1;
            utter.volume = 1.0;
            if (hindiVoice) { utter.voice = hindiVoice; utter.lang = 'hi-IN'; }
            else { utter.lang = 'en-IN'; }
            window.speechSynthesis.speak(utter);
        } catch(e) {}
    }

    function playFunnySound() {
        initAudio();
        if (!audioCtx || !soundEnabled) return;
        const now = audioCtx.currentTime;
        function tone(freq, start, dur, type, vol) {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = type || 'square';
            osc.frequency.setValueAtTime(freq, now + start);
            gain.gain.setValueAtTime(vol || 0.15, now + start);
            gain.gain.exponentialRampToValueAtTime(0.001, now + start + dur);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now + start);
            osc.stop(now + start + dur);
        }
        tone(220, 0, 0.12, 'square', 0.18);
        tone(220, 0.15, 0.12, 'square', 0.18);
        tone(330, 0.30, 0.12, 'square', 0.18);
        tone(440, 0.45, 0.25, 'sawtooth', 0.22);
        tone(880, 0.75, 0.06, 'triangle', 0.12);
        tone(660, 0.83, 0.06, 'triangle', 0.12);
        tone(880, 0.91, 0.06, 'triangle', 0.12);
        tone(990, 0.99, 0.10, 'triangle', 0.12);
        tone(110, 1.15, 0.35, 'sawtooth', 0.25);
    }

    function playCidGaliSound() {
        playFunnySound();
        playYouTubeSound();
        setTimeout(() => speak("Pakad pakad madarchod ko!"), 1300);
    }

    function playWinSound() {
        initAudio();
        if (!audioCtx || !soundEnabled) return;
        const now = audioCtx.currentTime;
        const notes = [523, 659, 784, 1047, 784, 1047, 1319];
        notes.forEach((f, i) => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'triangle';
            osc.frequency.value = f;
            gain.gain.setValueAtTime(0.2, now + i * 0.12);
            gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.12 + 0.3);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now + i * 0.12);
            osc.stop(now + i * 0.12 + 0.3);
        });
        setTimeout(() => playYouTubeSound(), 400);
        setTimeout(() => speak("Winner winner chicken dinner! Jeet gaya!"), 800);
    }

    function playDiceSound() {
        initAudio();
        if (!audioCtx || !soundEnabled) return;
        const now = audioCtx.currentTime;
        for (let i = 0; i < 4; i++) {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'square';
            osc.frequency.value = 200 + Math.random() * 400;
            gain.gain.setValueAtTime(0.08, now + i * 0.06);
            gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.06 + 0.05);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now + i * 0.06);
            osc.stop(now + i * 0.06 + 0.05);
        }
    }

    const WINNER_GALIS = [
        "😂 Itna lucky kaise hai bhai? Kya cheating kar raha tha?",
        "🎉 Jeet gaya tu! Ab jaake mu dho le, kya gandagi macha rakhi hai!",
        "🏆 Winner ban gaya, par akal to abhi bhi nahi aayi! 😜",
        "💀 Haar ke bhi nahi sudhra, ab jeet ke aur bigad jayega!",
        "🤣 Bhai tu jeeta, par style zero hai. Thoda toh sudhar!",
        "😎 Jeet gaya, ab ghamand mat kar, agli baar dhulai pakki hai!",
        "🔥 Aag laga di bhai! Par yeh sab kismat ka khel hai, skill nahi! 😂",
        "🙈 Tu jeeta? Sach me? Kya gadbad hai re! 😂"
    ];

    function getWinnerGali(name) {
        return WINNER_GALIS[Math.floor(Math.random() * WINNER_GALIS.length)];
    }

    // ============ Emoji Burst from player card side ============
    const BURST_EMOJIS = ['🎲','💥','🔥','✨','⚡','💫','🌟','💢','🎯','💣','⭐','🌀'];

    function burstEmojisFromCard(playerIndex) {
        const row = document.getElementById('playersRow');
        if (!row) return;
        const cards = row.querySelectorAll('.player-card');
        const card = cards[playerIndex];
        if (!card) return;

        const rect = card.getBoundingClientRect();
        const originX = rect.left + rect.width / 2;
        const originY = rect.top + rect.height / 2;

        const count = 14;
        for (let i = 0; i < count; i++) {
            const span = document.createElement('span');
            span.className = 'emoji-burst';
            span.textContent = BURST_EMOJIS[Math.floor(Math.random() * BURST_EMOJIS.length)];

            // Random direction (0-360 deg) with distance
            const angle = (Math.PI * 2) * (i / count) + (Math.random() * 0.6 - 0.3);
            const distance = 60 + Math.random() * 110;
            const dx = Math.cos(angle) * distance;
            const dy = Math.sin(angle) * distance - 20; // slight upward bias
            const rot = (Math.random() * 720 - 360) + 'deg';

            span.style.left = originX + 'px';
            span.style.top = originY + 'px';
            span.style.setProperty('--dx', dx + 'px');
            span.style.setProperty('--dy', dy + 'px');
            span.style.setProperty('--rot', rot);
            span.style.animationDelay = (i * 18) + 'ms';
            span.style.fontSize = (1.4 + Math.random() * 1.2) + 'rem';

            document.body.appendChild(span);
            setTimeout(() => span.remove(), 1700 + i * 18);
        }
    }
    // =========================================================

    function startGame() {
        initAudio();
        pickVoice();
        if (ytApiReady && !ytPlayer) createYTPlayer();

        players = [
            { name: document.getElementById('p1').value.trim() || 'Player 1', score: 0, color: COLORS[0] },
            { name: document.getElementById('p2').value.trim() || 'Player 2', score: 0, color: COLORS[1] },
            { name: document.getElementById('p3').value.trim() || 'Player 3', score: 0, color: COLORS[2] },
            { name: document.getElementById('p4').value.trim() || 'Player 4', score: 0, color: COLORS[3] }
        ];
        turn = 0;
        gameOver = false;
        document.getElementById('setupScreen').style.display = 'none';
        document.getElementById('gameScreen').style.display = 'block';
        document.getElementById('log').innerHTML = '';
        document.getElementById('rollAnnounce').innerHTML = '';
        addLog('Game shuru! Target: 30 points. ' + players[0].name + ' pehle roll karega.');
        renderPlayers();
        updateTurnBanner();
    }

    function renderPlayers() {
        const row = document.getElementById('playersRow');
        row.innerHTML = '';
        players.forEach((p, i) => {
            const div = document.createElement('div');
            div.className = 'player-card' + (i === turn && !gameOver ? ' active' : '') + (p.score >= TARGET ? ' winner' : '');
            const pct = Math.min(100, (p.score / TARGET) * 100);
            div.innerHTML = `
                <div class="name"><span class="color-dot" style="background:${p.color}"></span>${p.name}</div>
                <div class="score">${p.score}<span style="font-size:0.7rem;color:#aaa">/30</span></div>
                <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
            `;
            row.appendChild(div);
        });
    }

    function updateTurnBanner() {
        if (gameOver) return;
        const banner = document.getElementById('turnBanner');
        const p = players[turn];
        banner.innerHTML = `🎯 <span style="color:${p.color}">${p.name}</span> — SPIN KARO! (Score: ${p.score}/30)`;
    }

    // NOTE: "spin karo" AI announcement removed as requested.

    function addLog(msg) {
        const logDiv = document.getElementById('log');
        logDiv.innerHTML += '<div>' + msg + '</div>';
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    function rollDice() {
        if (gameOver) return;
        const btn = document.getElementById('rollBtn');
        btn.disabled = true;

        const diceDisplay = document.getElementById('diceDisplay');
        diceDisplay.classList.add('rolling');
        playDiceSound();

        // Immediately speak a random gali on each spin
        const gali = getRandomGali();
        setTimeout(() => speak(gali), 200);

        const announce = document.getElementById('rollAnnounce');
        announce.classList.remove('big');
        announce.innerHTML = 'Dice ghoom raha hai...';

        let count = 0;
        const diceFaces = ['⚀','⚁','⚂','⚃','⚄','⚅'];
        const rollInterval = setInterval(() => {
            diceDisplay.textContent = diceFaces[Math.floor(Math.random() * 6)];
            count++;
            if (count > 8) {
                clearInterval(rollInterval);
                diceDisplay.classList.remove('rolling');
                finalizeRoll();
            }
        }, 80);
    }

    function finalizeRoll() {
        const diceFaces = ['⚀','⚁','⚂','⚃','⚄','⚅'];
        const val = Math.floor(Math.random() * 6) + 1;
        const diceDisplay = document.getElementById('diceDisplay');
        diceDisplay.textContent = diceFaces[val - 1];

        const p = players[turn];
        p.score += val;

        // Emoji burst from this player's card side
        burstEmojisFromCard(turn);

        const announce = document.getElementById('rollAnnounce');
        announce.innerHTML = `🎲 <b>${p.name}</b> ko <b style="color:#ffd700;font-size:1.6rem">${val}</b> mila! (Score: ${p.score}/30)`;
        announce.classList.remove('big');
        void announce.offsetWidth;
        announce.classList.add('big');

        addLog(`${p.name} ne ${val} roll kiya. Score: ${p.score}/30`);

        if (p.score >= TARGET) {
            gameOver = true;
            p.score = TARGET;
            renderPlayers();
            document.getElementById('turnBanner').innerHTML = `🏆 <span style="color:${p.color}">${p.name}</span> JEET GAYA!`;

            document.getElementById('winnerText').textContent = `${p.name} ne 30 points complete kar liye! 🎉`;
            const gali = getWinnerGali(p.name);
            document.getElementById('winnerGali').textContent = gali;
            document.getElementById('winnerOverlay').classList.add('show');

            playWinSound();
            setTimeout(() => speak(gali), 1600);
            return;
        }

        if (val === 6) {
            addLog(`${p.name} ko 6 mila - EXTRA TURN! 🎲`);
            setTimeout(() => playCidGaliSound(), 400);
        } else {
            turn = (turn + 1) % players.length;
        }

        renderPlayers();
        updateTurnBanner();
        document.getElementById('rollBtn').disabled = false;
    }

    function restartGame() {
        document.getElementById('winnerOverlay').classList.remove('show');
        document.getElementById('setupScreen').style.display = 'block';
        document.getElementById('gameScreen').style.display = 'none';
        document.getElementById('diceDisplay').textContent = '🎲';
        document.getElementById('rollBtn').disabled = false;
        document.getElementById('rollAnnounce').innerHTML = '';
        document.getElementById('winnerGali').textContent = '';
        players = [];
        turn = 0;
        gameOver = false;
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        if (ytPlayer && ytReady) { try { ytPlayer.pauseVideo(); } catch(e) {} }
    }

    document.addEventListener('touchstart', initAudio, { once: true });
    document.addEventListener('click', initAudio, { once: true });
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
