
document.addEventListener('DOMContentLoaded', () => {
    const audioPlayer = document.getElementById('audio-player');
    const videoPlayer = document.getElementById('video-player');
    const transcriptContainer = document.getElementById('transcript-container');
    const summaryContainer = document.getElementById('summary-container');
    const minutesContainer = document.getElementById('minutes-container');
    const meetingTitle = document.getElementById('meeting-title');

    let segments = [];
    let currentSegmentIndex = -1;
    let summaryGenerated = false; // 요약 생성 여부 추적
    let minutesGenerated = false; // 회의록 생성 여부 추적
    let currentPlayer = null; // 현재 사용 중인 플레이어 (비디오 또는 오디오)
    let participants = []; // 참석자 목록
    const speakerColors = ['#4A90E2', '#50C878', '#F39C12', '#9B59B6', '#E74C3C', '#1ABC9C', '#E91E63', '#FFC107']; // 화자 색상 팔레트
    let speakerShareData = null; // 화자별 점유율 데이터
    let chartInstance = null; // Chart.js 인스턴스
    let originalMeetingDate = ''; // 원본 회의 날짜 (DB 형식: "YYYY-MM-DD HH:MM:SS")

    // 탭 전환 기능
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            // 모든 탭 버튼과 컨텐츠에서 active 클래스 제거
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // 클릭한 탭 버튼과 해당 컨텐츠에 active 클래스 추가
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');

            // 회의록 탭을 클릭했을 때 회의록 조회
            if (targetTab === 'minutes' && !minutesGenerated) {
                checkAndDisplayMinutes();
            }
        });
    });

    // 데이터 가져오기 및 뷰어 설정
    async function initializeViewer() {
        if (typeof MEETING_ID === 'undefined' || !MEETING_ID) {
            showError('회의 ID를 찾을 수 없습니다.');
            return;
        }

        try {
            const response = await fetch(`/api/meeting/${MEETING_ID}`);
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || '데이터를 불러오는 데 실패했습니다.');
            }

            // 데이터로 뷰어 설정
            segments = data.transcript;
            meetingTitle.textContent = data.title;

            // 편집 권한이 있는 경우 연필 버튼 표시
            if (data.can_edit) {
                const editTitleBtn = document.getElementById('edit-title-btn');
                if (editTitleBtn) {
                    editTitleBtn.style.display = 'flex';
                }

                const editDateBtn = document.getElementById('edit-date-btn');
                if (editDateBtn) {
                    editDateBtn.style.display = 'flex';
                }
            }

            // 원본 회의 날짜 저장
            originalMeetingDate = data.meeting_date;

            // 파일 확장자 확인하여 비디오/오디오 플레이어 선택
            const audioUrl = data.audio_url;
            const fileExtension = audioUrl.split('.').pop().toLowerCase();

            if (fileExtension === 'mp4') {
                // 비디오 파일인 경우 비디오 플레이어 사용
                videoPlayer.src = audioUrl;
                videoPlayer.style.display = 'block';
                audioPlayer.style.display = 'none';
                currentPlayer = videoPlayer;
                console.log('🎬 비디오 플레이어 활성화');
            } else {
                // 오디오 파일인 경우 오디오 플레이어 사용
                audioPlayer.src = audioUrl;
                audioPlayer.style.display = 'block';
                videoPlayer.style.display = 'none';
                currentPlayer = audioPlayer;
                console.log('🎵 오디오 플레이어 활성화');
            }

            // 회의 날짜 표시
            displayMeetingDate(data.meeting_date);

            // 참석자 목록 저장 및 표시
            participants = data.participants || [];
            displayParticipants(participants);

            // 화자별 점유율 데이터 저장
            speakerShareData = data.speaker_share;

            renderTranscript(segments);

            // 문단 요약 존재 여부 확인 및 표시
            await checkAndDisplaySummary();

            // 회의록 존재 여부 확인 및 표시
            await checkAndDisplayMinutes();

        } catch (error) {
            showError(error.message);
        }
    }

    // 문단 요약 존재 여부 확인 및 자동 표시
    async function checkAndDisplaySummary() {
        try {
            const response = await fetch(`/api/check_summary/${MEETING_ID}`);
            const data = await response.json();

            if (data.success && data.has_summary) {
                // 문단 요약이 이미 존재하면 자동으로 표시
                displaySummary(data.summary);
                summaryGenerated = true;

                console.log('✅ 기존 문단 요약을 불러왔습니다.');
            } else {
                console.log('ℹ️ 문단 요약이 아직 생성되지 않았습니다.');
            }
        } catch (error) {
            console.error('문단 요약 조회 중 오류:', error);
            // 오류가 발생해도 계속 진행 (필수 기능 아님)
        }
    }

    // 회의록 존재 여부 확인 및 자동 표시
    async function checkAndDisplayMinutes() {
        try {
            const response = await fetch(`/api/get_minutes/${MEETING_ID}`);
            const data = await response.json();

            if (data.success && data.has_minutes) {
                // 회의록이 이미 존재하면 자동으로 표시
                displayMinutes(data.minutes);
                minutesGenerated = true;

                console.log('✅ 기존 회의록을 불러왔습니다.');
            } else {
                // 회의록이 없으면 생성 버튼 표시
                updateMinutesTab();
                console.log('ℹ️ 회의록이 아직 생성되지 않았습니다.');
            }
        } catch (error) {
            console.error('회의록 조회 중 오류:', error);
            // 오류가 발생해도 계속 진행 (필수 기능 아님)
        }
    }

    // 회의록 렌더링
    function renderTranscript(segments) {
        transcriptContainer.innerHTML = '';
        segments.forEach((segment, index) => {
            const segDiv = document.createElement('div');
            segDiv.className = 'segment-block';
            segDiv.dataset.startTime = segment.start_time;
            segDiv.dataset.index = index;

            const time = new Date(segment.start_time * 1000).toISOString().substr(14, 5);

            // speaker_label에 해당하는 색상 찾기
            const speakerIndex = participants.indexOf(segment.speaker_label);
            const speakerColor = speakerIndex >= 0 ? speakerColors[speakerIndex % speakerColors.length] : '#333';

            segDiv.innerHTML = `
                <div class="segment-block-header">
                    <span class="segment-speaker" style="color: ${speakerColor}; font-weight: bold;">Speaker ${segment.speaker_label}</span>
                    <span class="segment-time">${time}</span>
                </div>
                <p class="segment-block-text">${segment.segment}</p>
            `;

            // 클릭 시 해당 시간으로 이동 및 재생
            segDiv.addEventListener('click', () => {
                if (currentPlayer) {
                    currentPlayer.currentTime = segment.start_time;
                    currentPlayer.play();
                }
            });

            transcriptContainer.appendChild(segDiv);
        });
    }

    // 재생 시간에 맞춰 하이라이트 (오디오 & 비디오 공통)
    function setupPlayerTimeUpdate(player) {
        player.addEventListener('timeupdate', () => {
            const currentTime = player.currentTime;
            let newSegmentIndex = -1;

            for (let i = 0; i < segments.length; i++) {
                const segment = segments[i];
                const nextSegment = segments[i + 1];
                const startTime = segment.start_time;
                const endTime = nextSegment ? nextSegment.start_time : player.duration;

                if (currentTime >= startTime && currentTime < endTime) {
                    newSegmentIndex = i;
                    break;
                }
            }

            if (newSegmentIndex !== currentSegmentIndex) {
                currentSegmentIndex = newSegmentIndex;
                highlightSegment(currentSegmentIndex);
            }
        });
    }

    // 두 플레이어 모두에 이벤트 리스너 설정
    setupPlayerTimeUpdate(audioPlayer);
    setupPlayerTimeUpdate(videoPlayer);

    // 세그먼트 하이라이트 함수
    function highlightSegment(index) {
        const segmentBlocks = document.querySelectorAll('.segment-block');
        segmentBlocks.forEach((block, i) => {
            if (i === index) {
                block.classList.add('current');
                block.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                block.classList.remove('current');
            }
        });
    }

    // 오류 메시지 표시
    function showError(message) {
        transcriptContainer.innerHTML = `<p class="error-message">오류: ${message}</p>`;
    }

    initializeViewer();

    // 회의록 생성 버튼 이벤트 리스너 초기 연결
    attachMinutesButtonListener();

    // 요약 내용 표시 함수
    function displaySummary(summaryText) {
        // 마크다운 형식을 HTML로 변환
        // ### 제목 -> <h3>제목</h3>
        // * 항목 -> <li>항목</li>
        let htmlContent = summaryText
            .replace(/### (.+)/g, '<h3>$1</h3>')
            .replace(/^\* (.+)/gm, '<li>$1</li>');

        // <li> 태그들을 <ul>로 감싸기
        htmlContent = htmlContent.replace(/(<li>.*?<\/li>\s*)+/gs, match => {
            return `<ul>${match}</ul>`;
        });

        summaryContainer.innerHTML = `<div class="summary-content">${htmlContent}</div>`;
    }

    // 회의록 탭 업데이트 함수
    function updateMinutesTab() {
        const generateMinutesButton = document.getElementById('generate-minutes-button');

        // 회의록 생성 버튼 항상 표시 (청킹된 문서 기반으로 생성)
        minutesContainer.innerHTML = `
            <p class="minutes-placeholder">회의록 생성 버튼을 눌러 정식 회의록을 작성하세요.</p>
            <button id="generate-minutes-button" class="btn-primary" style="margin-top: 1rem;">회의록 생성</button>
        `;

        // 버튼 이벤트 리스너 다시 추가
        attachMinutesButtonListener();
    }

    // 회의록 생성 버튼 이벤트 리스너
    function attachMinutesButtonListener() {
        const generateMinutesButton = document.getElementById('generate-minutes-button');

        if (generateMinutesButton) {
            generateMinutesButton.addEventListener('click', async () => {
                if (typeof MEETING_ID === 'undefined' || !MEETING_ID) {
                    alert('회의 ID를 찾을 수 없습니다.');
                    return;
                }

                if (!confirm('회의록을 생성하시겠습니까? 생성에는 시간이 소요될 수 있습니다.')) {
                    return;
                }

                try {
                    // 버튼 비활성화 및 로딩 표시
                    generateMinutesButton.disabled = true;
                    generateMinutesButton.textContent = '회의록 생성 중...';

                    // 회의록 컨테이너에 로딩 메시지 표시
                    minutesContainer.innerHTML = '<div class="minutes-loading">회의록을 생성하는 중입니다. 잠시만 기다려주세요...</div>';

                    const response = await fetch(`/api/generate_minutes/${MEETING_ID}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });

                    const data = await response.json();

                    if (data.success) {
                        // 회의록 내용을 마크다운에서 HTML로 변환하여 표시
                        displayMinutes(data.minutes);
                        minutesGenerated = true; // 회의록 생성 완료 표시
                        alert('회의록이 성공적으로 생성 및 저장되었습니다!');
                    } else {
                        minutesContainer.innerHTML = `<div class="minutes-error">회의록 생성 실패: ${data.error}</div>`;
                        // 버튼 다시 표시
                        updateMinutesTab();
                        alert(`회의록 생성 실패: ${data.error}`);
                    }
                } catch (error) {
                    console.error('회의록 생성 중 오류 발생:', error);
                    minutesContainer.innerHTML = '<div class="minutes-error">회의록 생성 중 오류가 발생했습니다.</div>';
                    // 버튼 다시 표시
                    updateMinutesTab();
                    alert('회의록 생성 중 오류가 발생했습니다.');
                }
            });
        }
    }

    // 회의 날짜 표시 함수
    function displayMeetingDate(meetingDate) {
        const dateDisplay = document.getElementById('meeting-date-display');
        if (!dateDisplay || !meetingDate) return;

        // "2025-01-05 14:30:00" 형식을 "2025년 1월 5일 오후 2:30" 형식으로 변환
        try {
            const date = new Date(meetingDate);
            const formattedDate = date.toLocaleString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            dateDisplay.textContent = formattedDate;
        } catch (error) {
            console.error('날짜 포맷 오류:', error);
            dateDisplay.textContent = meetingDate; // 변환 실패 시 원본 표시
        }
    }

    // 참석자 목록 표시 함수
    function displayParticipants(participants) {
        const participantsList = document.getElementById('participants-list');
        if (!participantsList) return;

        // 참석자가 없으면 기본 메시지 표시
        if (!participants || participants.length === 0) {
            participantsList.innerHTML = '<span class="no-participants">참석자 정보 없음</span>';
            return;
        }

        // 참석자 아이콘들 생성
        participantsList.innerHTML = participants.map((speaker, index) => {
            // 배경색을 speaker별로 다르게 설정 (전역 색상 팔레트 사용)
            const color = speakerColors[index % speakerColors.length];

            return `
                <div class="participant-icon" style="background-color: ${color}" title="화자 ${speaker}">
                    <span>${speaker}</span>
                </div>
            `;
        }).join('');
    }

    // 회의록 내용 표시 함수
    function displayMinutes(minutesText) {
        // minutes-empty 클래스 제거 (회의록이 있으므로)
        minutesContainer.classList.remove('minutes-empty');

        // 마크다운 형식을 HTML로 변환
        let htmlContent = minutesText
            // # 제목 -> <h1>제목</h1>
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            // ## 제목 -> <h2>제목</h2>
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            // ### 제목 -> <h3>제목</h3>
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            // **굵게** -> <strong>굵게</strong>
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            // 일반 텍스트를 <p>로 감싸기 (태그가 없는 줄)
            .replace(/^(?!<[h123]|<strong|<hr|$)(.+)$/gm, '<p>$1</p>')
            // --- -> <hr>
            .replace(/^---$/gm, '<hr>');

        minutesContainer.innerHTML = `<div class="minutes-content">${htmlContent}</div>`;

        // 회의록이 표시되면 복사 버튼 표시
        const copyMinutesBtn = document.getElementById('copy-minutes-btn');
        if (copyMinutesBtn) {
            copyMinutesBtn.style.display = 'flex';
        }
    }

    // === 화자별 점유율 모달 관련 로직 ===
    const speakerShareBtn = document.getElementById('speaker-share-btn');
    const speakerShareModal = document.getElementById('speaker-share-modal');
    const closeShareModal = document.getElementById('close-share-modal');

    // 모달 열기
    if (speakerShareBtn) {
        speakerShareBtn.addEventListener('click', () => {
            if (!speakerShareData || !speakerShareData.labels || speakerShareData.labels.length === 0) {
                alert('점유율 데이터를 불러올 수 없습니다.');
                return;
            }
            speakerShareModal.style.display = 'flex';
            renderSpeakerChart(speakerShareData);
        });
    }

    // 모달 닫기 (X 버튼)
    if (closeShareModal) {
        closeShareModal.addEventListener('click', () => {
            speakerShareModal.style.display = 'none';
        });
    }

    // 모달 닫기 (배경 클릭)
    if (speakerShareModal) {
        speakerShareModal.addEventListener('click', (e) => {
            if (e.target === speakerShareModal) {
                speakerShareModal.style.display = 'none';
            }
        });
    }

    // 화자별 점유율 차트 렌더링
    function renderSpeakerChart(shareData) {
        const ctx = document.getElementById('speakerShareChart');
        if (!ctx) return;

        // 기존 차트가 있으면 삭제
        if (chartInstance) {
            chartInstance.destroy();
        }

        // 화자별 색상 매칭 (participants 순서대로)
        const chartColors = shareData.labels.map(label => {
            const index = participants.indexOf(label);
            return index >= 0 ? speakerColors[index % speakerColors.length] : '#999';
        });

        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: shareData.labels,
                datasets: [{
                    label: '대화 점유율 (%)',
                    data: shareData.data,
                    backgroundColor: chartColors.map(color => color + '40'), // 투명도 추가
                    borderColor: chartColors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    // ======================================
    // 제목 편집 기능
    // ======================================

    const editTitleBtn = document.getElementById('edit-title-btn');
    const titleEditMode = document.getElementById('title-edit-mode');
    const titleInput = document.getElementById('title-input');
    const saveTitleBtn = document.getElementById('save-title-btn');
    const cancelTitleBtn = document.getElementById('cancel-title-btn');
    const titleEditContainer = document.querySelector('.title-edit-container');

    let originalTitle = '';

    // 편집 모드 활성화
    function enableTitleEdit() {
        originalTitle = meetingTitle.textContent;
        titleInput.value = originalTitle;

        // 제목 컨테이너 숨기고 편집 모드 표시
        titleEditContainer.style.display = 'none';
        titleEditMode.style.display = 'flex';

        // 입력 필드에 포커스
        titleInput.focus();
        titleInput.select();
    }

    // 편집 모드 취소
    function cancelTitleEdit() {
        // 편집 모드 숨기고 제목 컨테이너 표시
        titleEditMode.style.display = 'none';
        titleEditContainer.style.display = 'flex';

        // 입력 필드 초기화
        titleInput.value = '';
    }

    // 제목 저장
    async function saveTitleEdit() {
        const newTitle = titleInput.value.trim();

        // 제목 validation
        if (!newTitle) {
            alert('제목을 입력해주세요.');
            titleInput.focus();
            return;
        }

        if (newTitle.length > 100) {
            alert('제목은 100자 이하로 입력해주세요.');
            titleInput.focus();
            return;
        }

        // 변경사항이 없는 경우
        if (newTitle === originalTitle) {
            cancelTitleEdit();
            return;
        }

        // 저장 버튼 비활성화 (중복 클릭 방지)
        saveTitleBtn.disabled = true;
        saveTitleBtn.textContent = '저장 중...';

        try {
            const response = await fetch(`/api/update_title/${MEETING_ID}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: newTitle })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || '제목 수정에 실패했습니다.');
            }

            // 성공: 화면의 제목 업데이트
            meetingTitle.textContent = newTitle;

            // 편집 모드 종료
            cancelTitleEdit();

            // 성공 메시지
            console.log('✅ 제목 수정 완료:', newTitle);
            alert('제목이 성공적으로 수정되었습니다.');

        } catch (error) {
            console.error('❌ 제목 수정 실패:', error);
            alert(`제목 수정 중 오류가 발생했습니다:\n${error.message}`);
        } finally {
            // 버튼 복원
            saveTitleBtn.disabled = false;
            saveTitleBtn.textContent = '저장';
        }
    }

    // 이벤트 리스너 등록
    if (editTitleBtn) {
        editTitleBtn.addEventListener('click', enableTitleEdit);
    }

    if (saveTitleBtn) {
        saveTitleBtn.addEventListener('click', saveTitleEdit);
    }

    if (cancelTitleBtn) {
        cancelTitleBtn.addEventListener('click', cancelTitleEdit);
    }

    // Enter 키로 저장, Esc 키로 취소
    if (titleInput) {
        titleInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveTitleEdit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelTitleEdit();
            }
        });
    }

    // ======================================
    // 날짜 편집 기능
    // ======================================

    const editDateBtn = document.getElementById('edit-date-btn');
    const dateEditMode = document.getElementById('date-edit-mode');
    const dateInput = document.getElementById('date-input');
    const saveDateBtn = document.getElementById('save-date-btn');
    const cancelDateBtn = document.getElementById('cancel-date-btn');
    const dateEditContainer = document.querySelector('.date-edit-container');
    const meetingDateDisplay = document.getElementById('meeting-date-display');

    /**
     * DB 형식 날짜를 datetime-local 형식으로 변환
     * @param {string} dbDate - "YYYY-MM-DD HH:MM:SS" 형식
     * @returns {string} - "YYYY-MM-DDTHH:MM" 형식
     */
    function dbDateToInputFormat(dbDate) {
        if (!dbDate) return '';

        try {
            // "YYYY-MM-DD HH:MM:SS" -> "YYYY-MM-DDTHH:MM"
            const parts = dbDate.split(' ');
            if (parts.length !== 2) return '';

            const datePart = parts[0]; // "YYYY-MM-DD"
            const timePart = parts[1].substring(0, 5); // "HH:MM" (초 제거)

            return `${datePart}T${timePart}`;
        } catch (error) {
            console.error('날짜 형식 변환 오류:', error);
            return '';
        }
    }

    /**
     * datetime-local 형식을 DB 형식으로 변환
     * @param {string} inputDate - "YYYY-MM-DDTHH:MM" 형식
     * @returns {string} - "YYYY-MM-DD HH:MM:SS" 형식
     */
    function inputDateToDbFormat(inputDate) {
        if (!inputDate) return '';

        try {
            // "YYYY-MM-DDTHH:MM" -> "YYYY-MM-DD HH:MM:SS"
            const parts = inputDate.split('T');
            if (parts.length !== 2) return '';

            const datePart = parts[0]; // "YYYY-MM-DD"
            const timePart = parts[1]; // "HH:MM"

            return `${datePart} ${timePart}:00`;
        } catch (error) {
            console.error('날짜 형식 변환 오류:', error);
            return '';
        }
    }

    // 편집 모드 활성화
    function enableDateEdit() {
        // 입력 필드에 현재 날짜 설정 (datetime-local 형식으로 변환)
        const inputFormat = dbDateToInputFormat(originalMeetingDate);
        dateInput.value = inputFormat;

        // 날짜 컨테이너 숨기고 편집 모드 표시
        dateEditContainer.style.display = 'none';
        dateEditMode.style.display = 'flex';

        // 입력 필드에 포커스
        dateInput.focus();
    }

    // 편집 모드 취소
    function cancelDateEdit() {
        // 편집 모드 숨기고 날짜 컨테이너 표시
        dateEditMode.style.display = 'none';
        dateEditContainer.style.display = 'flex';

        // 입력 필드 초기화
        dateInput.value = '';
    }

    // 날짜 저장
    async function saveDateEdit() {
        const newDateInput = dateInput.value.trim();

        // 날짜 validation
        if (!newDateInput) {
            alert('날짜를 입력해주세요.');
            dateInput.focus();
            return;
        }

        // DB 형식으로 변환
        const newDateDb = inputDateToDbFormat(newDateInput);

        // 변경사항이 없는 경우
        if (newDateDb === originalMeetingDate) {
            cancelDateEdit();
            return;
        }

        // 저장 버튼 비활성화 (중복 클릭 방지)
        saveDateBtn.disabled = true;
        saveDateBtn.textContent = '저장 중...';

        try {
            const response = await fetch(`/api/update_date/${MEETING_ID}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ date: newDateInput })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || '날짜 수정에 실패했습니다.');
            }

            // 성공: 날짜 업데이트
            originalMeetingDate = data.new_date;

            // 화면에 표시되는 날짜 업데이트 (한국어 형식 - 시간 포함)
            try {
                const date = new Date(data.new_date);
                const formattedDate = date.toLocaleString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                meetingDateDisplay.textContent = formattedDate;
            } catch (error) {
                console.error('날짜 포맷 오류:', error);
                meetingDateDisplay.textContent = data.new_date;
            }

            // 편집 모드 종료
            cancelDateEdit();

            // 성공 메시지
            console.log('✅ 날짜 수정 완료:', data.new_date);
            alert('날짜가 성공적으로 수정되었습니다.');

        } catch (error) {
            console.error('❌ 날짜 수정 실패:', error);
            alert(`날짜 수정 중 오류가 발생했습니다:\n${error.message}`);
        } finally {
            // 버튼 복원
            saveDateBtn.disabled = false;
            saveDateBtn.textContent = '저장';
        }
    }

    // 이벤트 리스너 등록
    if (editDateBtn) {
        editDateBtn.addEventListener('click', enableDateEdit);
    }

    if (saveDateBtn) {
        saveDateBtn.addEventListener('click', saveDateEdit);
    }

    if (cancelDateBtn) {
        cancelDateBtn.addEventListener('click', cancelDateEdit);
    }

    // Enter 키로 저장, Esc 키로 취소
    if (dateInput) {
        dateInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveDateEdit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelDateEdit();
            }
        });
    }

    // ==================== 복사 기능 ====================

    const copySummaryBtn = document.getElementById('copy-summary-btn');
    const copyMinutesBtn = document.getElementById('copy-minutes-btn');

    // 문단 요약 복사
    if (copySummaryBtn) {
        copySummaryBtn.addEventListener('click', async () => {
            const summaryContainer = document.getElementById('summary-container');
            const text = extractTextFromContainer(summaryContainer);

            if (!text || text.trim() === '') {
                alert('복사할 내용이 없습니다.');
                return;
            }

            await copyToClipboard(text, copySummaryBtn);
        });
    }

    // 회의록 복사
    if (copyMinutesBtn) {
        copyMinutesBtn.addEventListener('click', async () => {
            const minutesContainer = document.getElementById('minutes-container');
            const text = extractTextFromContainer(minutesContainer);

            if (!text || text.trim() === '') {
                alert('복사할 내용이 없습니다.');
                return;
            }

            await copyToClipboard(text, copyMinutesBtn);
        });
    }

    // 컨테이너에서 텍스트 추출 함수
    function extractTextFromContainer(container) {
        // 플레이스홀더 텍스트 제외
        const clone = container.cloneNode(true);

        // 버튼 요소 제거
        const buttons = clone.querySelectorAll('button');
        buttons.forEach(btn => btn.remove());

        // 플레이스홀더 제거
        const placeholders = clone.querySelectorAll('.summary-placeholder, .minutes-placeholder');
        placeholders.forEach(p => p.remove());

        return clone.innerText.trim();
    }

    // 클립보드 복사 함수
    async function copyToClipboard(text, button) {
        try {
            await navigator.clipboard.writeText(text);

            // 성공 애니메이션
            button.classList.add('copied');

            setTimeout(() => {
                button.classList.remove('copied');
            }, 2000);

            console.log('✅ 클립보드에 복사되었습니다.');
        } catch (error) {
            console.error('❌ 복사 실패:', error);

            // 폴백: 구형 브라우저용
            try {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);

                // 성공 애니메이션
                button.classList.add('copied');
                setTimeout(() => {
                    button.classList.remove('copied');
                }, 2000);

                console.log('✅ 클립보드에 복사되었습니다 (폴백 방식).');
            } catch (fallbackError) {
                console.error('❌ 폴백 복사도 실패:', fallbackError);
                alert('복사에 실패했습니다. 브라우저가 클립보드 접근을 차단했을 수 있습니다.');
            }
        }
    }
});
