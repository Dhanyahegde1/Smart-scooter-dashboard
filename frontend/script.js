const BACKEND_BASE_URL = "https://YOUR-BACKEND-URL.onrender.com";
const WS_BASE_URL = BACKEND_BASE_URL.replace("https://", "wss://").replace("http://", "ws://");
class SmartScooterDashboard {
    constructor() {
        this.initState();
        this.cacheDOM();
        this.initMap();
        this.initMusicPlayer();
        this.initEventListeners();
        this.startNormalMode();
        this.updateTime();
        this.connectWebSocket();
        this.updateMLConnectionStatus();
        
        // Add initial logs
        this.addLog('Dashboard initialized', 'system');
        this.addLog('Starting WebSocket connection to ML backend...', 'ml');
        
        // Check backend health periodically
        setInterval(() => this.checkBackendHealth(), 5000);
        
        // Initial health check
        setTimeout(() => this.checkBackendHealth(), 1000);
    }
    
    initState() {
        // Scooter state
        this.speed = 33.5;
        this.acceleration = 1.2;
        this.battery = 78;
        this.rpm = 3250;
        this.distance = 5.2;
        
        // ML state
        this.anomalyScore = 0.15;
        this.reconstructionError = 0.084;
        this.mlThreshold = 0.70;
        this.mlConfidence = 95.2;
        this.mlConnected = false;
        this.mlModelReady = false;
        
        // GPS state
        this.latitude = 12.9166;
        this.longitude = 77.6161;
        
        // Music state
        this.isPlaying = true;
        this.currentTrackIndex = 0;
        this.volume = 80;
        this.tracks = [
            { title: 'Chill Vibes', artist: 'Lo-Fi Beats', duration: 225, src: "songs/audio1.mp3" },
            { title: 'Urban Drive', artist: 'Synthwave', duration: 260, src: "songs/song2.mp3" },
            { title: 'Night Rider', artist: 'Cyberpunk', duration: 195, src: "songs/song3.mp3" },
            { title: 'City Lights', artist: 'Electronic', duration: 310, src: "songs/song4.mp3" },
            { title: 'Safe Journey', artist: 'Ambient', duration: 295, src: "songs/song5.mp3" }
        ];
        
        // System state
        this.systemState = 'NORMAL';
        this.isAttackMode = false;
        this.isSafeMode = false;
        this.isSimulatingAttack = false;
        this.countdownActive = false;
        this.wsConnected = false;
        this.logEntries = [];
        
        // Attack simulation state
        this.simulationCountdown = 6;
        this.simulationTimer = null;
        
        // Map
        this.scooterMarker = null;
        this.routeCoordinates = [];
        this.mapUpdateInterval = null;
    }
    
