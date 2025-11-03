
document.addEventListener('DOMContentLoaded', () => {
    const audioPlayer = document.getElementById('audio-player');
    const transcriptContainer = document.getElementById('transcript-container');
    const meetingTitle = document.getElementById('meeting-title');

    let segments = [];
    let currentSegmentIndex = -1;

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
            audioPlayer.src = data.audio_url;

            renderTranscript(segments);

        } catch (error) {
            showError(error.message);
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

            segDiv.innerHTML = `
                <div class="segment-block-header">
                    <span class="segment-speaker">Speaker ${segment.speaker_label}</span>
                    <span class="segment-time">${time}</span>
                </div>
                <p class="segment-block-text">${segment.segment}</p>
            `;

            // 클릭 시 해당 시간으로 이동 및 재생
            segDiv.addEventListener('click', () => {
                audioPlayer.currentTime = segment.start_time;
                audioPlayer.play();
            });

            transcriptContainer.appendChild(segDiv);
        });
    }

    // 오디오 재생에 맞춰 하이라이트
    audioPlayer.addEventListener('timeupdate', () => {
        const currentTime = audioPlayer.currentTime;
        let newSegmentIndex = -1;

        for (let i = 0; i < segments.length; i++) {
            const segment = segments[i];
            const nextSegment = segments[i + 1];
            const startTime = segment.start_time;
            const endTime = nextSegment ? nextSegment.start_time : audioPlayer.duration;

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

    // 요약하기 버튼 이벤트 리스너
    const summarizeButton = document.getElementById('summarize-button');
    if (summarizeButton) {
        summarizeButton.addEventListener('click', async () => {
            if (typeof MEETING_ID === 'undefined' || !MEETING_ID) {
                alert('회의 ID를 찾을 수 없습니다.');
                return;
            }

            if (!confirm('회의 내용을 요약하시겠습니까? 요약에는 시간이 소요될 수 있습니다.')) {
                return;
            }

            try {
                // 버튼 비활성화 및 로딩 표시
                summarizeButton.disabled = true;
                summarizeButton.textContent = '요약 중...';

                const response = await fetch(`/api/summarize/${MEETING_ID}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    // body: JSON.stringify({}) // POST 요청이지만, 현재는 body에 보낼 데이터 없음
                });

                const data = await response.json();

                if (data.success) {
                    alert('요약이 성공적으로 생성 및 저장되었습니다!');
                    // 필요하다면 요약된 내용을 화면에 표시하거나 다른 액션 수행
                    console.log('Summary:', data.summary);
                } else {
                    alert(`요약 실패: ${data.error}`);
                }
            } catch (error) {
                console.error('요약 요청 중 오류 발생:', error);
                alert('요약 요청 중 오류가 발생했습니다.');
            } finally {
                // 버튼 다시 활성화
                summarizeButton.disabled = false;
                summarizeButton.textContent = '요약하기';
            }
        });
    }
});
