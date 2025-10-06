document.addEventListener('DOMContentLoaded', () => {
    // --- DOM ELEMENT SELECTION ---
    const ideaInput = document.getElementById('idea-input');
    const platformSelector = document.getElementById('platform-selector');
    const brandVoiceInput = document.getElementById('brand-voice');
    const creativitySlider = document.getElementById('creativity-slider');
    const generateBtn = document.getElementById('generate-btn');
    const suggestionGrid = document.getElementById('suggestion-grid');
    const formalitySlider = document.getElementById('formality-slider'); 
    const targetAudienceInput = document.getElementById('target-audience');
    const outputText = document.getElementById('output-text');
    const outputTabsContainer = document.getElementById('output-tabs');
    const editBtn = document.getElementById('edit-btn');
    const copyBtn = document.getElementById('copy-btn');
    const humanizeBtn = document.getElementById('humanize-btn');
    const refineBtn = document.getElementById('refine-btn');
    const ttsControls = document.getElementById('tts-controls');
    const scoreSection = document.querySelector('.score-section');
    const refineContainer = document.getElementById('refine-container');
    const refineInput = document.getElementById('refine-input');
    const submitRefineBtn = document.getElementById('submit-refine-btn');
    const cancelRefineBtn = document.getElementById('cancel-refine-btn');
    const voiceSelector = document.getElementById('voice-selector');
    const maleVoiceBtn = document.getElementById('male-voice-btn');
    const femaleVoiceBtn = document.getElementById('female-voice-btn');
    const playBtn = document.getElementById('play-btn');
    const stopBtn = document.getElementById('stop-btn');
    const readabilityScoreEl = document.getElementById('readability-score');
    const engagementScoreEl = document.getElementById('engagement-score');
    const humanLikenessScoreEl = document.getElementById('human-likeness-score');
    const justificationBox = document.getElementById('justification-box');
    const generateVideoBtn = document.getElementById('generate-video-btn');
    const videoPlayerContainer = document.getElementById('video-player-container');
    const videoPlayer = document.getElementById('video-player');
    
    // --- STATE VARIABLES ---
    let selectedPlatform = 'Instagram';
    let generatedVersions = [];
    let maleVoice = null;
    let femaleVoice = null;
    let selectedGender = 'female';
    let activeVersionIndex = 0;

    // --- INITIALIZE SPEECH SYNTHESIS ---
    const synth = window.speechSynthesis;
    if (!synth) {
        ttsControls.style.display = 'none';
        console.warn('Browser does not support the Web Speech API.');
    }
    function findAndSetVoices() {
        let voices = synth.getVoices();
        if (voices.length === 0) return;
        maleVoice = voices.find(voice => voice.lang.startsWith('en') && (voice.name.toLowerCase().includes('male') || voice.name.includes('David') || voice.name.includes('Mark')));
        femaleVoice = voices.find(voice => voice.lang.startsWith('en') && (voice.name.toLowerCase().includes('female') || voice.name.includes('Zira') || voice.name.includes('Susan')));
        if (!maleVoice) maleVoiceBtn.style.display = 'none';
        if (!femaleVoice) femaleVoiceBtn.style.display = 'none';
    }
    if (synth) {
        speechSynthesis.onvoiceschanged = findAndSetVoices;
        findAndSetVoices();
    }

    // --- EVENT LISTENERS ---
    platformSelector.addEventListener('click', (e) => {
        const button = e.target.closest('.platform-btn');
        if (button) {
            platformSelector.querySelector('.active').classList.remove('active');
            button.classList.add('active');
            selectedPlatform = button.dataset.platform;
        }
    });
    generateBtn.addEventListener('click', generateContent);
    outputTabsContainer.addEventListener('click', (e) => {
        const button = e.target.closest('.output-tab-btn');
        if (button) {
            const index = parseInt(button.dataset.index, 10);
            showVersion(index);
        }
    });
    voiceSelector.addEventListener('click', (e) => {
        const button = e.target.closest('.voice-btn');
        if (button) {
            selectedGender = button.dataset.gender;
            maleVoiceBtn.classList.toggle('active', selectedGender === 'male');
            femaleVoiceBtn.classList.toggle('active', selectedGender === 'female');
        }
    });
    suggestionGrid.addEventListener('click', (e) => {
        const button = e.target.closest('.suggestion-btn');
        if (button) {
            ideaInput.value = button.textContent;
            ideaInput.focus();
        }
    });
    editBtn.addEventListener('click', () => {
        const isReadOnly = outputText.hasAttribute('readonly');
        if (isReadOnly) {
            outputText.removeAttribute('readonly');
            editBtn.classList.add('active');
            outputText.focus();
        } else {
            outputText.setAttribute('readonly', true);
            editBtn.classList.remove('active');
        }
    });
    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(outputText.value).then(() => {
            const originalIcon = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                copyBtn.innerHTML = originalIcon;
            }, 1500);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    });
    humanizeBtn.addEventListener('click', async () => {
        const currentText = outputText.value;
        if (!currentText.trim() || humanizeBtn.disabled) {
            return;
        }
        const originalIcon = humanizeBtn.innerHTML;
        humanizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        humanizeBtn.disabled = true;
        editBtn.disabled = true;
        try {
            const response = await fetch('/humanize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: currentText }),
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "An unknown error occurred." }));
                throw new Error(`HTTP error! Status: ${response.status} - ${errorData.detail}`);
            }
            const data = await response.json();
            outputText.value = data.humanized_text;
        } catch (error) {
            console.error('Humanize Error:', error);
            alert(`Could not humanize text. \nDetails: ${error.message}`);
        } finally {
            humanizeBtn.innerHTML = originalIcon;
            humanizeBtn.disabled = false;
            editBtn.disabled = false;
        }
    });
    refineBtn.addEventListener('click', () => {
        if (outputText.value.trim() === '') return;
        ttsControls.classList.add('hidden');
        scoreSection.classList.add('hidden');
        refineContainer.classList.remove('hidden');
        refineInput.focus();
    });
    cancelRefineBtn.addEventListener('click', () => {
        refineContainer.classList.add('hidden');
        ttsControls.classList.remove('hidden');
        scoreSection.classList.remove('hidden');
        refineInput.value = '';
    });
    submitRefineBtn.addEventListener('click', async () => {
        const instruction = refineInput.value;
        if (!instruction || !instruction.trim() || submitRefineBtn.disabled) {
            return;
        }
        const originalText = submitRefineBtn.textContent;
        submitRefineBtn.textContent = 'Refining...';
        submitRefineBtn.disabled = true;
        cancelRefineBtn.disabled = true;
        const currentSettings = {
            idea: ideaInput.value,
            platform: selectedPlatform,
            tone: brandVoiceInput.value,
            creativity: parseFloat(creativitySlider.value),
            formality: parseFloat(formalitySlider.value),
            smart_emojis: document.getElementById('smart-emojis-toggle').dataset.active === 'true',
            auto_hashtag: document.getElementById('auto-hashtag-toggle').dataset.active === 'true',
            contextual_suggestions: document.getElementById('contextual-suggestions-toggle').dataset.active === 'true',
            target_audience: targetAudienceInput.value,
            original_content: generatedVersions[activeVersionIndex].content,
            refinement_instruction: instruction
        };
        try {
            const response = await fetch('/refine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentSettings),
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "An unknown error occurred." }));
                throw new Error(`HTTP error! Status: ${response.status} - ${errorData.detail}`);
            }
            const newVersion = await response.json();
            generatedVersions[activeVersionIndex] = newVersion;
            showVersion(activeVersionIndex);
        } catch (error) {
            console.error('Refine Error:', error);
            alert(`Could not refine content. \nDetails: ${error.message}`);
        } finally {
            submitRefineBtn.textContent = originalText;
            submitRefineBtn.disabled = false;
            cancelRefineBtn.disabled = false;
            refineContainer.classList.add('hidden');
            ttsControls.classList.remove('hidden');
            scoreSection.classList.remove('hidden');
            refineInput.value = '';
        }
    });
    generateVideoBtn.addEventListener('click', async () => {
        if (selectedPlatform !== 'Instagram' || !generatedVersions[activeVersionIndex]) {
            alert("Please generate an Instagram post with a script first to create a video.");
            return;
        }
        const currentVersion = generatedVersions[activeVersionIndex];
        const scriptText = currentVersion.content.script;
        const originalIdea = ideaInput.value;
        if (!scriptText) {
            alert("The current version does not have a script to generate a video from.");
            return;
        }
        generateVideoBtn.disabled = true;
        generateVideoBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Assembling Video...';
        videoPlayerContainer.classList.add('hidden');
        try {
            const response = await fetch('/generate-video', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ script: scriptText, idea: originalIdea }),
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "An unknown error occurred." }));
                throw new Error(`HTTP error! Status: ${response.status} - ${errorData.detail}`);
            }
            const data = await response.json();
            videoPlayer.src = data.video_url + `?t=${new Date().getTime()}`;
            videoPlayerContainer.classList.remove('hidden');
            videoPlayer.load();
        } catch (error) {
            console.error('Video Generation Error:', error);
            alert(`Could not generate video. \nDetails: ${error.message}`);
        } finally {
            generateVideoBtn.disabled = false;
            generateVideoBtn.innerHTML = '<i class="fas fa-film"></i> Generate Video Reel';
        }
    });

    // --- TTS FUNCTIONS ---
    function speakText() {
        if (synth.speaking) { return; }
        const textToSpeak = outputText.value;
        if (textToSpeak.trim() !== '') {
            synth.cancel();
            const utterance = new SpeechSynthesisUtterance(textToSpeak);
            if (selectedGender === 'male' && maleVoice) utterance.voice = maleVoice;
            else if (selectedGender === 'female' && femaleVoice) utterance.voice = femaleVoice;
            utterance.onstart = () => { playBtn.disabled = true; stopBtn.disabled = false; };
            utterance.onend = () => { playBtn.disabled = false; stopBtn.disabled = true; };
            utterance.onerror = (e) => { console.error('Speech synthesis error:', e); playBtn.disabled = false; stopBtn.disabled = true; };
            synth.speak(utterance);
        }
    }
    function stopText() {
        synth.cancel();
    }
    if (synth) {
        playBtn.addEventListener('click', speakText);
        stopBtn.addEventListener('click', stopText);
        stopBtn.disabled = true;
    }

    // --- CORE API FUNCTION ---
    async function generateContent() {
        if (generateBtn.classList.contains('loading')) return;
        const idea = ideaInput.value;
        const tone = brandVoiceInput.value;
        const creativity = parseFloat(creativitySlider.value);
        const formality = parseFloat(formalitySlider.value);
        const smartEmojis = document.getElementById('smart-emojis-toggle').dataset.active === 'true';
        const autoHashtag = document.getElementById('auto-hashtag-toggle').dataset.active === 'true';
        const contextualSuggestions = document.getElementById('contextual-suggestions-toggle').dataset.active === 'true';
        const targetAudience = targetAudienceInput.value;
        if (!idea.trim() || !tone.trim()) {
            alert('Please fill in the idea and brand voice fields.');
            return;
        }
        setLoadingState(true);
        clearResults();
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ idea, platform: selectedPlatform, tone, creativity, formality, smart_emojis: smartEmojis, auto_hashtag: autoHashtag, contextual_suggestions: contextualSuggestions, target_audience: targetAudience }),
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "An unknown error occurred on the server." }));
                throw new Error(`${errorData.detail}`);
            }
            const data = await response.json();
            if (data.versions && data.versions.length > 0) {
                displayResults(data.versions);
            } else {
                // This case should now be rare due to the improved backend error handling
                throw new Error("Received an empty or invalid versions array from the server.");
            }
        } catch (error) {
            console.error('Error:', error);
            outputText.value = `An error occurred.\n\nDetails: ${error.message}`;
        } finally {
            setLoadingState(false);
        }
    }

    // --- HELPER FUNCTIONS ---
    function setLoadingState(isLoading) {
        if (isLoading) {
            generateBtn.classList.add('loading');
            generateBtn.textContent = 'Generating...';
        } else {
            generateBtn.classList.remove('loading');
            generateBtn.textContent = 'Generate Content';
        }
    }

    function clearResults() {
        if (synth && synth.speaking) { synth.cancel(); }
        outputText.value = '';
        outputTabsContainer.innerHTML = '';
        generatedVersions = [];
        readabilityScoreEl.textContent = '0%';
        engagementScoreEl.textContent = '0%';
        humanLikenessScoreEl.textContent = '0%';
        updateShape(0, 0);
        updateShape(1, 0);
        updateShape(2, 0);
        document.querySelectorAll('.char-count').forEach(el => el.remove());
        justificationBox.innerHTML = '';
        justificationBox.classList.add('hidden');
        if (videoPlayerContainer) videoPlayerContainer.classList.add('hidden');
        if (videoPlayer) videoPlayer.src = "";
    }

    function displayResults(versions) {
        generatedVersions = versions;
        outputTabsContainer.innerHTML = ''; 
        versions.forEach((version, index) => {
            const button = document.createElement('button');
            button.classList.add('output-tab-btn');
            button.textContent = `Version ${index + 1}`;
            button.dataset.index = index;
            if (version.virality_score) {
                const scoreSpan = document.createElement('span');
                scoreSpan.className = 'virality-score';
                scoreSpan.innerHTML = `🔥 ${version.virality_score}`;
                button.appendChild(scoreSpan);
            }
            outputTabsContainer.appendChild(button);
        });
        if (versions.length > 0) {
            showVersion(0);
        }
    }

    function showVersion(index) {
        if (index >= generatedVersions.length || index < 0) return;
        activeVersionIndex = index;
        if (synth && synth.speaking) { synth.cancel(); }
        outputText.setAttribute('readonly', true);
        editBtn.classList.remove('active');
        const buttons = outputTabsContainer.querySelectorAll('.output-tab-btn');
        buttons.forEach((btn, i) => btn.classList.toggle('active', i === index));
        const versionData = generatedVersions[index];
        const { content, analysis, justification } = versionData;
        let formattedContent = "";
        document.querySelectorAll('.char-count').forEach(el => el.remove());
        
        if (typeof content === 'string') {
            formattedContent = content;
        } else if (content && content.caption && content.script) {
            // NEW: Added labels for clarity
            formattedContent = `CAPTION:\n${content.caption}\n\n---\n\nSCRIPT:\n${content.script}`;
        } else if (content && content.thread && Array.isArray(content.thread)) {
            const X_CHAR_LIMIT = 280;
            formattedContent = "";
            const wrapper = outputText.parentElement;
            content.thread.forEach((tweet, i) => {
                const lineCount = (formattedContent.match(/\n/g) || []).length;
                formattedContent += `[${i + 1}/${content.thread.length}]\n${tweet}\n\n`;
                const charCountEl = document.createElement('div');
                charCountEl.className = 'char-count';
                const charLength = tweet.length;
                charCountEl.textContent = `${charLength} / ${X_CHAR_LIMIT}`;
                charCountEl.style.top = `${2 + (lineCount * 1.5)}rem`;
                if (charLength > X_CHAR_LIMIT) { charCountEl.classList.add('over-limit'); }
                wrapper.appendChild(charCountEl);
            });
        } else {
            // Fallback for unexpected content structures, e.g. for LinkedIn/Blog if AI returns an object
            formattedContent = "Error: Received unexpected content format.\n\n" + JSON.stringify(content, null, 2);
        }
        outputText.value = formattedContent.trim();

        if (justification) {
            justificationBox.innerHTML = `<p><strong>AI Analyst:</strong> <em>"${justification}"</em></p>`;
            justificationBox.classList.remove('hidden');
        } else {
            justificationBox.innerHTML = '';
            justificationBox.classList.add('hidden');
        }

        readabilityScoreEl.textContent = `${analysis.readability}%`;
        engagementScoreEl.textContent = `${analysis.engagement_potential}%`;
        humanLikenessScoreEl.textContent = `${analysis.human_likeness}%`;
        updateShape(0, analysis.readability);
        updateShape(1, analysis.engagement_potential);
        updateShape(2, analysis.human_likeness);
    }

    // --- THREE.JS & PRELOADER LOGIC ---
    let scoreScenes = [], scoreCameras = [], scoreRenderers = [], wireframeMeshes = [], solidMeshes = [];
    function initScoreShapes() { const canvases = [document.getElementById('shape-canvas-1'), document.getElementById('shape-canvas-2'), document.getElementById('shape-canvas-3')]; canvases.forEach(canvas => { if (!canvas) return; const scene = new THREE.Scene(); scoreScenes.push(scene); const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000); camera.position.z = 2; scoreCameras.push(camera); const renderer = new THREE.WebGLRenderer({ canvas: canvas, antalias: true, alpha: true }); renderer.setSize(canvas.clientWidth, canvas.clientHeight); renderer.setPixelRatio(window.devicePixelRatio); scoreRenderers.push(renderer); const geometry = new THREE.IcosahedronGeometry(1, 0); const wireframeMaterial = new THREE.MeshBasicMaterial({ color: 0x6a6aff, wireframe: true }); const wireframeMesh = new THREE.Mesh(geometry, wireframeMaterial); scene.add(wireframeMesh); wireframeMeshes.push(wireframeMesh); const solidMaterial = new THREE.MeshBasicMaterial({ color: 0x8282ff, transparent: true, opacity: 0.5 }); const solidMesh = new THREE.Mesh(geometry, solidMaterial); solidMesh.scale.set(0, 0, 0); scene.add(solidMesh); solidMeshes.push(solidMesh) }) }
    function animateScoreShapes() { if(wireframeMeshes.every(el => el === undefined)) return; wireframeMeshes.forEach(mesh => { mesh.rotation.x += 0.002; mesh.rotation.y += 0.003; }); solidMeshes.forEach(mesh => { mesh.rotation.x += 0.002; mesh.rotation.y += 0.003; }); for (let i = 0; i < scoreScenes.length; i++) { if(scoreRenderers[i]) scoreRenderers[i].render(scoreScenes[i], scoreCameras[i]); } }
    function updateShape(index, percentage) { if (!solidMeshes[index]) return; const targetScale = percentage / 100; const mesh = solidMeshes[index]; const startScale = mesh.scale.x; const deltaScale = targetScale - startScale; let duration = 1000; let startTime = null; function animationStep(timestamp) { if (!startTime) startTime = timestamp; const progress = Math.min((timestamp - startTime) / duration, 1); const newScale = startScale + deltaScale * progress; mesh.scale.set(newScale, newScale, newScale); if (progress < 1) { requestAnimationFrame(animationStep); } } requestAnimationFrame(animationStep); }
    let plexusScene, plexusCamera, plexusRenderer, particles, group; function initPlexusAnimation() { const container = document.querySelector('.network-canvas-container'); const canvas = document.getElementById('plexus-canvas'); if (!container || !canvas) return; plexusScene = new THREE.Scene(); plexusCamera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000); plexusCamera.position.z = 15; plexusRenderer = new THREE.WebGLRenderer({ canvas: canvas, antalias: true, alpha: true }); plexusRenderer.setSize(container.clientWidth, container.clientHeight); plexusRenderer.setPixelRatio(window.devicePixelRatio); const particleCount = 100; const particlesGeometry = new THREE.BufferGeometry(); const positions = new Float32Array(particleCount * 3); for (let i = 0; i < particleCount; i++) { positions[i * 3] = (Math.random() - 0.5) * 30; positions[i * 3 + 1] = (Math.random() - 0.5) * 15; positions[i * 3 + 2] = (Math.random() - 0.5) * 10 } particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3)); const particleMaterial = new THREE.PointsMaterial({ color: 0x32b9f7, size: 0.1, blending: THREE.AdditiveBlending, transparent: true }); particles = new THREE.Points(particlesGeometry, particleMaterial); const lineGeometry = new THREE.BufferGeometry(); const linePositions = new Float32Array(particleCount * particleCount * 3); lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3)); const lineMaterial = new THREE.LineBasicMaterial({ color: 0x32b9f7, transparent: true, opacity: 0.1, blending: THREE.AdditiveBlending }); const lines = new THREE.LineSegments(lineGeometry, lineMaterial); group = new THREE.Group(); group.add(particles); group.add(lines); plexusScene.add(group) }
    function animatePlexus() { if (!particles || !group || !plexusRenderer) return; group.rotation.y += 0.0005; const positions = particles.geometry.attributes.position.array; const linePositions = group.children[1].geometry.attributes.position.array; let vertexPos = 0; const particleCount = positions.length / 3; for (let i = 0; i < particleCount; i++) { for (let j = i + 1; j < particleCount; j++) { const dx = positions[i * 3] - positions[j * 3]; const dy = positions[i * 3 + 1] - positions[j * 3 + 1]; const dz = positions[i * 3 + 2] - positions[j * 3 + 2]; const dist = Math.sqrt(dx * dx + dy * dy + dz * dz); if (dist < 4) { linePositions[vertexPos++] = positions[i * 3]; linePositions[vertexPos++] = positions[i * 3 + 1]; linePositions[vertexPos++] = positions[i * 3 + 2]; linePositions[vertexPos++] = positions[j * 3]; linePositions[vertexPos++] = positions[j * 3 + 1]; linePositions[vertexPos++] = positions[j * 3 + 2] } } } group.children[1].geometry.setDrawRange(0, vertexPos / 3); group.children[1].geometry.attributes.position.needsUpdate = true; plexusRenderer.render(plexusScene, plexusCamera) }
    let preloaderScene, preloaderCamera, preloaderRenderer, preloaderParticles, preloaderGroup; function initPreloaderPlexus() { const canvas = document.getElementById('preloader-canvas'); if (!canvas) return; preloaderScene = new THREE.Scene(); preloaderCamera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000); preloaderCamera.position.z = 25; preloaderRenderer = new THREE.WebGLRenderer({ canvas: canvas, antalias: true, alpha: true }); preloaderRenderer.setSize(window.innerWidth, window.innerHeight); preloaderRenderer.setPixelRatio(window.devicePixelRatio); const particleCount = 150; const particlesGeometry = new THREE.BufferGeometry(); const positions = new Float32Array(particleCount * 3); for (let i = 0; i < particleCount; i++) { positions[i * 3] = (Math.random() - 0.5) * 50; positions[i * 3 + 1] = (Math.random() - 0.5) * 50; positions[i * 3 + 2] = (Math.random() - 0.5) * 50; } particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3)); const particleMaterial = new THREE.PointsMaterial({ color: 0x6a6aff, size: 0.15, blending: THREE.AdditiveBlending, transparent: true }); preloaderParticles = new THREE.Points(particlesGeometry, particleMaterial); const lineMaterial = new THREE.LineBasicMaterial({ color: 0x6a6aff, transparent: true, opacity: 0.1, blending: THREE.AdditiveBlending }); const lineGeometry = new THREE.BufferGeometry(); const linePositions = new Float32Array(particleCount * particleCount * 3); lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3)); const lines = new THREE.LineSegments(lineGeometry, lineMaterial); preloaderGroup = new THREE.Group(); preloaderGroup.add(preloaderParticles); preloaderGroup.add(lines); preloaderScene.add(preloaderGroup); }
    function animatePreloaderPlexus() { if (!preloaderGroup || !preloaderRenderer) return; preloaderGroup.rotation.y += 0.001; preloaderGroup.rotation.x += 0.0005; const positions = preloaderParticles.geometry.attributes.position.array; const linePositions = preloaderGroup.children[1].geometry.attributes.position.array; let vertexPos = 0; const particleCount = positions.length / 3; for (let i = 0; i < particleCount; i++) { for (let j = i + 1; j < particleCount; j++) { const dx = positions[i * 3] - positions[j * 3]; const dy = positions[i * 3 + 1] - positions[j * 3 + 1]; const dz = positions[i * 3 + 2] - positions[j * 3 + 2]; const dist = Math.sqrt(dx * dx + dy * dy + dz * dz); if (dist < 6) { linePositions[vertexPos++] = positions[i * 3]; linePositions[vertexPos++] = positions[i * 3 + 1]; linePositions[vertexPos++] = positions[i * 3 + 2]; linePositions[vertexPos++] = positions[j * 3]; linePositions[vertexPos++] = positions[j * 3 + 1]; linePositions[vertexPos++] = positions[j * 3 + 2]; } } } preloaderGroup.children[1].geometry.setDrawRange(0, vertexPos / 3); preloaderGroup.children[1].geometry.attributes.position.needsUpdate = true; preloaderRenderer.render(preloaderScene, preloaderCamera); }
    function animate() { requestAnimationFrame(animate); animateScoreShapes(); animatePlexus(); animatePreloaderPlexus(); }
    const toggleableOptions = document.querySelectorAll('.toggleable-option'); toggleableOptions.forEach(option => { option.addEventListener('click', () => { const isActive = option.dataset.active === 'true'; option.dataset.active = !isActive }) });
    function onWindowResize() { if (plexusCamera && plexusRenderer) { const plexusContainer = document.querySelector('.network-canvas-container'); if(plexusContainer) {plexusCamera.aspect = plexusContainer.clientWidth / plexusContainer.clientHeight; plexusCamera.updateProjectionMatrix(); plexusRenderer.setSize(plexusContainer.clientWidth, plexusContainer.clientHeight)} } for (let i = 0; i < scoreCameras.length; i++) { if(scoreRenderers[i]) {const container = scoreRenderers[i].domElement.parentElement; if(container){scoreCameras[i].aspect = container.clientWidth / container.clientHeight; scoreCameras[i].updateProjectionMatrix(); scoreRenderers[i].setSize(container.clientWidth, container.clientHeight)}} } }; window.addEventListener('resize', onWindowResize, false);
    initScoreShapes();
    initPlexusAnimation();
    initPreloaderPlexus();
    animate();
    function startLoaderAnimation() { const texts = ["Activating Systems...", "Calibrating Nuance Engine...", "Loading Creative Matrix...", "Authenticating Voice Profiles..."]; let textIndex = 0; let charIndex = 0; const loaderTextEl = document.getElementById('loader-text'); if (!loaderTextEl) return; function type() { if (charIndex < texts[textIndex].length) { loaderTextEl.textContent += texts[textIndex].charAt(charIndex); charIndex++; setTimeout(type, 50); } else { setTimeout(erase, 1500); } } function erase() { if (charIndex > 0) { loaderTextEl.textContent = texts[textIndex].substring(0, charIndex - 1); charIndex--; setTimeout(erase, 30); } else { textIndex = (textIndex + 1) % texts.length; setTimeout(type, 500); } } type(); }
    startLoaderAnimation();
});
window.onload = () => {
    const MIN_LOAD_TIME = 3500;
    const startTime = Date.now();
    const hideLoader = () => {
        const timeElapsed = Date.now() - startTime;
        const remainingTime = MIN_LOAD_TIME - timeElapsed;
        if (remainingTime <= 0) {
            const preloader = document.getElementById('preloader');
            const mainContainer = document.querySelector('.main-container');
            if (preloader) preloader.classList.add('hidden');
            if (mainContainer) mainContainer.style.visibility = 'visible';
        } else {
            setTimeout(hideLoader, remainingTime);
        }
    };
    hideLoader();
};