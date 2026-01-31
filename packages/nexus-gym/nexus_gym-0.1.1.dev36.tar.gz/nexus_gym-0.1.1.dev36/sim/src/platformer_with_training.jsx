import React, { useState, useEffect, useCallback, useRef } from 'react';

const GAME_WIDTH = 800;
const GAME_HEIGHT = 450;
const PLAYER_SIZE = 28;
const GRAVITY = 0.6;
const JUMP_FORCE = -14;
const MOVE_SPEED = 5;
const FRICTION = 0.85;

const THEMES = [
  { id: 'crystal_caves', name: 'Crystal Caves', emoji: '💎', colors: ['#1a0a2e', '#16213e', '#0f3460', '#533483', '#e94560'] },
  { id: 'volcanic_depths', name: 'Volcanic Depths', emoji: '🌋', colors: ['#1a0000', '#2d0a0a', '#4a1010', '#8b2500', '#ff4500'] },
  { id: 'cyber_district', name: 'Cyber District', emoji: '🤖', colors: ['#0a0a0f', '#1a1a2e', '#0f0f23', '#00d4ff', '#ff00ff'] },
  { id: 'enchanted_forest', name: 'Enchanted Forest', emoji: '🌲', colors: ['#0a1a0a', '#1a2f1a', '#2d4a2d', '#4a7c59', '#98fb98'] },
  { id: 'frozen_peaks', name: 'Frozen Peaks', emoji: '❄️', colors: ['#0a1a2a', '#1a3a5a', '#2a5a8a', '#6ab7ff', '#ffffff'] },
  { id: 'desert_ruins', name: 'Desert Ruins', emoji: '🏜️', colors: ['#1a1000', '#3d2914', '#6b4423', '#c49a6c', '#ffd700'] },
  { id: 'cosmic_void', name: 'Cosmic Void', emoji: '🌌', colors: ['#000010', '#0a0020', '#1a0040', '#4a0080', '#ff00aa'] },
  { id: 'steampunk_factory', name: 'Steampunk Factory', emoji: '⚙️', colors: ['#1a1410', '#2d2420', '#4a3830', '#8b7355', '#d4a574'] },
];

// ============================================================================
// WebSocket Hook for RL Training Mode
// ============================================================================
const useRLTraining = (enabled, wsUrl = 'ws://localhost:8765') => {
  const wsRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [rlInput, setRlInput] = useState({ left: false, right: false, jump: false });
  const [episodeCount, setEpisodeCount] = useState(0);
  const [resetRequest, setResetRequest] = useState(null);
  const sendStateRef = useRef(null);

  useEffect(() => {
    if (!enabled) return;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('RL Training: WebSocket connected');
          setConnected(true);
          ws.send(JSON.stringify({ type: 'ready' }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'action') {
              setRlInput({
                left: data.left || false,
                right: data.right || false,
                jump: data.jump || false,
              });
            } else if (data.type === 'reset') {
              setResetRequest({
                episodeCount: data.episode_count || 0,
                levelConfig: data.level_config || null,
              });
              if (data.episode_count !== undefined) {
                setEpisodeCount(data.episode_count);
              }
            }
          } catch (e) {
            console.error('RL Training: Failed to parse message', e);
          }
        };

        ws.onclose = () => {
          console.log('RL Training: WebSocket disconnected');
          setConnected(false);
          setTimeout(connect, 2000);
        };

        ws.onerror = (error) => {
          console.error('RL Training: WebSocket error', error);
        };
      } catch (e) {
        console.error('RL Training: Connection failed', e);
        setTimeout(connect, 2000);
      }
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [enabled, wsUrl]);

  const sendState = useCallback((state) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'state', ...state }));
    }
  }, []);

  sendStateRef.current = sendState;

  const clearResetRequest = useCallback(() => {
    setResetRequest(null);
  }, []);

  const sendControl = useCallback((command) => {
    try {
      if (wsRef.current) {
        console.log('sendControl', command, 'readyState:', wsRef.current.readyState);
        if (wsRef.current.readyState === WebSocket.OPEN) {
          if (command === 'start') {
            wsRef.current.send(JSON.stringify({ type: 'start' }));
          } else {
            wsRef.current.send(JSON.stringify({ type: 'control', command }));
          }
        } else {
          console.warn('WebSocket not open', wsRef.current.readyState);
          alert("WebSocket not ready! State: " + wsRef.current.readyState);
        }
      } else {
        console.error('No WebSocket ref');
        alert("No WebSocket connection found!");
      }
    } catch (e) {
      console.error('Error sending control', e);
      alert("Error sending control: " + e.message);
    }
  }, []);

  return {
    connected,
    rlInput,
    sendState,
    sendControl,
    episodeCount,
    resetRequest,
    clearResetRequest,
    wsUrl,
  };
};