    cacheDOM() {
        // Performance metrics
        this.currentSpeedElement = document.getElementById('currentSpeed');
        this.accelerationElement = document.getElementById('acceleration');
        this.batteryElement = document.getElementById('batteryLevel');
        this.rpmElement = document.getElementById('rpmValue');
        this.distanceElement = document.getElementById('distance');
        
        // ML metrics
        this.anomalyScoreElement = document.getElementById('anomalyScore');
        this.anomalyFillElement = document.getElementById('anomalyFill');
        this.anomalyStatusElement = document.getElementById('anomalyStatus');
        this.reconstructionErrorElement = document.getElementById('reconstructionError');
        this.mlThresholdElement = document.getElementById('mlThreshold');
        this.confidenceValueElement = document.getElementById('confidenceValue');
        this.confidenceFillElement = document.getElementById('confidenceFill');
        this.mlModelStatusElement = document.getElementById('mlModelStatus');
        
        // GPS elements
        this.latitudeElement = document.getElementById('latitude');
        this.longitudeElement = document.getElementById('longitude');
        this.lastUpdateElement = document.getElementById('lastUpdate');
        
        // Music elements
        this.audioPlayer = document.getElementById('audioPlayer');
        this.playBtn = document.getElementById('playBtn');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.volumeSlider = document.getElementById('volumeSlider');
        this.currentTrackElement = document.getElementById('currentTrack');
        this.currentArtistElement = document.getElementById('currentArtist');
        this.progressFillElement = document.getElementById('progressFill');
        this.currentTimeElement = document.getElementById('currentTime');
        this.totalTimeElement = document.getElementById('totalTime');
        this.songListElement = document.getElementById('songList');
        this.musicStatusElement = document.getElementById('musicStatus');
        this.musicPlayerElement = document.getElementById('musicPlayer');
        
        // Disabled overlays
        this.mapDisabledOverlay = document.getElementById('mapDisabledOverlay');
        this.musicDisabledOverlay = document.getElementById('musicDisabledOverlay');
        
        // Log elements
        this.logContainer = document.getElementById('logContainer');
        this.logCountElement = document.getElementById('logCount');
        this.clearLogBtn = document.getElementById('clearLog');
        
        // Overlay elements
        this.attackSimulationOverlay = document.getElementById('attackSimulationOverlay');
        this.safeModeOverlay = document.getElementById('safeModeOverlay');
        this.simulationTypeElement = document.getElementById('simulationType');
        this.simulationCountdownElement = document.getElementById('simulationCountdown');
        this.simulationProgressElement = document.getElementById('simulationProgress');
        this.acknowledgeSimulationBtn = document.getElementById('acknowledgeSimulation');
        this.acknowledgeSafeModeBtn = document.getElementById('acknowledgeSafeMode');
        
        // Attack buttons
        this.attackButtons = document.querySelectorAll('.test-attack-btn');
        this.resetSystemBtn = document.getElementById('resetSystem');
        this.emergencyAttackBtn = document.getElementById('emergencyAttack');
        
        // ML status elements
        this.mlStatusBadge = document.getElementById('mlStatusBadge');
        this.mlStatusDot = document.getElementById('mlStatusDot');
        this.mlStatusText = document.getElementById('mlStatusText');
        this.mlConnectionElement = document.getElementById('mlConnection');
        this.mlConnectionText = document.getElementById('mlConnectionText');
        this.mlBackendStatusElement = document.getElementById('mlBackendStatus');
        
        // System mode indicator
        this.systemModeElement = document.querySelector('#systemMode span');
        this.modeIndicator = document.querySelector('.mode-indicator');
        
        // Footer
        this.currentTimeDisplay = document.getElementById('currentTimeDisplay');
        
        // Filter buttons
        this.filterButtons = document.querySelectorAll('.filter-btn');
    }
    
    // ========== WEBSOCKET CONNECTION ==========
    