// ============================================================================
// Theme Selector Component
// ============================================================================
const ThemeSelector = ({ onSelect, currentLevel, isLoading }) => {
  const [hoveredTheme, setHoveredTheme] = useState(null);

  return (
    <div style={{
      position: 'absolute',
      inset: 0,
      background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f23 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '"Courier New", monospace',
      overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `
          linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px',
        animation: 'gridMove 20s linear infinite',
      }} />

      {[...Array(20)].map((_, i) => (
        <div key={i} style={{
          position: 'absolute',
          width: Math.random() * 4 + 2,
          height: Math.random() * 4 + 2,
          background: `rgba(0, 212, 255, ${Math.random() * 0.5 + 0.2})`,
          borderRadius: '50%',
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 100}%`,
          animation: `float ${Math.random() * 5 + 3}s ease-in-out infinite`,
          animationDelay: `${Math.random() * 2}s`,
        }} />
      ))}

      <div style={{
        position: 'relative',
        zIndex: 10,
        textAlign: 'center',
      }}>
        <h1 style={{
          fontSize: currentLevel === 1 ? '3.5rem' : '2.5rem',
          fontWeight: 'bold',
          color: '#00d4ff',
          textShadow: '0 0 30px rgba(0, 212, 255, 0.8), 0 0 60px rgba(0, 212, 255, 0.4)',
          marginBottom: '0.5rem',
          letterSpacing: '0.3em',
          textTransform: 'uppercase',
        }}>
          {currentLevel === 1 ? 'NEXUS' : 'LEVEL COMPLETE'}
        </h1>

        <p style={{
          color: 'rgba(255, 255, 255, 0.6)',
          fontSize: '1rem',
          letterSpacing: '0.5em',
          marginBottom: '2rem',
          textTransform: 'uppercase',
        }}>
          {currentLevel === 1 ? 'AI-Powered Platformer' : `Prepare for Level ${currentLevel}`}
        </p>

        {currentLevel > 1 && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '0.5rem',
            marginBottom: '2rem',
          }}>
            {[...Array(currentLevel - 1)].map((_, i) => (
              <div key={i} style={{
                width: 12,
                height: 12,
                background: '#00d4ff',
                borderRadius: '50%',
                boxShadow: '0 0 10px rgba(0, 212, 255, 0.8)',
              }} />
            ))}
            <div style={{
              width: 12,
              height: 12,
              border: '2px solid #00d4ff',
              borderRadius: '50%',
              animation: 'pulse 1s ease-in-out infinite',
            }} />
          </div>
        )}

        <h2 style={{
          fontSize: '1.3rem',
          color: 'rgba(255, 255, 255, 0.9)',
          marginBottom: '1.5rem',
          fontWeight: 'normal',
        }}>
          Choose Your Realm
        </h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '1rem',
          maxWidth: '700px',
          margin: '0 auto',
        }}>
          {THEMES.map((theme) => (
            <button
              key={theme.id}
              onClick={() => !isLoading && onSelect(theme)}
              onMouseEnter={() => setHoveredTheme(theme.id)}
              onMouseLeave={() => setHoveredTheme(null)}
              disabled={isLoading}
              style={{
                position: 'relative',
                padding: '1.2rem 0.8rem',
                background: hoveredTheme === theme.id
                  ? `linear-gradient(135deg, ${theme.colors[0]}, ${theme.colors[2]})`
                  : 'rgba(255, 255, 255, 0.03)',
                border: hoveredTheme === theme.id
                  ? `2px solid ${theme.colors[3]}`
                  : '2px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                cursor: isLoading ? 'wait' : 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                transform: hoveredTheme === theme.id ? 'translateY(-4px) scale(1.02)' : 'none',
                boxShadow: hoveredTheme === theme.id
                  ? `0 10px 40px ${theme.colors[3]}40, inset 0 1px 0 rgba(255,255,255,0.1)`
                  : '0 4px 20px rgba(0, 0, 0, 0.3)',
                overflow: 'hidden',
              }}
            >
              {hoveredTheme === theme.id && (
                <div style={{
                  position: 'absolute',
                  top: '-50%',
                  left: '-50%',
                  width: '200%',
                  height: '200%',
                  background: `radial-gradient(circle, ${theme.colors[3]}20 0%, transparent 70%)`,
                  pointerEvents: 'none',
                }} />
              )}

              <span style={{
                fontSize: '2rem',
                display: 'block',
                marginBottom: '0.5rem',
                filter: hoveredTheme === theme.id ? 'none' : 'grayscale(0.3)',
                transition: 'filter 0.3s',
              }}>
                {theme.emoji}
              </span>
              <span style={{
                color: hoveredTheme === theme.id ? theme.colors[4] : 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.75rem',
                fontWeight: 'bold',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                transition: 'color 0.3s',
              }}>
                {theme.name}
              </span>

              <div style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '4px',
                marginTop: '0.6rem',
              }}>
                {theme.colors.slice(2).map((color, i) => (
                  <div key={i} style={{
                    width: 8,
                    height: 8,
                    background: color,
                    borderRadius: '50%',
                    opacity: hoveredTheme === theme.id ? 1 : 0.5,
                    transition: 'opacity 0.3s',
                  }} />
                ))}
              </div>
            </button>
          ))}
        </div>

        {isLoading && (
          <div style={{
            marginTop: '2rem',
            color: '#00d4ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1rem',
          }}>
            <div style={{
              width: 20,
              height: 20,
              border: '3px solid transparent',
              borderTop: '3px solid #00d4ff',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
            <span style={{ letterSpacing: '0.2em' }}>GENERATING LEVEL...</span>
          </div>
        )}

        <div style={{
          marginTop: '2.5rem',
          padding: '1rem 2rem',
          background: 'rgba(255, 255, 255, 0.03)',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
        }}>
          <p style={{ color: 'rgba(255, 255, 255, 0.4)', fontSize: '0.8rem', margin: 0 }}>
            <span style={{ color: '#00d4ff' }}>←→</span> Move &nbsp;|&nbsp;
            <span style={{ color: '#00d4ff' }}>SPACE</span> Jump &nbsp;|&nbsp;
            <span style={{ color: '#ff00aa' }}>★</span> Collect all stars to advance
          </p>
        </div>
      </div>

      <style>{`
        @keyframes gridMove {
          0% { transform: translate(0, 0); }
          100% { transform: translate(40px, 40px); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.3; }
          50% { transform: translateY(-20px) rotate(180deg); opacity: 0.8; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.2); }
        }
        @keyframes spin {
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

// ============================================================================
// Game Canvas Component
// ============================================================================
const GameCanvas = ({
  level,
  theme,
  onComplete,
  onDeath,
  currentLevelNum,
  trainingMode = false,
  rlInput = null,
  onStateUpdate = null,
  onStatsUpdate = null,
  initialShowRays = true,
}) => {
  const canvasRef = useRef(null);
  const gameStateRef = useRef({
    player: { x: 50, y: 400, vx: 0, vy: 0, grounded: false, facing: 1 },
    keys: { left: false, right: false, jump: false },
    platforms: [],
    hazards: [],
    collectibles: [],
    goal: null,
    particles: [],
    cameraX: 0,
    deathAnimation: null,
    winAnimation: null,
    stepCount: 0,
    totalReward: 0,
    raycasts: [], // Array of { dist: 1.0, type: 0, hitX: 0, hitY: 0 }
  });
  const animationRef = useRef(null);
  const [collected, setCollected] = useState(0);
  const [totalCollectibles, setTotalCollectibles] = useState(0);
  const [showRays, setShowRays] = useState(initialShowRays); // Toggle for ray visualization

  // Initialize level
  useEffect(() => {
    if (!level) return;

    const state = gameStateRef.current;
    state.platforms = level.platforms || [];
    state.hazards = level.hazards || [];
    state.collectibles = (level.collectibles || []).map(c => ({ ...c, collected: false }));
    state.goal = level.goal;
    state.player = { x: level.startX || 50, y: level.startY || 400, vx: 0, vy: 0, grounded: false, facing: 1 };
    state.particles = [];
    state.cameraX = 0;
    state.deathAnimation = null;
    state.winAnimation = null;
    state.stepCount = 0;
    state.totalReward = 0;
    setCollected(0);
    setTotalCollectibles(state.collectibles.length);
  }, [level]);

  // Handle RL input in training mode
  useEffect(() => {
    if (trainingMode && rlInput) {
      const state = gameStateRef.current;
      state.keys.left = rlInput.left;
      state.keys.right = rlInput.right;
      state.keys.jump = rlInput.jump;
    }
  }, [trainingMode, rlInput]);

  // Input handling (only for non-training mode)
  useEffect(() => {
    if (trainingMode) return;

    const handleKeyDown = (e) => {
      const state = gameStateRef.current;
      if (e.code === 'ArrowLeft' || e.code === 'KeyA') state.keys.left = true;
      if (e.code === 'ArrowRight' || e.code === 'KeyD') state.keys.right = true;
      if (e.code === 'Space' || e.code === 'ArrowUp' || e.code === 'KeyW') {
        e.preventDefault();
        state.keys.jump = true;
      }
    };
    const handleKeyUp = (e) => {
      const state = gameStateRef.current;
      if (e.code === 'ArrowLeft' || e.code === 'KeyA') state.keys.left = false;
      if (e.code === 'ArrowRight' || e.code === 'KeyD') state.keys.right = false;
      if (e.code === 'Space' || e.code === 'ArrowUp' || e.code === 'KeyW') state.keys.jump = false;
    };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [trainingMode]);

  // Game loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const colors = theme?.colors || ['#1a1a2e', '#16213e', '#0f3460', '#00d4ff', '#ff00aa'];

    const spawnParticles = (x, y, color, count = 5) => {
      const state = gameStateRef.current;
      for (let i = 0; i < count; i++) {
        state.particles.push({
          x, y,
          vx: (Math.random() - 0.5) * 8,
          vy: (Math.random() - 0.5) * 8 - 2,
          life: 1,
          color,
          size: Math.random() * 4 + 2,
        });
      }
    };

    const gameLoop = () => {
      const state = gameStateRef.current;
      const { player, keys, platforms, hazards, collectibles, goal, particles } = state;

      // Handle death animation
      if (state.deathAnimation !== null) {
        state.deathAnimation += 0.02;
        if (state.deathAnimation >= 1) {
          onDeath();
          return;
        }
        ctx.fillStyle = colors[0];
        ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
        ctx.fillStyle = `rgba(255, 0, 0, ${state.deathAnimation * 0.3})`;
        ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 48px "Courier New"';
        ctx.textAlign = 'center';
        ctx.globalAlpha = state.deathAnimation;
        ctx.fillText('DEFEATED', GAME_WIDTH / 2, GAME_HEIGHT / 2);
        ctx.globalAlpha = 1;
        animationRef.current = requestAnimationFrame(gameLoop);
        return;
      }

      // --- Raycast Logic ---
      const rays = 16;
      const maxRayDist = 400;
      const rayResults = [];
      const px_center = player.x + PLAYER_SIZE / 2;
      const py_center = player.y + PLAYER_SIZE / 2;

      const intersectRayRect = (ox, oy, dx, dy, rx, ry, rw, rh) => {
        let tmin = -Infinity, tmax = Infinity;
        if (dx !== 0) {
          let t1 = (rx - ox) / dx;
          let t2 = (rx + rw - ox) / dx;
          tmin = Math.max(tmin, Math.min(t1, t2));
          tmax = Math.min(tmax, Math.max(t1, t2));
        } else if (ox < rx || ox > rx + rw) return null;

        if (dy !== 0) {
          let t1 = (ry - oy) / dy;
          let t2 = (ry + rh - oy) / dy;
          tmin = Math.max(tmin, Math.min(t1, t2));
          tmax = Math.min(tmax, Math.max(t1, t2));
        } else if (oy < ry || oy > ry + rh) return null;

        return (tmax >= tmin && tmax >= 0) ? tmin : null;
      };

      for (let i = 0; i < rays; i++) {
        const angle = (i * 2 * Math.PI) / rays;
        const dx = Math.cos(angle);
        const dy = Math.sin(angle);

        let closestT = maxRayDist;
        let hitType = 0; // 0: Empty

        // Check platforms (0.25)
        for (const plat of platforms) {
          const t = intersectRayRect(px_center, py_center, dx, dy, plat.x, plat.y, plat.width, plat.height);
          if (t !== null && t < closestT) {
            closestT = t;
            hitType = 0.25;
          }
        }
        // Check hazards (0.5)
        for (const hazard of hazards) {
          const t = intersectRayRect(px_center, py_center, dx, dy, hazard.x, hazard.y, hazard.width || 30, hazard.height || 20);
          if (t !== null && t < closestT) {
            closestT = t;
            hitType = 0.5;
          }
        }
        // Check stars (0.75)
        for (const star of collectibles) {
          if (star.collected) continue;
          const t = intersectRayRect(px_center, py_center, dx, dy, star.x, star.y, 30, 30);
          if (t !== null && t < closestT) {
            closestT = t;
            hitType = 0.75;
          }
        }
        // Check goal (1.0)
        if (goal) {
          const t = intersectRayRect(px_center, py_center, dx, dy, goal.x, goal.y, 40, 40);
          if (t !== null && t < closestT) {
            closestT = t;
            hitType = 1.0;
          }
        }

        rayResults.push({
          dist: closestT / maxRayDist,
          type: hitType,
          hitX: px_center + dx * closestT,
          hitY: py_center + dy * closestT
        });
      }
      state.raycasts = rayResults;

      // Handle win animation
      if (state.winAnimation !== null) {
        state.winAnimation += 0.015;
        if (state.winAnimation >= 1) {
          onComplete();
          return;
        }
      }

      // Player movement
      if (keys.left) {
        player.vx -= 0.8;
        player.facing = -1;
      }
      if (keys.right) {
        player.vx += 0.8;
        player.facing = 1;
      }
      if (keys.jump && player.grounded) {
        player.vy = JUMP_FORCE;
        player.grounded = false;
        spawnParticles(player.x + PLAYER_SIZE / 2, player.y + PLAYER_SIZE, colors[3], 8);
      }

      // Apply physics
      player.vx *= FRICTION;
      player.vy += GRAVITY;
      player.x += player.vx;
      player.y += player.vy;

      player.vx = Math.max(-MOVE_SPEED, Math.min(MOVE_SPEED, player.vx));
      player.vy = Math.max(-20, Math.min(20, player.vy));

      // Platform collision
      player.grounded = false;
      for (const plat of platforms) {
        if (
          player.x + PLAYER_SIZE > plat.x &&
          player.x < plat.x + plat.width &&
          player.y + PLAYER_SIZE > plat.y &&
          player.y + PLAYER_SIZE < plat.y + plat.height + player.vy + 5 &&
          player.vy >= 0
        ) {
          player.y = plat.y - PLAYER_SIZE;
          player.vy = 0;
          player.grounded = true;
        }
      }

      // Hazard collision
      let isDead = false;
      for (const hazard of hazards) {
        const hw = hazard.width || 30;
        const hh = hazard.height || 20;

        if (
          player.x + PLAYER_SIZE > hazard.x + 5 &&
          player.x < hazard.x + hw - 5 &&
          player.y + PLAYER_SIZE > hazard.y + 5 &&
          player.y < hazard.y + hh - 5
        ) {
          spawnParticles(player.x + PLAYER_SIZE / 2, player.y + PLAYER_SIZE / 2, '#ff0000', 20);
          state.deathAnimation = 0;
          state.totalReward -= 20;
          isDead = true;
        }
      }

      // Collectible collision
      let newCollected = 0;
      let starsGainedThisFrame = 0;
      for (const col of collectibles) {
        if (col.collected) {
          newCollected++;
          continue;
        }
        const cx = col.x + 15;
        const cy = col.y + 15;
        const dist = Math.sqrt(
          Math.pow(player.x + PLAYER_SIZE / 2 - cx, 2) +
          Math.pow(player.y + PLAYER_SIZE / 2 - cy, 2)
        );
        if (dist < PLAYER_SIZE) {
          col.collected = true;
          newCollected++;
          starsGainedThisFrame++;
          spawnParticles(cx, cy, colors[4], 15);
        }
      }
      state.totalReward += starsGainedThisFrame * 5.0;
      setCollected(newCollected);

      // Goal collision
      let levelComplete = false;
      if (goal && newCollected === collectibles.length) {
        const gx = goal.x + 20;
        const gy = goal.y + 20;
        const dist = Math.sqrt(
          Math.pow(player.x + PLAYER_SIZE / 2 - gx, 2) +
          Math.pow(player.y + PLAYER_SIZE / 2 - gy, 2)
        );
        if (dist < PLAYER_SIZE + 20) {
          spawnParticles(gx, gy, '#00ff00', 30);
          state.winAnimation = 0;
          state.totalReward += 100;
          levelComplete = true;
        }
      }

      // World bounds
      if (player.x < 0) player.x = 0;
      if (player.x > (level?.width || 1200) - PLAYER_SIZE) {
        player.x = (level?.width || 1200) - PLAYER_SIZE;
      }
      if (player.y > GAME_HEIGHT + 100) {
        spawnParticles(player.x + PLAYER_SIZE / 2, GAME_HEIGHT, '#ff0000', 10);
        state.deathAnimation = 0;
        state.totalReward -= 20;
        isDead = true;
      }

      // Camera follow
      const targetCameraX = player.x - GAME_WIDTH / 3;
      state.cameraX += (targetCameraX - state.cameraX) * 0.08;
      state.cameraX = Math.max(0, Math.min((level?.width || 1200) - GAME_WIDTH, state.cameraX));

      // Update particles
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.2;
        p.life -= 0.03;
        if (p.life <= 0) particles.splice(i, 1);
      }

      // Update step count and apply step penalty
      state.stepCount++;
      state.totalReward -= 0.01;

      // Report stats to parent
      if (onStatsUpdate) {
        onStatsUpdate({
          stepCount: state.stepCount,
          totalReward: state.totalReward,
        });
      }

      if (trainingMode && onStateUpdate) {
        onStateUpdate({
          player_x: player.x,
          player_y: player.y,
          player_vx: player.vx,
          player_vy: player.vy,
          player_grounded: player.grounded,
          stars_collected: newCollected,
          total_stars: collectibles.length,
          goal_x: goal ? goal.x : 0,
          goal_y: goal ? goal.y : 0,
          level_width: level?.width || 1200,
          is_dead: isDead,
          level_complete: levelComplete,
          platforms: platforms,
          hazards: hazards,
          collectibles: collectibles.map(c => ({ x: c.x, y: c.y, collected: c.collected })),
          raycasts: rayResults.flatMap(r => [r.dist, r.type]),
        });

        // If something terminal happened, send it an extra time to ensure it's not lost
        if (isDead || levelComplete) {
          onStateUpdate({
            type: 'terminal',
            is_dead: isDead,
            level_complete: levelComplete,
            stars_collected: newCollected
          });
        }
      }

      // RENDER
      const bgGrad = ctx.createLinearGradient(0, 0, 0, GAME_HEIGHT);
      bgGrad.addColorStop(0, colors[0]);
      bgGrad.addColorStop(0.5, colors[1]);
      bgGrad.addColorStop(1, colors[2]);
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

      ctx.fillStyle = `${colors[3]}15`;
      for (let i = 0; i < 20; i++) {
        const bx = ((i * 137) % (level?.width || 1200)) - state.cameraX * 0.3;
        const by = (i * 73) % GAME_HEIGHT;
        ctx.beginPath();
        ctx.arc(bx, by, 30 + (i % 3) * 20, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.strokeStyle = `${colors[3]}10`;
      ctx.lineWidth = 1;
      for (let x = -state.cameraX % 50; x < GAME_WIDTH; x += 50) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, GAME_HEIGHT);
        ctx.stroke();
      }
      for (let y = 0; y < GAME_HEIGHT; y += 50) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(GAME_WIDTH, y);
        ctx.stroke();
      }

      // Platforms
      for (const plat of platforms) {
        const px = plat.x - state.cameraX;
        if (px > GAME_WIDTH + 50 || px + plat.width < -50) continue;

        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.fillRect(px + 4, plat.y + 4, plat.width, plat.height);

        const platGrad = ctx.createLinearGradient(px, plat.y, px, plat.y + plat.height);
        platGrad.addColorStop(0, colors[2]);
        platGrad.addColorStop(1, colors[1]);
        ctx.fillStyle = platGrad;
        ctx.fillRect(px, plat.y, plat.width, plat.height);

        ctx.fillStyle = `${colors[3]}40`;
        ctx.fillRect(px, plat.y, plat.width, 3);

        ctx.strokeStyle = colors[3];
        ctx.lineWidth = 2;
        ctx.strokeRect(px, plat.y, plat.width, plat.height);
      }

      // Hazards
      ctx.fillStyle = colors[4];
      for (const hazard of hazards) {
        const hx = hazard.x - state.cameraX;
        if (hx > GAME_WIDTH + 50 || hx + (hazard.width || 30) < -50) continue;

        const hw = hazard.width || 30;
        const hh = hazard.height || 20;
        const spikes = Math.floor(hw / 15);

        ctx.beginPath();
        for (let i = 0; i < spikes; i++) {
          const sx = hx + (i * hw / spikes);
          ctx.moveTo(sx, hazard.y + hh);
          ctx.lineTo(sx + hw / spikes / 2, hazard.y);
          ctx.lineTo(sx + hw / spikes, hazard.y + hh);
        }
        ctx.fill();

        ctx.shadowColor = colors[4];
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      // Collectibles
      const time = Date.now() / 1000;
      for (const col of collectibles) {
        if (col.collected) continue;
        const cx = col.x - state.cameraX;
        if (cx > GAME_WIDTH + 50 || cx < -50) continue;

        const bobY = Math.sin(time * 3 + col.x * 0.1) * 5;
        const rotation = time * 2 + col.x * 0.05;

        ctx.save();
        ctx.translate(cx + 15, col.y + 15 + bobY);
        ctx.rotate(rotation);

        ctx.shadowColor = colors[4];
        ctx.shadowBlur = 15;

        ctx.fillStyle = colors[4];
        ctx.beginPath();
        for (let i = 0; i < 5; i++) {
          const angle = (i * 4 * Math.PI) / 5 - Math.PI / 2;
          const r = 12;
          ctx.lineTo(Math.cos(angle) * r, Math.sin(angle) * r);
          const innerAngle = angle + (2 * Math.PI) / 10;
          ctx.lineTo(Math.cos(innerAngle) * 5, Math.sin(innerAngle) * 5);
        }
        ctx.closePath();
        ctx.fill();

        ctx.shadowBlur = 0;
        ctx.restore();
      }

      // Goal portal
      if (goal) {
        const gx = goal.x - state.cameraX;
        const allCollected = collectibles.every(c => c.collected);

        ctx.save();
        ctx.translate(gx + 20, goal.y + 20);

        if (allCollected) {
          ctx.shadowColor = '#00ff00';
          ctx.shadowBlur = 30;
        }

        for (let i = 0; i < 3; i++) {
          ctx.strokeStyle = allCollected
            ? `rgba(0, 255, 0, ${0.8 - i * 0.2})`
            : `rgba(100, 100, 100, ${0.5 - i * 0.15})`;
          ctx.lineWidth = 3 - i;
          ctx.beginPath();
          ctx.arc(0, 0, 18 - i * 4, time * (1 + i * 0.5), time * (1 + i * 0.5) + Math.PI * 1.5);
          ctx.stroke();
        }

        ctx.fillStyle = allCollected ? '#00ff00' : '#444';
        ctx.beginPath();
        ctx.arc(0, 0, 8, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0;
        ctx.restore();
      }

      // Particles
      for (const p of particles) {
        ctx.globalAlpha = p.life;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x - state.cameraX, p.y, p.size * p.life, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      // Player
      const px = player.x - state.cameraX;

      ctx.fillStyle = 'rgba(0,0,0,0.3)';
      ctx.beginPath();
      ctx.ellipse(px + PLAYER_SIZE / 2, player.y + PLAYER_SIZE + 5, PLAYER_SIZE / 2, 5, 0, 0, Math.PI * 2);
      ctx.fill();

      const playerGrad = ctx.createLinearGradient(px, player.y, px + PLAYER_SIZE, player.y + PLAYER_SIZE);
      playerGrad.addColorStop(0, colors[3]);
      playerGrad.addColorStop(1, colors[4]);
      ctx.fillStyle = playerGrad;
      ctx.shadowColor = colors[3];
      ctx.shadowBlur = 15;

      const radius = 6;
      ctx.beginPath();
      ctx.moveTo(px + radius, player.y);
      ctx.lineTo(px + PLAYER_SIZE - radius, player.y);
      ctx.quadraticCurveTo(px + PLAYER_SIZE, player.y, px + PLAYER_SIZE, player.y + radius);
      ctx.lineTo(px + PLAYER_SIZE, player.y + PLAYER_SIZE - radius);
      ctx.quadraticCurveTo(px + PLAYER_SIZE, player.y + PLAYER_SIZE, px + PLAYER_SIZE - radius, player.y + PLAYER_SIZE);
      ctx.lineTo(px + radius, player.y + PLAYER_SIZE);
      ctx.quadraticCurveTo(px, player.y + PLAYER_SIZE, px, player.y + PLAYER_SIZE - radius);
      ctx.lineTo(px, player.y + radius);
      ctx.quadraticCurveTo(px, player.y, px + radius, player.y);
      ctx.fill();

      ctx.shadowBlur = 0;
      ctx.fillStyle = '#fff';
      const eyeOffset = player.facing * 3;
      ctx.beginPath();
      ctx.arc(px + PLAYER_SIZE / 2 - 4 + eyeOffset, player.y + 10, 4, 0, Math.PI * 2);
      ctx.arc(px + PLAYER_SIZE / 2 + 4 + eyeOffset, player.y + 10, 4, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#000';
      ctx.beginPath();
      ctx.arc(px + PLAYER_SIZE / 2 + 4 + eyeOffset + player.facing * 2, player.y + 10, 2, 0, Math.PI * 2);
      ctx.fill();

      // Rays visualization
      if (showRays && state.raycasts.length > 0) {
        ctx.save();
        ctx.lineWidth = 1;
        state.raycasts.forEach(r => {
          if (r.type === 0 && r.dist >= 1.0) return; // Don't draw if nothing hit and max dist

          ctx.beginPath();
          ctx.moveTo(px_center - state.cameraX, py_center);
          ctx.lineTo(r.hitX - state.cameraX, r.hitY);

          // Color based on hit type
          if (r.type === 0.25) ctx.strokeStyle = 'rgba(0, 212, 255, 0.3)'; // Platform
          else if (r.type === 0.5) ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)'; // Hazard
          else if (r.type === 0.75) ctx.strokeStyle = 'rgba(255, 0, 255, 0.5)'; // Star
          else if (r.type === 1.0) ctx.strokeStyle = 'rgba(0, 255, 0, 0.5)'; // Goal
          else ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';

          ctx.stroke();

          if (r.type > 0) {
            ctx.fillStyle = ctx.strokeStyle;
            ctx.beginPath();
            ctx.arc(r.hitX - state.cameraX, r.hitY, 2, 0, Math.PI * 2);
            ctx.fill();
          }
        });
        ctx.restore();
      }

      // Win overlay
      if (state.winAnimation !== null) {
        ctx.fillStyle = `rgba(0, 255, 100, ${state.winAnimation * 0.3})`;
        ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 48px "Courier New"';
        ctx.textAlign = 'center';
        ctx.globalAlpha = state.winAnimation;
        ctx.shadowColor = '#00ff00';
        ctx.shadowBlur = 20;
        ctx.fillText('LEVEL COMPLETE!', GAME_WIDTH / 2, GAME_HEIGHT / 2);
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;
      }

      animationRef.current = requestAnimationFrame(gameLoop);
    };

    animationRef.current = requestAnimationFrame(gameLoop);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [level, theme, onComplete, onDeath, trainingMode, onStateUpdate, onStatsUpdate]);

  return (
    <div style={{
      position: 'relative',
      width: GAME_WIDTH,
      height: GAME_HEIGHT,
      borderRadius: '12px',
      overflow: 'hidden',
      boxShadow: `0 0 60px ${theme?.colors?.[3] || '#00d4ff'}40, 0 20px 60px rgba(0,0,0,0.5)`,
    }}>
      <canvas
        ref={canvasRef}
        width={GAME_WIDTH}
        height={GAME_HEIGHT}
        style={{ display: 'block' }}
      />

      {/* HUD */}
      <div style={{
        position: 'absolute',
        top: '1rem',
        left: '1rem',
        right: '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontFamily: '"Courier New", monospace',
        pointerEvents: 'none',
      }}>
        <div style={{
          background: 'rgba(0,0,0,0.5)',
          padding: '0.5rem 1rem',
          borderRadius: '8px',
          border: `1px solid ${theme?.colors?.[3] || '#00d4ff'}40`,
          backdropFilter: 'blur(5px)',
        }}>
          <span style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem' }}>LEVEL</span>
          <span style={{
            color: theme?.colors?.[3] || '#00d4ff',
            fontSize: '1.5rem',
            fontWeight: 'bold',
            marginLeft: '0.5rem',
            textShadow: `0 0 10px ${theme?.colors?.[3] || '#00d4ff'}`,
          }}>
            {currentLevelNum}
          </span>
        </div>

        <div style={{
          background: 'rgba(0,0,0,0.5)',
          padding: '0.5rem 1rem',
          borderRadius: '8px',
          border: `1px solid ${theme?.colors?.[4] || '#ff00aa'}40`,
          backdropFilter: 'blur(5px)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <span style={{ color: theme?.colors?.[4] || '#ff00aa', fontSize: '1.2rem' }}>★</span>
          <span style={{
            color: '#fff',
            fontSize: '1.2rem',
            fontWeight: 'bold',
          }}>
            {collected}/{totalCollectibles}
          </span>
        </div>
      </div>

      {/* Theme indicator */}
      <div style={{
        position: 'absolute',
        bottom: '8px',
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(0,0,0,0.5)',
        padding: '0.4rem 1rem',
        borderRadius: '20px',
        border: `1px solid ${theme?.colors?.[3] || '#00d4ff'}30`,
        backdropFilter: 'blur(5px)',
        fontFamily: '"Courier New", monospace',
        fontSize: '0.7rem',
        color: 'rgba(255,255,255,0.5)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        pointerEvents: 'none',
        zIndex: 10,
      }}>
        {theme?.emoji} {theme?.name}
      </div>

      {/* Action Indicators (Inside Game Canvas) */}
      {trainingMode && (
        <div style={{
          position: 'absolute',
          top: '1.1rem',
          left: 0,
          right: 0,
          zIndex: 10,
        }}>
          <ActionIndicators rlInput={rlInput} />
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Training Mode Header HUD Component
// ============================================================================
const TrainingHUD = ({ connected, episodeCount, stepCount, totalReward, wsUrl }) => {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      padding: '1rem 2rem',
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(10px)',
      borderBottom: '1px solid rgba(0, 212, 255, 0.3)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      fontFamily: '"Courier New", monospace',
      zIndex: 1000,
    }}>
      <div style={{
        color: '#00d4ff',
        fontSize: '1.2rem',
        letterSpacing: '0.2em',
        textShadow: '0 0 20px rgba(0, 212, 255, 0.5)',
      }}>
        NEXUS // RL TRAINING
      </div>

      <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        {/* Connection Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: connected ? '#00ff88' : '#ff4444',
            boxShadow: connected ? '0 0 10px rgba(0, 255, 136, 0.5)' : 'none',
          }} />
          <span style={{ color: 'rgba(255,255,255,0.7)' }}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* Episode */}
        <div style={{ color: 'rgba(255,255,255,0.7)' }}>
          Episode: <span style={{ color: '#00d4ff', fontWeight: 'bold' }}>{episodeCount}</span>
        </div>

        {/* Steps */}
        <div style={{ color: 'rgba(255,255,255,0.7)' }}>
          Steps: <span style={{ color: '#00d4ff', fontWeight: 'bold' }}>{stepCount}</span>
        </div>

        {/* Reward */}
        <div style={{ color: 'rgba(255,255,255,0.7)' }}>
          Reward: <span style={{
            color: totalReward >= 0 ? '#00ff88' : '#ff4444',
            fontWeight: 'bold'
          }}>
            {totalReward.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Training Mode Footer Component
// ============================================================================
const TrainingFooter = ({ wsUrl, connected, onStartTraining, trainingActive }) => {
  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      padding: '0.5rem 2rem',
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(10px)',
      borderTop: '1px solid rgba(0, 212, 255, 0.2)',
      fontFamily: '"Courier New", monospace',
      fontSize: '0.75rem',
      color: 'rgba(255, 255, 255, 0.5)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      zIndex: 1000,
    }}>
      <div>
        WebSocket: {wsUrl} | Gymnasium Environment {connected ? 'Connected' : 'Disconnected'}
      </div>

      <button
        onClick={onStartTraining}
        disabled={!connected || trainingActive}
        style={{
          background: trainingActive ? 'rgba(0, 255, 0, 0.2)' : connected ? 'rgba(0, 255, 0, 0.8)' : 'rgba(255, 255, 255, 0.1)',
          color: trainingActive ? 'rgba(150, 255, 150, 0.8)' : connected ? '#000' : 'rgba(255, 255, 255, 0.3)',
          border: 'none',
          borderRadius: '4px',
          padding: '4px 12px',
          fontWeight: 'bold',
          fontFamily: 'inherit',
          cursor: (!connected || trainingActive) ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s',
          textTransform: 'uppercase',
          letterSpacing: '1px'
        }}
      >
        {trainingActive ? 'Training In Progress' : 'Start Training'}
      </button>
    </div>
  );
};

// ============================================================================
// Training Action Indicators (Below game canvas)
// ============================================================================
const ActionIndicators = ({ rlInput }) => {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      gap: '0.3rem',
      marginTop: 0,
      pointerEvents: 'none',
    }}>
      <div style={{
        padding: '0.6rem 1.2rem',
        background: rlInput?.left ? 'rgba(0, 212, 255, 0.8)' : 'rgba(20, 20, 40, 0.8)',
        border: `2px solid ${rlInput?.left ? '#00d4ff' : 'rgba(255,255,255,0.4)'}`,
        borderRadius: '4px',
        fontSize: '0.75rem',
        fontFamily: '"Courier New", monospace',
        color: rlInput?.left ? '#00d4ff' : 'rgba(255,255,255,0.5)',
        transition: 'all 0.1s',
      }}>
        ← LEFT
      </div>
      <div style={{
        padding: '0.6rem 1.2rem',
        background: rlInput?.right ? 'rgba(0, 212, 255, 0.8)' : 'rgba(20, 20, 40, 0.8)',
        border: `2px solid ${rlInput?.right ? '#00d4ff' : 'rgba(255,255,255,0.4)'}`,
        borderRadius: '4px',
        fontSize: '0.75rem',
        fontFamily: '"Courier New", monospace',
        color: rlInput?.right ? '#00d4ff' : 'rgba(255,255,255,0.5)',
        transition: 'all 0.1s',
      }}>
        → RIGHT
      </div>
      <div style={{
        padding: '0.6rem 1.2rem',
        background: rlInput?.jump ? 'rgba(0, 212, 255, 0.8)' : 'rgba(20, 20, 40, 0.8)',
        border: `2px solid ${rlInput?.jump ? '#00d4ff' : 'rgba(255,255,255,0.4)'}`,
        borderRadius: '4px',
        fontSize: '0.75rem',
        fontFamily: '"Courier New", monospace',
        color: rlInput?.jump ? '#00d4ff' : 'rgba(255,255,255,0.5)',
        transition: 'all 0.1s',
      }}>
        ↑ JUMP
      </div>
    </div>
  );
};

// ============================================================================
// Main App Component
// ============================================================================
export default function AIPlatformer() {
  // Check URL params for training mode and theme
  const urlParams = new URLSearchParams(window.location.search);
  const trainingMode = urlParams.get('training') === 'true';
  const showRaysDefault = urlParams.get('rays') !== 'false'; // Default to true unless explicitly false
  const wsUrl = urlParams.get('ws') || 'ws://localhost:8765';
  const themeParam = urlParams.get('theme') || 'cyber_district';

  // Find the theme object from the theme ID
  const getThemeById = (themeId) => {
    const found = THEMES.find(t => t.id === themeId);
    return found || THEMES[2]; // Default to Cyber District (index 2)
  };

  const [gameState, setGameState] = useState(trainingMode ? 'playing' : 'theme_select');
  const [currentLevel, setCurrentLevel] = useState(1);
  const [selectedTheme, setSelectedTheme] = useState(trainingMode ? getThemeById(themeParam) : null);
  const [levelData, setLevelData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Training stats
  const [trainingStats, setTrainingStats] = useState({ stepCount: 0, totalReward: 0 });

  // RL Training hook
  const {
    connected,
    rlInput,
    sendState,
    episodeCount,
    resetRequest,
    clearResetRequest,
    sendControl,
  } = useRLTraining(trainingMode, wsUrl);

  // Handle stats updates from game canvas
  const handleStatsUpdate = useCallback((stats) => {
    setTrainingStats(stats);
  }, []);

  // Handle reset requests from Python
  useEffect(() => {
    if (trainingMode && resetRequest) {
      const levelConfig = resetRequest.levelConfig || generateFallbackLevel(1);
      setLevelData(levelConfig);
      setGameState('playing');
      setTrainingStats({ stepCount: 0, totalReward: 0 });
      clearResetRequest();
    }
  }, [trainingMode, resetRequest, clearResetRequest]);

  const generateFallbackLevel = (levelNum) => {
    const width = 800 + levelNum * 150;
    const platforms = [
      { x: 0, y: 450, width: 200, height: 30 },
    ];
    const hazards = [];
    const collectibles = [];

    let currentX = 180;
    const numPlatforms = 6 + levelNum * 2;

    for (let i = 0; i < numPlatforms; i++) {
      const gap = 40 + Math.random() * (30 + levelNum * 5);
      const platWidth = 80 + Math.random() * 100;
      const y = 300 + Math.sin(i * 0.5) * 100 + Math.random() * 50;

      platforms.push({
        x: currentX + gap,
        y: Math.max(200, Math.min(450, y)),
        width: platWidth,
        height: 25,
      });

      if (i % 2 === 0 && collectibles.length < 4 + levelNum) {
        collectibles.push({
          x: currentX + gap + platWidth / 2 - 15,
          y: y - 50,
        });
      }

      if (i % 3 === 0 && i > 0 && hazards.length < 2 + levelNum) {
        hazards.push({
          x: currentX + gap + platWidth / 2 - 15,
          y: y - 20,
          width: 30,
          height: 20,
        });
      }

      currentX += gap + platWidth;
    }

    platforms.push({
      x: currentX + 50,
      y: 400,
      width: 150,
      height: 30,
    });

    return {
      width: currentX + 250,
      startX: 50,
      startY: 350,
      platforms,
      hazards,
      collectibles,
      goal: { x: currentX + 100, y: 340 },
    };
  };

  const generateLevel = async (theme, levelNum) => {
    setIsLoading(true);

    const prompt = `Generate a platformer game level with theme "${theme.name}" (${theme.emoji}).

Level ${levelNum} of difficulty progression (1=easy, higher=harder).

Return ONLY valid JSON with this exact structure, no other text:
{
  "width": ${800 + levelNum * 150},
  "startX": 50,
  "startY": 350,
  "platforms": [
    {"x": 0, "y": 450, "width": 200, "height": 30},
    ... more platforms with x, y, width, height
  ],
  "hazards": [
    {"x": 300, "y": 430, "width": 30, "height": 20},
    ... ${Math.min(2 + levelNum, 8)} hazards (spikes)
  ],
  "collectibles": [
    {"x": 150, "y": 380},
    ... ${Math.min(4 + levelNum, 10)} collectible stars
  ],
  "goal": {"x": ${700 + levelNum * 120}, "y": 350}
}

CRITICAL REQUIREMENTS:
1. Difficulty ${levelNum}: ${levelNum <= 2 ? 'Easy jumps, few hazards' : levelNum <= 4 ? 'Moderate gaps, some tricky jumps' : 'Challenging platforming, precise jumps needed'}
2. Platform gaps should be jumpable (max ${60 + levelNum * 8} pixels horizontal gap)
3. Platforms y-values between 200-450 (lower is higher on screen)
4. Always include ground platforms connecting the level
5. Place hazards ON platforms, not floating
6. Collectibles should be reachable but sometimes challenging
7. Goal must be on a platform at the far right
8. Theme "${theme.name}": Make platform heights/patterns feel like ${theme.name.toLowerCase()}
9. Create interesting vertical variety - some high platforms, some low
10. Ensure the player can reach the goal by collecting all stars first`;

    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 2000,
          messages: [{ role: "user", content: prompt }],
        }),
      });

      const data = await response.json();
      const text = data.content?.[0]?.text || '';

      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const level = JSON.parse(jsonMatch[0]);
        setLevelData(level);
        setGameState('playing');
      } else {
        throw new Error('No valid JSON found');
      }
    } catch (error) {
      console.error('Level generation error:', error);
      const fallbackLevel = generateFallbackLevel(levelNum);
      setLevelData(fallbackLevel);
      setGameState('playing');
    }

    setIsLoading(false);
  };

  const handleThemeSelect = (theme) => {
    setSelectedTheme(theme);
    generateLevel(theme, currentLevel);
  };

  const handleLevelComplete = () => {
    if (trainingMode) {
      // In training mode, we don't advance level, the Python Env handles it via reset
      return;
    }
    setCurrentLevel(prev => prev + 1);
    setGameState('theme_select');
    setLevelData(null);
  };

  const handleDeath = () => {
    if (trainingMode) {
      // In training mode, the Python Env handles reset
      return;
    }
    if (selectedTheme) {
      generateLevel(selectedTheme, currentLevel);
    }
  };

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0a0a0f',
      fontFamily: '"Courier New", monospace',
      overflow: 'hidden',
      color: '#fff',
    }}>
      {/* Main Game Content Area */}
      {gameState === 'playing' && levelData && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          width: 'auto',
          height: 'auto',
          transform: trainingMode ? 'scale(min(1, calc((100vh - 250px) / 600)))' : 'none',
          transformOrigin: 'center center',
          marginTop: trainingMode ? '40px' : '0',
          marginBottom: '0',
        }}>
          <GameCanvas
            key={episodeCount}
            level={levelData}
            theme={selectedTheme}
            onComplete={handleLevelComplete}
            onDeath={handleDeath}
            currentLevelNum={currentLevel}
            trainingMode={trainingMode}
            rlInput={rlInput}
            onStateUpdate={sendState}
            onStatsUpdate={handleStatsUpdate}
            initialShowRays={showRaysDefault}
          />
        </div>
      )}

      {/* Theme Selection */}
      {gameState === 'theme_select' && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
          <ThemeSelector
            onSelect={handleThemeSelect}
            currentLevel={currentLevel}
            isLoading={isLoading}
          />
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', fontSize: '1.5rem', color: '#00d4ff' }}>
          GENERATING LEVEL...
        </div>
      )}

      {/* Waiting message */}
      {trainingMode && gameState === 'playing' && !levelData && (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'rgba(255,255,255,0.5)',
          fontSize: '1.2rem',
          textAlign: 'center',
          padding: '2rem',
        }}>
          Waiting for Python environment to send reset...
        </div>
      )}

      {/* Training Header HUD */}
      {trainingMode && (
        <TrainingHUD
          connected={connected}
          episodeCount={episodeCount}
          stepCount={trainingStats.stepCount}
          totalReward={trainingStats.totalReward}
          wsUrl={wsUrl}
        />
      )}

      {/* Training Footer */}
      {trainingMode && (
        <TrainingFooter
          wsUrl={wsUrl}
          connected={connected}
          trainingActive={episodeCount > 0}
          onStartTraining={() => sendControl('start')}
        />
      )}

      <style>{`
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
          overflow: hidden; 
          background: #000;
        }
        /* Handle scroll for theme select if many themes */
        .theme-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 1.5rem;
          width: 100%;
          max-width: 1000px;
          padding: 2rem;
        }
      `}</style>
    </div>
  );
}