    connectWebSocket() {
        const wsUrl = `${WS_BASE_URL}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ Connected to ML backend');
                this.wsConnected = true;
                this.updateMLConnectionStatus();
                this.addLog('WebSocket connected to ML backend', 'ml');
                
                // Send initial connection message
                this.ws.send(JSON.stringify({ 
                    type: 'CONNECTION', 
                    status: 'CONNECTED',
                    timestamp: new Date().toISOString()
                }));
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleBackendMessage(data);
                } catch (error) {
                    console.error('Error parsing message:', error);
                    this.addLog('Error parsing ML backend message', 'ml');
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.wsConnected = false;
                this.updateMLConnectionStatus();
                this.addLog('WebSocket connection error', 'ml');
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.wsConnected = false;
                this.updateMLConnectionStatus();
                this.addLog('Disconnected from ML backend', 'ml');
                
                // Attempt reconnect after 5 seconds
                setTimeout(() => {
                    if (!this.wsConnected) {
                        this.addLog('Attempting to reconnect to ML backend...', 'ml');
                        this.connectWebSocket();
                    }
                }, 5000);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.addLog('Failed to create WebSocket connection', 'ml');
        }
    }
    
    updateMLConnectionStatus() {
        // Update header ML status
        const connectionDot = this.mlConnectionElement.querySelector('.connection-indicator');
        
        if (this.wsConnected) {
            connectionDot.className = 'connection-indicator connected';
            this.mlConnectionText.textContent = 'ML Model Connected';
            
            this.mlStatusDot.className = 'status-indicator connected';
            this.mlStatusText.textContent = 'ML Protection Active';
            
            this.mlModelStatusElement.innerHTML = '<i class="fas fa-check-circle"></i><span>Ready</span>';
            this.mlModelStatusElement.className = 'status-display ready';
            
            // Update footer status
            this.mlBackendStatusElement.innerHTML = '<div class="status-dot connected"></div><span>ML Backend: <strong>Connected</strong></span>';
            
        } else {
            connectionDot.className = 'connection-indicator connecting';
            this.mlConnectionText.textContent = 'Connecting to ML...';
            
            this.mlStatusDot.className = 'status-indicator connecting';
            this.mlStatusText.textContent = 'ML Protection Connecting...';
            
            this.mlModelStatusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Connecting...</span>';
            this.mlModelStatusElement.className = 'status-display analyzing';
            
            // Update footer status
            this.mlBackendStatusElement.innerHTML = '<div class="status-dot connecting"></div><span>ML Backend: <strong>Connecting...</strong></span>';
        }
    }
    
    handleBackendMessage(data) {
        console.log('Received from backend:', data);
        
        switch(data.type) {
            case 'INITIAL_STATE':
                this.updateSystemState(data.state);
                if (data.anomaly_score) {
                    this.anomalyScore = data.anomaly_score;
                    this.updateMLMetrics();
                }
                break;
                
            case 'ATTACK_DETECTED':
                this.handleAttackDetected(data);
                break;
                
            case 'COUNTDOWN_UPDATE':
                this.updateCountdown(data.countdown);
                break;
                
            case 'SYSTEM_STATE':
                this.updateSystemState(data.state);
                if (data.state === 'SAFE_MODE') {
                    this.activateSafeMode();
                }
                break;
                
            case 'SYSTEM_RESET':
                this.resetSafeMode();
                this.addLog('System reset by backend', 'system');
                break;
                
            case 'PONG':
                this.mlConnected = true;
                this.updateMLConnectionStatus();
                break;
                
            case 'ML_MODEL_STATUS':
                this.mlModelReady = data.ready;
                if (data.ready) {
                    this.mlModelStatusElement.innerHTML = '<i class="fas fa-check-circle"></i><span>Model Ready</span>';
                    this.mlModelStatusElement.className = 'status-display ready';
                }
                break;
        }
    }
    
    // ========== BACKEND HEALTH CHECK ==========
    
    async checkBackendHealth() {
        try {
            const response = await fetch(`${BACKEND_BASE_URL}/api/health`);
            if (response.ok) {
                const data = await response.json();
                if (this.wsConnected) {
                    this.addLog(`Backend healthy - State: ${data.state}`, 'system');
                }
                return true;
            }
        } catch (error) {
            console.error('Backend health check failed:', error);
            if (!this.wsConnected) {
                this.addLog('⚠️ ML backend not responding. Check backend deployment status', 'ml');
            }
            return false;
        }
    }
    
    // ========== SYSTEM STATE MANAGEMENT ==========
    
    updateSystemState(state) {
        this.systemState = state;
        this.isSafeMode = (state === 'SAFE_MODE');
        this.isAttackMode = (state === 'ATTACK_DETECTED');
        
        // Update UI
        this.systemModeElement.textContent = state.replace('_', ' ');
        this.modeIndicator.className = 'mode-indicator ' + 
            (state === 'SAFE_MODE' ? 'safe' : 
             state === 'ATTACK_DETECTED' ? 'attack' : 'normal');
        
        // Update anomaly score based on state
        if (state === 'ATTACK_DETECTED') {
            this.anomalyScore = 0.75 + Math.random() * 0.2;
        } else if (state === 'SAFE_MODE') {
            this.anomalyScore = 0.9 + Math.random() * 0.1;
        }
        
        this.updateMLMetrics();
    }
    
    // ========== ATTACK SIMULATION ==========
    
    async simulateAttack(attackType, isEmergency = false) {
        if (this.isSafeMode) {
            this.addLog('❌ Cannot simulate attack: System in safe mode', 'security');
            return;
        }
        
        if (!this.wsConnected) {
            this.addLog('❌ Cannot simulate attack: ML backend not connected', 'security');
            alert('ML backend not connected. Make sure the FastAPI server is running on port 8000.');
            return;
        }
        
        if (isEmergency) {
            // Emergency attack - immediate safe mode
            this.addLog('🚨 EMERGENCY ATTACK TRIGGERED', 'security');
            this.emergencyAttackBtn.classList.add('attacking');
            this.activateSafeMode();
            return;
        }
        
        // Test attack with 6-second countdown
        this.isSimulatingAttack = true;
        this.simulationCountdown = 6;
        
        try {
            // Call ML backend to get anomaly score
            const response = await fetch(`${BACKEND_BASE_URL}/api/simulate-attack`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    attack_type: attackType,
                    timestamp: new Date().toISOString()
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.addLog(`🚨 ${attackType.toUpperCase()} attack simulation started`, 'security');
                this.addLog(`ML anomaly score: ${data.anomaly_score.toFixed(3)}`, 'ml');
                
                // Update ML metrics
                this.anomalyScore = data.anomaly_score;
                this.updateMLMetrics();
                
                // Show attack simulation overlay
                this.showAttackSimulation(attackType);
                
                // Disable map and music temporarily
                this.disableSystemsTemporarily();
                
            } else {
                this.addLog(`❌ Attack simulation failed: ${data.message}`, 'security');
            }
            
        } catch (error) {
            console.error('Attack simulation error:', error);
            this.addLog('❌ Failed to simulate attack. Backend might be down.', 'security');
            
            // Fallback: Show local attack simulation
            this.showLocalAttackSimulation(attackType);
        }
    }
    
    showAttackSimulation(attackType) {
        this.simulationTypeElement.textContent = `${attackType.toUpperCase()} Attack Simulated`;
        this.attackSimulationOverlay.style.display = 'flex';
        
        // Start countdown
        this.startSimulationCountdown();
    }
    
    startSimulationCountdown() {
        let countdown = this.simulationCountdown;
        this.simulationCountdownElement.textContent = countdown;
        
        // Reset progress bar
        this.simulationProgressElement.style.width = '100%';
        this.simulationProgressElement.style.transition = 'none';
        this.simulationProgressElement.offsetHeight; // Force reflow
        this.simulationProgressElement.style.transition = `width ${countdown}s linear`;
        
        // Start progress bar animation
        setTimeout(() => {
            this.simulationProgressElement.style.width = '0%';
        }, 100);
        
        this.simulationTimer = setInterval(() => {
            countdown--;
            this.simulationCountdownElement.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(this.simulationTimer);
                this.showAttackSimulatedMessage();
                setTimeout(() => {
                    this.activateSafeMode();
                    this.attackSimulationOverlay.style.display = 'none';
                }, 2000);
            }
        }, 1000);
    }
    
    showAttackSimulatedMessage() {
        this.simulationTypeElement.textContent = 'ATTACK SIMULATED';
        this.simulationCountdownElement.textContent = 'SWITCHING TO SAFE MODE';
        this.simulationCountdownElement.style.fontSize = '24px';
        this.simulationCountdownElement.style.color = '#ff4757';
    }
    
    disableSystemsTemporarily() {
        // Disable map interactions
        if (this.map) {
            this.map.dragging.disable();
            this.map.touchZoom.disable();
            this.map.doubleClickZoom.disable();
            this.map.scrollWheelZoom.disable();
        }
        
        // Show disabled overlays
        this.mapDisabledOverlay.style.display = 'flex';
        this.musicDisabledOverlay.style.display = 'flex';
        
        // Pause music
        if (this.audioPlayer) {
            this.audioPlayer.pause();
            this.isPlaying = false;
            this.playBtn.innerHTML = '<i class="fas fa-play"></i>';
            this.musicStatusElement.innerHTML = '<i class="fas fa-ban"></i><span>Disabled</span>';
            this.musicPlayerElement.classList.add('disabled');
        }
        
        // Disable attack buttons during simulation
        this.attackButtons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
        });
    }
    
    showLocalAttackSimulation(attackType) {
        // Fallback simulation if backend is down
        this.addLog(`⚠️ Using local simulation for: ${attackType}`, 'security');
        
        this.anomalyScore = 0.85;
        this.updateMLMetrics();
        this.showAttackSimulation(attackType);
        this.disableSystemsTemporarily();
    }
    
    handleAttackDetected(data) {
        console.log('Attack detected:', data);
        
        this.isAttackMode = true;
        this.updateSystemState('ATTACK_DETECTED');
        
        if (data.anomaly_score) {
            this.anomalyScore = data.anomaly_score;
            this.updateMLMetrics();
        }
        
        this.addLog(`🚨 ML detected attack! Score: ${(data.anomaly_score || 0).toFixed(3)}`, 'security');
    }
    
    // ========== SAFE MODE HANDLING ==========
    
    activateSafeMode() {
        this.isSafeMode = true;
        this.isAttackMode = false;
        this.isSimulatingAttack = false;
        this.countdownActive = false;
        
        // Clear any simulation timers
        clearInterval(this.simulationTimer);
        
        // Hide attack simulation overlay
        this.attackSimulationOverlay.style.display = 'none';
        
        // Show safe mode overlay
        this.safeModeOverlay.style.display = 'flex';
        this.safeModeOverlay.style.zIndex = '1001';
        
        // Stop normal operations
        clearInterval(this.telemetryInterval);
        clearInterval(this.mapUpdateInterval);
        
        // Stop music completely
        if (this.audioPlayer) {
            this.audioPlayer.pause();
            this.isPlaying = false;
            this.playBtn.innerHTML = '<i class="fas fa-play"></i>';
            this.musicStatusElement.innerHTML = '<i class="fas fa-ban"></i><span>Disabled</span>';
        }
        
        // Disable map completely
        if (this.map) {
            this.map.dragging.disable();
            this.map.touchZoom.disable();
            this.map.doubleClickZoom.disable();
            this.map.scrollWheelZoom.disable();
            this.map.boxZoom.disable();
            this.map.keyboard.disable();
            
            // Show red overlay
            this.mapDisabledOverlay.style.display = 'flex';
        }
        
        // Show music disabled overlay
        this.musicDisabledOverlay.style.display = 'flex';
        this.musicPlayerElement.classList.add('disabled');
        
        // Disable all attack buttons
        this.attackButtons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
        });
        
        // Remove emergency attack animation
        this.emergencyAttackBtn.classList.remove('attacking');
        
        // Update system state
        this.updateSystemState('SAFE_MODE');
        
        // Add log entries
        this.addLog('🔒 SAFE MODE ACTIVATED', 'security');
        this.addLog('Map tracking frozen', 'system');
        this.addLog('Music system disabled', 'system');
        this.addLog('Refresh page to exit safe mode', 'ml');
    }
    
    resetSafeMode() {
        this.isSafeMode = false;
        this.isAttackMode = false;
        this.isSimulatingAttack = false;
        this.countdownActive = false;
        
        // Hide safe mode overlay
        this.safeModeOverlay.style.display = 'none';
        
        // Hide disabled overlays
        this.mapDisabledOverlay.style.display = 'none';
        this.musicDisabledOverlay.style.display = 'none';
        
        // Restart normal operations
        this.startNormalMode();
        
        // Re-enable music
        this.isPlaying = false;
        this.musicPlayerElement.classList.remove('disabled');
        this.playPause(); // This will toggle to play
        
        // Re-enable map
        if (this.map) {
            this.map.dragging.enable();
            this.map.touchZoom.enable();
            this.map.doubleClickZoom.enable();
            this.map.scrollWheelZoom.enable();
            this.map.boxZoom.enable();
            this.map.keyboard.enable();
        }
        
        // Re-enable attack buttons
        this.attackButtons.forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
        });
        
        // Update system state
        this.updateSystemState('NORMAL');
        
        this.addLog('✅ Safe mode deactivated', 'system');
    }
    
    // ========== TELEMETRY SIMULATION ==========
    
    startNormalMode() {
        // Clear existing intervals
        clearInterval(this.telemetryInterval);
        clearInterval(this.mapUpdateInterval);
        
        // Start telemetry updates
        this.telemetryInterval = setInterval(() => this.updateTelemetry(), 1000);
        
        // Start map updates
        this.mapUpdateInterval = setInterval(() => this.updateMapPosition(), 2000);
    }
    
    updateTelemetry() {
        if (this.isSafeMode || this.isSimulatingAttack) return;
        
        // Simulate normal riding data
        this.speed = 33.5 + (Math.random() - 0.5) * 3;
        this.acceleration = (Math.random() - 0.5) * 2;
        this.rpm = 3250 + (Math.random() - 0.5) * 500;
        this.distance += 0.01;
        this.battery = Math.max(0, this.battery - 0.005);
        
        // Update UI
        this.currentSpeedElement.textContent = this.speed.toFixed(1);
        this.accelerationElement.textContent = `${this.acceleration.toFixed(1)} m/s²`;
        this.batteryElement.textContent = `${Math.floor(this.battery)}%`;
        this.rpmElement.textContent = Math.floor(this.rpm).toLocaleString();
        this.distanceElement.textContent = `${this.distance.toFixed(1)} km`;
        
        // Update GPS coordinates
        this.latitude += (Math.random() - 0.5) * 0.0001;
        this.longitude += (Math.random() - 0.5) * 0.0001;
        this.latitudeElement.textContent = this.latitude.toFixed(4);
        this.longitudeElement.textContent = this.longitude.toFixed(4);
        this.lastUpdateElement.textContent = 'Just now';
        
        // Update ML metrics (simulated)
        if (!this.isAttackMode) {
            this.anomalyScore = Math.max(0.1, Math.min(0.3, this.anomalyScore + (Math.random() - 0.5) * 0.05));
            this.updateMLMetrics();
        }
        
        // Send telemetry to backend if connected
        if (this.wsConnected && this.ws.readyState === WebSocket.OPEN) {
            const telemetryData = [
                this.speed,
                this.acceleration,
                (Math.random() - 0.5) * 0.5,
                9.8 + (Math.random() - 0.5) * 0.2,
                (Math.random() - 0.5) * 0.0001,
                (Math.random() - 0.5) * 0.0001
            ];
            
            this.ws.send(JSON.stringify({
                type: 'TELEMETRY',
                data: telemetryData,
                timestamp: new Date().toISOString()
            }));
        }
    }
    
    updateMapPosition() {
        if (this.isSafeMode || !this.scooterMarker || this.isSimulatingAttack) return;
        
        // Update marker position
        this.scooterMarker.setLatLng([this.latitude, this.longitude]);
        
        // Add to route history
        this.routeCoordinates.push([this.latitude, this.longitude]);
        if (this.routeCoordinates.length > 100) {
            this.routeCoordinates.shift();
        }
        
        // Update route line
        if (this.routeLine) {
            this.routeLine.setLatLngs(this.routeCoordinates);
        }
        
        // Smooth map pan
        this.map.panTo([this.latitude, this.longitude], {
            animate: true,
            duration: 1
        });
    }
    
    // ========== ML METRICS ==========
    
    updateMLMetrics() {
        // Update anomaly score
        this.anomalyScoreElement.textContent = this.anomalyScore.toFixed(3);
        
        // Update reconstruction error (simulated)
        this.reconstructionError = this.anomalyScore * 0.1;
        this.reconstructionErrorElement.textContent = this.reconstructionError.toFixed(3);
        
        // Update threshold
        this.mlThresholdElement.textContent = this.mlThreshold.toFixed(2);
        
        // Update confidence
        this.mlConfidence = Math.max(50, 100 - (this.anomalyScore * 50));
        this.confidenceValueElement.textContent = `${this.mlConfidence.toFixed(1)}%`;
        this.confidenceFillElement.style.width = `${this.mlConfidence}%`;
        
        // Update anomaly gauge
        const anomalyPercentage = Math.min(this.anomalyScore * 100, 100);
        const degrees = (anomalyPercentage / 100) * 360;
        
        let gaugeColor = '#00ff9d'; // Green
        if (this.anomalyScore > 0.7) gaugeColor = '#fbbf24'; // Yellow
        if (this.anomalyScore > 0.9) gaugeColor = '#ff4757'; // Red
        
        this.anomalyFillElement.style.background = 
            `conic-gradient(${gaugeColor} 0deg, ${gaugeColor} ${degrees}deg, #2d3748 ${degrees}deg, #2d3748 360deg)`;
        
        // Update status text
        if (this.anomalyScore < 0.3) {
            this.anomalyStatusElement.innerHTML = '<i class="fas fa-check-circle"></i> Normal Behavior';
            this.anomalyStatusElement.style.color = '#00ff9d';
        } else if (this.anomalyScore < 0.7) {
            this.anomalyStatusElement.innerHTML = '<i class="fas fa-exclamation-circle"></i> Suspicious Pattern';
            this.anomalyStatusElement.style.color = '#fbbf24';
        } else {
            this.anomalyStatusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Anomaly Detected';
            this.anomalyStatusElement.style.color = '#ff4757';
        }
    }
    
    // ========== MAP INITIALIZATION ==========
    
    initMap() {
        try {
            this.map = L.map('map').setView([12.9166, 77.6161], 15);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(this.map);
            
            // Create custom scooter icon
            const scooterIcon = L.divIcon({
                className: 'scooter-marker',
                html: '<i class="fas fa-motorcycle" style="color: #00f3ff; font-size: 32px; text-shadow: 0 0 10px #00f3ff;"></i>',
                iconSize: [40, 40],
                iconAnchor: [20, 40]
            });
            
            // Add scooter marker
            this.scooterMarker = L.marker([this.latitude, this.longitude], {
                icon: scooterIcon,
                zIndexOffset: 1000
            }).addTo(this.map);
            
            // Add route line
            this.routeLine = L.polyline([], {
                color: '#00f3ff',
                weight: 3,
                opacity: 0.7,
                lineCap: 'round'
            }).addTo(this.map);
            
            // Add destination marker
            const destinationIcon = L.divIcon({
                className: 'destination-marker',
                html: '<i class="fas fa-map-marker-alt" style="color: #ff4757; font-size: 28px;"></i>',
                iconSize: [30, 30],
                iconAnchor: [15, 30]
            });
            
            L.marker([12.9266, 77.6261], { icon: destinationIcon })
                .addTo(this.map)
                .bindPopup('Destination: Oxford College<br>Distance: 2.3 km')
                .openPopup();
                
            this.addLog('Map initialized successfully', 'system');
            
        } catch (error) {
            console.error('Failed to initialize map:', error);
            this.addLog('❌ Failed to initialize map', 'system');
        }
    }
    
    // ========== MUSIC PLAYER ==========
    
    initMusicPlayer() {
        // Set initial track source
        this.audioPlayer.src = this.tracks[this.currentTrackIndex].src;
        this.audioPlayer.volume = this.volume / 100;
        this.volumeSlider.value = this.volume;
        this.populateSongList();
        
        // Set initial track info
        this.currentTrackElement.textContent = this.tracks[this.currentTrackIndex].title;
        this.currentArtistElement.textContent = this.tracks[this.currentTrackIndex].artist;
        
        const minutes = Math.floor(this.tracks[this.currentTrackIndex].duration / 60);
        const seconds = this.tracks[this.currentTrackIndex].duration % 60;
        this.totalTimeElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        this.audioPlayer.addEventListener('timeupdate', () => this.updateProgress());
        this.audioPlayer.addEventListener('ended', () => this.nextTrack());
        
        // Try to play audio
        setTimeout(() => {
            if (!this.isSafeMode && this.isPlaying) {
                this.audioPlayer.play().then(() => {
                    this.playBtn.innerHTML = '<i class="fas fa-pause"></i>';
                    this.musicStatusElement.innerHTML = '<i class="fas fa-play-circle"></i><span>Playing</span>';
                    this.addLog('Music player initialized and playing', 'music');
                }).catch((error) => {
                    console.log('Autoplay blocked or failed:', error);
                    this.isPlaying = false;
                    this.playBtn.innerHTML = '<i class="fas fa-play"></i>';
                    this.musicStatusElement.innerHTML = '<i class="fas fa-play-circle"></i><span>Click to play</span>';
                    this.addLog('Music autoplay blocked by browser. Click play button to start.', 'music');
                });
            }
        }, 1000);
    }
    
    populateSongList() {
        this.songListElement.innerHTML = '';
        
        this.tracks.forEach((track, index) => {
            const songItem = document.createElement('div');
            songItem.className = `song-item ${index === this.currentTrackIndex ? 'active' : ''}`;
            
            const minutes = Math.floor(track.duration / 60);
            const seconds = track.duration % 60;
            const durationText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            songItem.innerHTML = `
                <i class="fas fa-music"></i>
                <div class="song-info">
                    <div class="song-title">${track.title}</div>
                    <div class="song-artist">${track.artist}</div>
                </div>
                <div class="song-duration">${durationText}</div>
            `;
            
            songItem.addEventListener('click', () => {
                if (!this.isSafeMode && !this.isSimulatingAttack) {
                    this.selectTrack(index);
                }
            });
            
            this.songListElement.appendChild(songItem);
        });
    }
    
    playPause() {
        if (this.isSafeMode || this.isSimulatingAttack) return;
        
        this.isPlaying = !this.isPlaying;
        
        if (this.isPlaying) {
            this.audioPlayer.play().then(() => {
                this.playBtn.innerHTML = '<i class="fas fa-pause"></i>';
                this.musicStatusElement.innerHTML = '<i class="fas fa-play-circle"></i><span>Playing</span>';
                this.addLog('Music playing', 'music');
            }).catch(error => {
                console.error('Play failed:', error);
                this.isPlaying = false;
                this.playBtn.innerHTML = '<i class="fas fa-play"></i>';
                this.addLog('Music playback failed - check console', 'music');
            });
        } else {
            this.audioPlayer.pause();
            this.playBtn.innerHTML = '<i class="fas fa-play"></i>';
            this.musicStatusElement.innerHTML = '<i class="fas fa-pause-circle"></i><span>Paused</span>';
            this.addLog('Music paused', 'music');
        }
    }
    
    nextTrack() {
        if (this.isSafeMode || this.isSimulatingAttack) return;
        
        this.currentTrackIndex = (this.currentTrackIndex + 1) % this.tracks.length;
        this.selectTrack(this.currentTrackIndex);
    }
    
    prevTrack() {
        if (this.isSafeMode || this.isSimulatingAttack) return;
        
        this.currentTrackIndex = (this.currentTrackIndex - 1 + this.tracks.length) % this.tracks.length;
        this.selectTrack(this.currentTrackIndex);
    }
    
    selectTrack(index) {
        if (this.isSafeMode || this.isSimulatingAttack) return;
        
        this.currentTrackIndex = index;
        const track = this.tracks[index];
        
        this.currentTrackElement.textContent = track.title;
        this.currentArtistElement.textContent = track.artist;
        
        const minutes = Math.floor(track.duration / 60);
        const seconds = track.duration % 60;
        this.totalTimeElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // Update active song in list
        document.querySelectorAll('.song-item').forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
        
        // Change audio source and load
        this.audioPlayer.src = track.src;
        this.audioPlayer.load();
        
        this.addLog(`Selected track: ${track.title}`, 'music');
        
        if (this.isPlaying) {
            this.audioPlayer.play().then(() => {
                this.playBtn.innerHTML = '<i class="fas fa-pause"></i>';
                this.musicStatusElement.innerHTML = '<i class="fas fa-play-circle"></i><span>Playing</span>';
            }).catch(error => {
                console.error("Play failed:", error);
                this.isPlaying = false;
                this.playBtn.innerHTML = '<i class="fas fa-play"></i>';
            });
        }
    }
    
    updateProgress() {
        if (!this.audioPlayer.duration || isNaN(this.audioPlayer.duration)) return;
        
        const progress = (this.audioPlayer.currentTime / this.audioPlayer.duration) * 100;
        this.progressFillElement.style.width = `${progress}%`;
        
        const formatTime = (seconds) => {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        };
        
        this.currentTimeElement.textContent = formatTime(this.audioPlayer.currentTime);
    }
    
    updateVolume() {
        this.volume = this.volumeSlider.value;
        this.audioPlayer.volume = this.volume / 100;
    }
    
    // ========== EVENT LISTENERS ==========
    
    initEventListeners() {
        // Music controls
        this.playBtn.addEventListener('click', () => this.playPause());
        this.prevBtn.addEventListener('click', () => this.prevTrack());
        this.nextBtn.addEventListener('click', () => this.nextTrack());
        this.volumeSlider.addEventListener('input', () => this.updateVolume());
        
        // Attack simulation buttons
        this.attackButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const attackType = e.target.closest('.test-attack-btn').dataset.attack;
                this.simulateAttack(attackType, false);
            });
        });
        
        // Emergency attack button
        this.emergencyAttackBtn.addEventListener('click', () => {
            this.simulateAttack('EMERGENCY', true);
        });
        
        // System controls
        this.resetSystemBtn.addEventListener('click', () => this.resetSystem());
        
        // Overlay controls
        this.acknowledgeSimulationBtn.addEventListener('click', () => {
            this.attackSimulationOverlay.style.display = 'none';
            clearInterval(this.simulationTimer);
            this.isSimulatingAttack = false;
        });
        
        this.acknowledgeSafeModeBtn.addEventListener('click', () => {
            this.safeModeOverlay.style.display = 'none';
        });
        
        // Log controls
        this.clearLogBtn.addEventListener('click', () => this.clearLog());
        
        // Filter buttons
        this.filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.filterLogs(filter);
                this.filterButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }
    
    // ========== SYSTEM CONTROLS ==========
    
    async resetSystem() {
        try {
            const response = await fetch(`${BACKEND_BASE_URL}/api/reset-system`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.resetSafeMode();
                this.addLog('System reset requested', 'system');
            }
        } catch (error) {
            console.error('Reset failed, using local reset:', error);
            this.resetSafeMode();
            this.addLog('System reset (local)', 'system');
        }
    }
    
    // ========== LOG SYSTEM ==========
    
    addLog(message, type = 'system') {
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        
        const logEntry = {
            timestamp,
            message,
            type,
            id: Date.now() + Math.random()
        };
        
        this.logEntries.unshift(logEntry);
        
        if (this.logEntries.length > 20) {
            this.logEntries.pop();
        }
        
        this.updateLogDisplay();
    }
    
    updateLogDisplay(filter = 'all') {
        this.logContainer.innerHTML = '';
        
        const filteredLogs = filter === 'all' 
            ? this.logEntries 
            : this.logEntries.filter(log => log.type === filter);
        
        filteredLogs.forEach(log => {
            const logElement = document.createElement('div');
            logElement.className = `log-entry ${log.type}`;
            logElement.innerHTML = `
                <div class="log-time">${log.timestamp}</div>
                <div class="log-message">${log.message}</div>
            `;
            this.logContainer.appendChild(logElement);
        });
        
        this.logCountElement.textContent = `${filteredLogs.length} Events`;
    }
    
    filterLogs(filter) {
        this.updateLogDisplay(filter);
    }
    
    clearLog() {
        this.logEntries = [];
        this.updateLogDisplay();
        this.addLog('Event log cleared', 'system');
    }
    
    // ========== UTILITIES ==========
    
    updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        this.currentTimeDisplay.textContent = timeString;
        
        setTimeout(() => this.updateTime(), 1000);
    }
    
    updateCountdown(seconds) {
        if (this.countdownNumberElement) {
            this.countdownNumberElement.textContent = seconds;
        }
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Smart Scooter Dashboard...');
    window.dashboard = new SmartScooterDashboard();
});