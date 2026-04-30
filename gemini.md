## 프로젝트 구조

- /camping-scanner/.venv # 가상환경
- /camping-scanner/app # 소스 경로
- /camping-scanner/app/main.py # FastAPI 엔트리 포인트 (Server 기동)
- /camping-scanner/app/core/ # 핵심 공통 로직
- /camping-scanner/app/core/config_loader.py # YAML 설정 로드
- /camping-scanner/app/core/logger.py # 로그 핸들러
- /camping-scanner/app/core/notifier.py # 텔레그램 알림 발송
- /camping-scanner/app/core/scheduler.py # APScheduler 설정 및 시작
- /camping-scanner/app/core/termination_handler.py # 감시 종료 및 UI 제거 로직
- /camping-scanner/app/core/websocket_manager.py # 웹소켓 연결 관리
- /camping-scanner/app/core/ua_generator.py # User-Agent 정보를 관리하고 무작위로 반환해 줄 유틸리티
- /camping-scanner/app/core/tray_icon.py # 트래이 아이콘
- /camping-scanner/app/platforms # 사이트별 크롤링 모듈 (전략 패턴)
- /camping-scanner/app/platforms/base.py # 추상 베이스 클래스
- /camping-scanner/app/platforms/interpark.py # 인터파크 크롤링 로직
- /camping-scanner/app/platforms/thankq.py # 땡큐캠핑 크롤링 로직
- /camping-scanner/app/services # 비즈니스 로직 처리 (모니터링 서비스 등)
- /camping-scanner/app/services/monitor_service.py
- /camping-scanner/app/services/notification.py
- /camping-scanner/app/static # CSS, JS, Image 등 정적 파일
- /camping-scanner/app/static/css/style.css
- /camping-scanner/app/static/js/script.js # 프론트엔드 메인 로직
- /camping-scanner/app/templates # HTML 템플릿 (Jinja2)
- /camping-scanner/app/templates/index.html # 웹 초기 화면
- /camping-scanner/config # 배포시 외부에서 수정 가능한 설정 파일 경로
- /camping-scanner/config/config.yaml # 서버 포트, API 토큰 등 설정 (Git 제외 대상)
- /camping-scanner/data # 캠핑장 정보 XML 파일들
- /camping-scanner/data/thankqcamping-campsite.xml # 땡큐캠핑 목록 XML
- /camping-scanner/data/interpark-campsite.xml # 인터파크 목록 XML
- /camping-scanner/data/camfit-campsite.xml
- /camping-scanner/data/campingtalk-campsite.xml
- /camping-scanner/data/etc-campsite.xml
- /camping-scanner/data/forcamper-campsite.xml
- /camping-scanner/data/maketicket-campsite.xml
- /camping-scanner/data/mirihae-campsite.xml
- /camping-scanner/data/naver-campsite.xml
- /camping-scanner/data/xticket-campsite.xml
- /camping-scanner/logs # 로그 저장소
- /camping-scanner/.gitignore # Git 관리 예외 설정 파일
- /camping-scanner/.prettierignore
- /camping-scanner/.prettierrc
- /camping-scanner/build.py # 빌드 배포를 위한 파일
- /camping-scanner/README.md
- /camping-scanner/requirements.txt

## 1. 프로젝트 개요

- **언어 및 프레임워크:** python 3.14.0
- **목적:** 캠핑장 빈자리 알람 프로그램

## 2. 질문 사항

- [] ** findNextRun 기능 체크 박스 추가 :** 자동 예약 요청 요청 옆에 [검색 감시 종료] 라벨로 체크 박스를 두고 싶어, 기본 값은 N 값이야.

## 3. 분석 대상 코드

### [/camping-scanner/app/static/js/script.js]

```javascript
const resizer = document.getElementById("footer-resizer");
const footer = document.getElementById("main-footer");

let isResizing = false;

resizer.addEventListener("mousedown", (e) => {
    isResizing = true;
    // 드래그 중 텍스트 선택 방지
    document.body.style.userSelect = "none";
    resizer.classList.add("bg-indigo-500");
});

document.addEventListener("mousemove", (e) => {
    if (!isResizing) return;

    // 전체 화면 높이에서 마우스의 현재 Y좌표를 빼서 footer의 높이를 계산
    const newHeight = window.innerHeight - e.clientY;

    // 최소 높이(50px)와 최대 높이(화면의 80%) 제한
    if (newHeight > 50 && newHeight < window.innerHeight * 0.8) {
        footer.style.height = `${newHeight}px`;
    }
});

document.addEventListener("mouseup", () => {
    isResizing = false;
    document.body.style.userSelect = "auto";
    resizer.classList.remove("bg-indigo-500");
});

function toggleMenu() {
    document.getElementById("menuLayer").classList.toggle("hidden-layer");
    document.getElementById("overlay").classList.toggle("hidden");
}

async function confirmShutdown() {
    if (confirm("프로그램을 완전히 종료하시겠습니까?")) {
        try {
            const response = await fetch("/api/shutdown", { method: "POST" });
            const result = await response.json();

            if (result.status === "success") {
                document.body.innerHTML = `
                <div class="flex flex-col h-screen items-center justify-center bg-slate-900 text-white">
                    <i class="fa-solid fa-circle-check text-emerald-500 text-6xl mb-6"></i>
                    <h1 class="text-3xl font-black mb-2">SYSTEM SHUTDOWN</h1>
                    <p class="text-slate-400">프로그램이 안전하게 종료되었습니다. 이 창을 닫으셔도 됩니다.</p>
                </div>
              `;
                setTimeout(() => {
                    window.close();
                }, 2000);
            }
        } catch (error) {
            console.error("종료 요청 중 오류 발생:", error);
            alert("서버 통신 오류가 발생했습니다.");
        }
    }
}

const Comp = {
    currentCampsiteData: null,
    interparkStayOption: {}, //인터파크 박수 지정 옵션 값

    init: function () {
        this.initComponent();
        this.bindEvents();
        this.changeFlatform();
        this.changeFlatform();
    },

    bindEvents: function () {
        document.getElementById("platformSelect").addEventListener("change", this.changeFlatform);
        document.getElementById("watchBtn").addEventListener("click", this.watchCampsite);
        document.getElementById("stopWatchBtn").addEventListener("click", () => this.stopWatching()); //감시중지
        document.getElementById("homePageBtn").addEventListener("click", () => this.openHomePage()); //홈페이지 열기
        document.getElementById("watchDate").addEventListener("change", () => this.onChangeWatchDate()); //날짜 변경 체크(인터파크)
    },

    initComponent: function () {
        const dateInput = document.getElementById("watchDate");

        const today = moment().format("YYYY-MM-DD");
        const tomorrow = moment().add(1, "days").format("YYYY-MM-DD");
        dateInput.min = tomorrow;
        dateInput.value = tomorrow;
    },

    changeFlatform: async function () {
        const selectEl = document.getElementById("platformSelect");
        const listContainer = document.getElementById("campsiteList");
        const filename = selectEl.value; // 예: "camfit-campsite.xml"

        // 1. 선택된 옵션의 텍스트(플랫폼 이름) 가져오기
        const selectedPlatformName = selectEl.options[selectEl.selectedIndex].text;

        // 3. 기존 리스트 초기화
        listContainer.innerHTML = "";

        const _parent = this;
        try {
            // 1. API 호출 (Spring의 RestTemplate/WebClient 역할)
            const response = await fetch(`/api/campsites/${filename}`);
            if (!response.ok) throw new Error("네트워크 응답 에러");

            const xmlText = await response.text();

            // 2. XML 파싱 (Java의 XML Parser 역할)
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xmlText, "text/xml");

            // 3. 하위 목록 렌더링
            Comp.renderCampsiteList(xmlDoc);
        } catch (error) {
            console.error("데이터 로드 중 오류 발생:", error);
            listContainer.innerHTML = '<li class="p-4 text-center text-red-500">데이터를 불러오지 못했습니다.</li>';
        }
    },

    renderCampsiteList: function (xmlDoc) {
        const listContainer = document.getElementById("campsiteList");
        listContainer.innerHTML = "";

        // <campsite> 노드들을 모두 가져옴
        const campsites = xmlDoc.getElementsByTagName("campsite");
        const type = xmlDoc.getElementsByTagName("type");
        const homepage = xmlDoc.getElementsByTagName("homepage");

        Array.from(campsites).forEach((site, index) => {
            // <name> 태그 값 추출 (CDATA가 포함되어 있어도 textContent로 해결)

            const nameNode = site.getElementsByTagName("name")[0];
            const name = nameNode ? nameNode.textContent : "이름 없음";

            // 하위 <site> 노드들(구역 정보) 추출[cite: 1]
            const siteNodes = site.getElementsByTagName("site");
            const sitesSummary = Array.from(siteNodes)
                .map((s) => s.textContent)
                .join(", ");

            //사이트 플랫폼 정보 추가
            const typeElement = xmlDoc.createElement("type");
            typeElement.textContent = type[0].textContent;
            site.appendChild(typeElement);

            //홈페이지 정보 추가

            if (homepage.length > 0) {
                const homepageElement = xmlDoc.createElement("homepage");
                homepageElement.textContent = homepage[0].textContent;
                site.appendChild(homepageElement);
            }

            const li = document.createElement("li");
            li.className = "p-3 hover:bg-indigo-50 cursor-pointer border-b border-slate-100 transition";
            li.innerHTML = `
                <div class="flex flex-col">
                  <span class="font-bold text-slate-800">${index + 1}. ${name}</span>
                </div>
              `;

            // 캠핑장 클릭 이벤트: 상세 정보 표시 로직으로 연결
            li.onclick = () => {
                this.highlightSelection(li);
                this.updateDetailPanel(site); // 상세 정보 렌더링 함수(별도 구현) 호출
            };

            listContainer.appendChild(li);

            if (index == 0) {
                this.highlightSelection(li);
                this.updateDetailPanel(site);
            }
        });
    },

    highlightSelection: function (element) {
        document.querySelectorAll("#campsiteList li").forEach((el) => el.classList.remove("bg-indigo-100"));
        element.classList.add("bg-indigo-100");
    },
    //예약정보 판넬 업데이트
    updateDetailPanel: function (site) {
        this.currentCampsiteData = site;

        const detailPanel = document.getElementById("detailPanel");
        const name = site.getElementsByTagName("name")[0]?.textContent || "이름 없음";
        const sites = Array.from(site.getElementsByTagName("site"))
            .map((s) => s.textContent)
            .join(", ");
        const type = site.getElementsByTagName("type")[0]?.textContent || "정보 없음";

        document.getElementById("campsiteName").textContent = site.getElementsByTagName("name")[0]?.textContent || "";
        document.getElementById("platformName").textContent = site.getElementsByTagName("type")[0]?.textContent || "";
        //campsiteName

        this.generatorMaxDayOption(site);
        this.generatorSiteChecker(site);
    },
    onChangeWatchDate: function (e) {
        const type = Comp.currentCampsiteData.getElementsByTagName("type")[0]?.textContent;
        if (type === "Interpark") {
            //인터파크일 경우만 처리
            const goodsCode = Comp.currentCampsiteData.getElementsByTagName("code")[0]?.textContent;
            const selectedDate = document.getElementById("watchDate").value;
            const start_date = moment(selectedDate).format("YYYYMMDD");
            Comp.generatorInterparkDayOption(start_date, Comp.interparkStayOption[goodsCode]);
        }
    },
    //사이트 최대 박수 지정
    generatorMaxDayOption: function (site) {
        const dayCountSelect = document.getElementById("dayCountSelect");
        dayCountSelect.innerHTML = "";

        const type = site.getElementsByTagName("type")[0]?.textContent || "";
        if (type === "Interpark") {
            //인터파크일 경우 요청 값이 다름
            const goodsCode = site.getElementsByTagName("code")[0]?.textContent; //최대 예약 박수
            const watchDate = document.getElementById("watchDate").value;
            const start_date = moment(watchDate).format("YYYYMMDD");
            if (goodsCode in Comp.interparkStayOption) {
                Comp.generatorInterparkDayOption(start_date, Comp.interparkStayOption[goodsCode]);
            } else {
                const end_date = moment(watchDate).add(2, "months").format("YYYYMMDD");
                Comp.fetchInterParkStayDayOption(goodsCode, start_date, end_date);
            }
        } else {
            const maxStayDay = site.getElementsByTagName("maxStayDay")[0]?.textContent || 2; //최대 예약 박수
            for (let i = 0; i < maxStayDay; i++) {
                const option = document.createElement("option");
                option.value = `${i + 1}`;
                option.textContent = `${i + 1}박`;
                dayCountSelect.appendChild(option);
            }
        }
    },
    //인터파크 박수 옵션 체크
    generatorInterparkDayOption: function (playDay, data) {
        if (data) {
            const targetOption = data.find((item) => item.playDate === playDay);
            if (targetOption && targetOption.playSeqList) {
                const stayList = targetOption.playSeqList;
                const dayCountSelect = document.getElementById("dayCountSelect");
                dayCountSelect.innerHTML = "";
                stayList.forEach((stay) => {
                    const option = document.createElement("option");
                    option.value = `${stay.stayPlaySeq}`;
                    option.textContent = `${stay.stayDay}`;
                    dayCountSelect.appendChild(option);
                });
            }
        }
    },
    fetchInterParkStayDayOption: async function (goodsCode, start_date, end_date) {
        const url = `/api/interpark/play-seq?goodsCode=${goodsCode}&start_date=${start_date}&end_date=${end_date}`;
        try {
            const response = await fetch(url);
            const result = await response.json();

            if (result.common.message === "success") {
                if (result.data) {
                    Comp.interparkStayOption[goodsCode] = result.data;
                    Comp.generatorInterparkDayOption(start_date, Comp.interparkStayOption[goodsCode]);
                }
            } else {
                alert("데이터를 가져오는데 실패했습니다.");
            }
        } catch (error) {
            console.error("서버 통신 오류:", error);
        }
    },
    generatorSiteChecker: function (site) {
        const siteCheckerContainer = document.getElementById("siteCheckerContainer");
        const labelArea = document.querySelector("label.border-b"); // "사이트 :" 레이블 선택

        //전체 체크 박스 추가
        const oldAllCheck = document.getElementById("allCheckWrapper");
        if (oldAllCheck) oldAllCheck.remove();

        const allCheckWrapper = document.createElement("span");
        allCheckWrapper.id = "allCheckWrapper";
        allCheckWrapper.className = "ml-auto flex items-center text-[10px] font-normal cursor-pointer text-slate-500";
        allCheckWrapper.innerHTML = `
            <input type="checkbox" id="allCheck" class="mr-1 w-3 h-3 accent-indigo-600" checked />
            전체 선택
        `;

        // 레이블을 flex로 만들어 우측 끝으로 밀어넣기 위해 스타일 살짝 변경
        labelArea.classList.add("flex", "items-center", "justify-between");
        labelArea.appendChild(allCheckWrapper);

        //사이트 목록 추가
        siteCheckerContainer.innerHTML = "";
        const sites = site.getElementsByTagName("site");

        Array.from(sites).forEach((element, index) => {
            const code = element.getAttribute("code") || "";
            const name = element.textContent || "";

            const label = document.createElement("label");
            label.className = "flex items-center";
            label.innerHTML = `<input type="checkbox" checked class="site-item mr-2 accent-indigo-600" value="${code}" /> ${name}`;

            siteCheckerContainer.appendChild(label);
        });

        // 4. 이벤트 바인딩 호출
        this.bindAllCheckEvent();
    },
    //예약 감시 수행
    watchCampsite: async function () {
        const parent = Comp;
        const currentCampsite = Comp.currentCampsiteData;

        const watchDate = document.getElementById("watchDate").value;
        const stayDay = document.getElementById("dayCountSelect").value;

        const type = currentCampsite.getElementsByTagName("type")[0]?.textContent;
        const campId = currentCampsite.getElementsByTagName("code")[0]?.textContent;

        const requestInterval = document.getElementById("requestInterval").value;
        const campsiteName = currentCampsite.getElementsByTagName("name")[0]?.textContent;

        const watchUuid = `${type}_${campId}_${watchDate}_${stayDay}`;

        if (parent.checkExistingMonitoring(watchUuid)) {
            alert("이미 동일한 감시 항목이 존재합니다.");
            return;
        }

        const selectedSites = Array.from(document.querySelectorAll(".site-item:checked")).map((cb) => cb.value);

        if (selectedSites.length === 0) {
            alert("최소 하나 이상의 사이트를 선택해주세요.");
            return;
        }

        const requestData = {
            type: type, // "THANKQ"
            campsiteName: campsiteName, // "THANKQ"
            camp_id: campId, // "3446"
            date: watchDate, // "2026-04-28"
            stay_day: stayDay, // 1
            findNextRun: "N",
            requestInterval: requestInterval, // 1
            watchUuid: watchUuid, // UUID for tracking the monitoring session
            // 체크박스에서 선택된 구역 코드들을 배열(List)로 수집
            site_codes: Array.from(document.querySelectorAll("#siteCheckerContainer input:checked")).map((cb) => cb.value)
        };

        try {
            // 2. FastAPI 엔드포인트로 POST 요청 전송
            const response = await fetch("/api/monitor/start", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestData) // JSON 문자열로 직렬화
            });

            const result = await response.json();
            if (response.ok) {
                //alert(`${requestData.type} 감시가 시작되었습니다!`);
                Logger.addLog(`${requestData.type} 감시가 시작되었습니다!`);
                parent.addMonitoringEntry(requestData); // 모니터링 항목 추가 함수 호출
            }
        } catch (error) {
            console.error("요청 실패:", error);
        }
    },
    //동일한 감시 항목 존재 유무 체크
    checkExistingMonitoring: function (watchUuid) {
        const monitoringList = document.getElementById("monitoring-list");
        return Array.from(monitoringList.children).some((tr) => tr.dataset.watchUuid === watchUuid);
    },
    //모니터링 항목 추가
    addMonitoringEntry: function (entry) {
        const monitoringList = document.getElementById("monitoring-list");

        const emptyRow = document.querySelector("#monitoring-list .EMPTY-ROW");
        if (emptyRow) {
            emptyRow.remove();
        }

        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-50";
        tr.innerHTML = `
            <td class="p-2 border-r font-bold">${entry.campsiteName}</td>
            <td class="p-2 border-r text-center">${entry.date}</td>
            <td class="p-2 border-r text-center">${entry.stay_day}</td>
            <td class="p-2 border-r text-center font-bold text-indigo-600 MNT-COUNT">0</td>
            <td class="p-2 text-center text-green-600 font-bold italic">Monitoring..</td>
        `;
        tr.dataset.watchuuid = entry.watchUuid;
        tr.dataset.reqcnt = 0; //모니터링 카운트

        // [추가] 테이블 행 클릭 시 선택 처리
        tr.onclick = () => {
            this.highlightMonitoringRow(tr);
            this.selectedMonitoringUuid = entry.watchUuid;
        };

        monitoringList.appendChild(tr);
    },
    // [추가] 감시 목록 행 하이라이트
    highlightMonitoringRow: function (element) {
        document.querySelectorAll("#monitoring-list tr").forEach((el) => el.classList.remove("bg-red-50"));
        element.classList.add("bg-red-50"); // 선택된 행은 붉은색 계열로 표시
    },

    // [추가] 감지 중지 로직 수행
    stopWatching: async function () {
        if (!this.selectedMonitoringUuid) {
            alert("중지할 감시 항목을 목록에서 선택해주세요.");
            return;
        }

        if (confirm("해당 감시 작업을 중지하시겠습니까?")) {
            try {
                // 백엔드 FastAPI에 중지 요청 (Java의 DELETE/POST 요청과 유사)
                const response = await fetch(`/api/monitor/stop/${this.selectedMonitoringUuid}`, {
                    method: "POST"
                });

                if (response.ok) {
                    // 화면에서 해당 행 삭제
                    const row = document.querySelector(`tr[data-watchuuid="${this.selectedMonitoringUuid}"]`);
                    if (row) row.remove();

                    // 목록이 비었으면 다시 EMPTY-ROW 추가
                    const monitoringList = document.getElementById("monitoring-list");
                    if (monitoringList.children.length === 0) {
                        monitoringList.innerHTML = `
                            <tr class="hover:bg-slate-50 EMPTY-ROW">
                                <td class="p-2 text-center text-green-600 font-bold italic" colspan="5">감시 중인 항목이 없습니다.</td>
                            </tr>`;
                    }

                    this.selectedMonitoringUuid = null;
                    Logger.addLog("감시가 중지되었습니다.");
                    //alert("감시가 중지되었습니다.");
                }
            } catch (error) {
                console.error("중지 요청 실패:", error);
            }
        }
    },

    bindAllCheckEvent: function () {
        const allCheck = document.getElementById("allCheck");

        allCheck.addEventListener("change", function () {
            // 모든 .site-item 체크박스를 전체 선택 상태와 동기화
            const siteChecks = document.querySelectorAll(".site-item");
            siteChecks.forEach((cb) => (cb.checked = allCheck.checked));
        });

        // 개별 항목 클릭 시 전체 선택 상태 업데이트 (Event Delegation 방식 권장)
        document.getElementById("siteCheckerContainer").addEventListener("change", function (e) {
            if (e.target.classList.contains("site-item")) {
                const allItems = document.querySelectorAll(".site-item");
                const checkedItems = document.querySelectorAll(".site-item:checked");

                // 모든 항목이 체크되어 있을 때만 "전체 선택"도 체크
                allCheck.checked = allItems.length === checkedItems.length;
            }
        });
    },
    //홈페이지 열기
    openHomePage: function () {
        const homepageUrl = this.currentCampsiteData.getElementsByTagName("homepage")[0]?.textContent;
        const campId = this.currentCampsiteData.getElementsByTagName("code")[0]?.textContent;
        window.open(`${homepageUrl}${campId}`, "_blank");
    },
    //감시 모니터링 증가
    changeMonitoringCount: function (data) {
        if (data) {
            const uuid = data.uuid || "";
            const row = document.querySelector(`tr[data-watchuuid="${uuid}"]`);

            // debugger;

            if (row) {
                let currentCount = row.dataset.reqcnt;
                let numericCount = parseInt(currentCount || 0, 10) + 1;
                row.dataset.reqcnt = numericCount;
                const countCell = row.querySelector("td.MNT-COUNT");
                if (countCell) {
                    countCell.innerText = numericCount;
                    countCell.classList.add("text-indigo-600", "font-bold");
                }
            }
        }
    }
};

const Alert = {
    retryCount: 0,

    init: function () {
        this.connect();
    },

    connect: function () {
        const socket = new WebSocket(`ws://${window.location.host}/ws/alerts`);

        socket.onopen = () => {
            console.log("알람 서버와 실시간 연결 성공");
            this.retryCount = 0; // 연결 성공 시 재시도 횟수 초기화
        };

        socket.onclose = () => {
            this.retryCount++;
            const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000); // 최대 30초 대기
            console.warn(`연결 끊김. ${delay / 1000}초 후 재연결 시도... (횟수: ${this.retryCount})`);
            setTimeout(() => this.connect(), delay);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.messageType) {
                case "alert":
                    Alert.showToast(data.data); // 알림 표시
                    break;

                case "monitor":
                    Comp.changeMonitoringCount(data.data);
                    break;

                case "remove_monitor":
                    const uuid = data.data.uuid;
                    const row = document.querySelector(`tr[data-watchuuid="${uuid}"]`);

                    if (row) {
                        // 부드럽게 사라지는 효과
                        row.style.transition = "all 0.5s";
                        row.style.backgroundColor = "#fee2e2"; // 살짝 붉은색으로 변함
                        row.style.opacity = "0";

                        setTimeout(() => {
                            row.remove(); // DOM에서 삭제
                            console.log(`감시 종료된 행 제거 완료: ${uuid}`);
                        }, 500);
                    }
                    break;
            }
        };
    },
    showToast: function (msg) {
        //alert("알림:" + msg);
        Toast.showToast(msg);
    }
};

const Logger = {
    MAX_LOG_COUNT: 100,
    retryCount: 0,

    init: function () {
        this.connect();
    },

    connect: function () {
        const ws = new WebSocket(`ws://${window.location.host}/ws/logs`);

        ws.onopen = () => {
            console.log("서버와 실시간 연결 성공");
            this.retryCount = 0; // 연결 성공 시 재시도 횟수 초기화
            this.addLog("--- 시스템 실시간 감시 연결됨 ---", "system");
        };

        ws.onmessage = (event) => {
            this.addLog(event.data);
        };

        ws.onclose = () => {
            this.retryCount++;
            const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000); // 최대 30초 대기
            console.warn(`연결 끊김. ${delay / 1000}초 후 재연결 시도... (횟수: ${this.retryCount})`);

            setTimeout(() => this.connect(), delay);
        };
    },

    addLog: function (message, type = "normal") {
        const logContainer = document.getElementById("log-container");
        const logLine = document.createElement("div");
        logLine.className = "border-b border-gray-800 py-1 animate-pulse"; // 새 로그 강조 효과
        logLine.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;

        logContainer.prepend(logLine);
        if (logContainer.children.length > this.MAX_LOG_COUNT) {
            logContainer.removeChild(logContainer.lastChild);
        }
    }
};

const Toast = {
    showToast: function (data) {
        const container = document.getElementById("toast-container");
        // Toast 요소 생성
        const toast = document.createElement("div");
        toast.className = "bg-white border-l-4 border-indigo-500 shadow-lg rounded-lg p-4 min-w-[300px] transform transition-all duration-300 translate-y-10 opacity-0";

        // 메시지 구성 (found_sites 배열에서 이름만 추출)
        const siteNames = data.list.map((site) => site.site_name).join(", ");

        toast.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0 text-indigo-500">
                <i class="fa-solid fa-bell-concierge"></i>
            </div>
            <div class="ml-3">
                <p class="text-sm font-black text-slate-800">빈자리 발견!</p>
                <p class="text-xs text-slate-600 mt-1">${data.res_dt} (${data.res_days}박)</p>
                <p class="text-xs font-bold text-indigo-600">${siteNames}</p>
                <p class="text-xs font-bold text-indigo-600"><a href="${data.link}" target="_blank">바로가기</a></p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-auto text-slate-400 hover:text-slate-600">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
    `;

        container.appendChild(toast);

        // 애니메이션 효과 (나타나기)
        setTimeout(() => {
            toast.classList.remove("translate-y-10", "opacity-0");
        }, 10);

        // 5초 후 자동 삭제
        setTimeout(() => {
            toast.classList.add("opacity-0");
            setTimeout(() => toast.remove(), 300);
        }, 1000 * 60);
    }
};
```

### [/camping-scanner/app/static/css/style.css]

```css
@import url("https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;900&display=swap");

body {
    font-family: "Pretendard", sans-serif;
    background-color: #f1f5f9;
}

.custom-scrollbar::-webkit-scrollbar {
    width: 5px;
    height: 5px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 10px;
}

.hidden-layer {
    transform: translateX(100%);
}

#menuLayer {
    transition: transform 0.3s ease-in-out;
}

select,
input {
    border: 1px solid #d1d5db !important;
}
```

### [/camping-scanner/app/templates/index.html]

```html
<!doctype html>
<html lang="ko">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>캠핑가자 Web Admin</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
        <link rel="stylesheet" href="/static/css/style.css" />
        <style></style>
    </head>
    <body class="flex flex-col h-screen overflow-hidden">
        <header class="w-full h-14 bg-white border-b shadow-sm flex items-center justify-between px-6 z-20">
            <div class="flex items-center space-x-2">
                <i class="fa-solid fa-tent text-indigo-600 text-xl"></i>
                <h1 class="text-xl font-black text-slate-800">
                    캠핑가자
                    <span class="text-slate-400 text-xs font-medium">ver 1.4.2 (Py)</span>
                </h1>
            </div>

            <!-- 우측 상단 버튼 그룹 -->
            <div class="flex items-center space-x-2">
                <!-- 프로그램 종료 버튼 추가 -->

                <!-- 기존 햄버거 메뉴 -->
                <button onclick="toggleMenu()" class="p-2 hover:bg-slate-100 rounded-lg transition">
                    <i class="fa-solid fa-bars text-xl text-slate-600"></i>
                </button>

                <button onclick="confirmShutdown()" class="flex items-center space-x-2 px-3 py-1.5 bg-white border border-red-200 text-red-600 text-xs font-black rounded-lg hover:bg-red-50 hover:border-red-300 transition-all shadow-sm" title="애플리케이션 종료">
                    <i class="fa-solid fa-power-off"></i>
                    <span>프로그램 종료</span>
                </button>
            </div>
        </header>

        <div class="flex flex-1 overflow-hidden">
            <aside class="w-64 bg-white border-r flex flex-col shadow-inner">
                <div class="p-4 space-y-4">
                    <div class="space-y-2">
                        <label class="text-xs font-black text-indigo-600 uppercase">Camping Platform</label>
                        <select id="platformSelect" class="w-full p-2 text-sm font-bold bg-slate-50 rounded border-slate-300 outline-none focus:ring-2 focus:ring-indigo-500">
                            {% for name, filename in platform_map.items() %}
                            <option value="{{ filename }}">{{ name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <div class="px-4 pb-2">
                    <label class="text-xs font-black text-slate-400 uppercase">Camping Sites</label>
                </div>
                <nav class="flex-1 overflow-y-auto custom-scrollbar px-2 pb-4">
                    <ul id="campsiteList" class="space-y-0.5 text-sm">
                        <!--
              <li class="p-2.5 hover:bg-indigo-50 hover:text-indigo-700 rounded cursor-pointer transition border-b border-slate-50">1) 평택 진위천유원지</li>
              <li class="p-2.5 hover:bg-indigo-50 hover:text-indigo-700 rounded cursor-pointer transition border-b border-slate-50">2) 안성 안성맞춤캠핑장</li>
              <li class="p-2.5 bg-indigo-600 text-white shadow-md rounded font-bold">4) 연천 한탄강오토캠핑장</li>
              <li class="p-2.5 hover:bg-indigo-50 hover:text-indigo-700 rounded cursor-pointer transition border-b border-slate-50">13) 서울 우이동가족캠핑장</li>
              -->
                    </ul>
                </nav>
            </aside>

            <main class="flex-1 flex flex-col overflow-hidden">
                <div class="flex-1 p-4 grid grid-cols-12 gap-4 overflow-y-auto custom-scrollbar">
                    <section id="reservationPanel" class="col-span-5 bg-white rounded border border-slate-300 flex flex-col shadow-sm">
                        <div class="p-3 border-b bg-slate-50 flex justify-between items-center">
                            <h2 class="font-black text-slate-700 text-sm"><i class="fa-solid fa-pen-to-square mr-1"></i> 예약 정보</h2>
                            <div class="space-x-1">
                                <button class="px-3 py-1 bg-indigo-600 text-white text-xs font-bold rounded hover:bg-indigo-700" id="watchBtn">감시</button>
                                <button class="px-3 py-1 bg-white border border-slate-300 text-slate-600 text-xs font-bold rounded hover:bg-slate-50" id="homePageBtn">홈페이지</button>
                            </div>
                        </div>
                        <div class="p-4 space-y-4 text-sm">
                            <div class="flex items-center">
                                <label class="w-24 font-bold text-slate-600">플랫폼 :</label>
                                <span class="font-black text-indigo-600" id="platformName"></span>
                            </div>
                            <div class="flex items-center">
                                <label class="w-24 font-bold text-slate-600">캠핑장 :</label>
                                <span class="font-black text-indigo-600" id="campsiteName"></span>
                            </div>
                            <div class="flex items-center">
                                <label class="w-24 font-bold text-slate-600">예약일 :</label>
                                <input type="date" value="" class="flex-1 p-1.5 border rounded" id="watchDate" />
                            </div>
                            <div class="flex items-center">
                                <label class="w-24 font-bold text-slate-600">연박 :</label>
                                <select class="flex-1 p-1.5 border rounded bg-white" id="dayCountSelect">
                                    <option value="1">1박</option>
                                    <option value="2">2박</option>
                                </select>
                            </div>
                            <div class="flex flex-col space-y-2">
                                <label class="font-bold text-slate-600 border-b pb-1">사이트 :</label>
                                <div class="grid grid-cols-2 gap-2 p-3 bg-slate-50 rounded border border-dashed" id="siteCheckerContainer">
                                    <!--
                                      <label class="flex items-center"><input type="checkbox" checked class="mr-2 accent-indigo-600" /> 전체</label>
                                      <label class="flex items-center"><input type="checkbox" checked class="mr-2 accent-indigo-600" /> 언덕야영장</label>
                                      <label class="flex items-center"><input type="checkbox" checked class="mr-2 accent-indigo-600" /> 강변야영장</label>
                                      <label class="flex items-center"><input type="checkbox" class="mr-2 accent-indigo-600" /> 캐라반</label>
                                      -->
                                </div>
                            </div>
                            <div class="space-y-3 pt-2 border-t">
                                <div class="flex items-center">
                                    <label class="w-24 font-bold text-slate-600 text-xs">최대요청주기</label>
                                    <select class="flex-1 p-1 border rounded text-xs" id="requestInterval">
                                        <option value="60">1분</option>
                                        <option value="30">30초</option>
                                        <option value="10">10초</option>
                                    </select>
                                </div>
                                <div class="flex items-center">
                                    <label class="w-24 font-bold text-slate-600 text-xs underline decoration-indigo-300">아이디</label>
                                    <input type="text" class="flex-1 p-1 border rounded text-xs" />
                                </div>
                                <div class="flex items-center">
                                    <label class="w-24 font-bold text-slate-600 text-xs underline decoration-indigo-300">비밀번호</label>
                                    <input type="password" class="flex-1 p-1 border rounded text-xs" />
                                </div>
                                <div class="flex items-center justify-end">
                                    <label class="flex items-center font-bold text-red-600 text-xs"> <input type="checkbox" class="mr-1 w-4 h-4" /> 자동 예약 요청 </label>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section class="col-span-7 bg-white rounded border border-slate-300 flex flex-col shadow-sm">
                        <div class="p-3 border-b bg-slate-50">
                            <h2 class="font-black text-slate-700 text-sm"><i class="fa-solid fa-chart-line mr-1"></i> 감시 정보</h2>
                        </div>
                        <div class="flex-1 overflow-auto custom-scrollbar">
                            <table class="w-full text-xs text-left border-collapse">
                                <thead class="bg-slate-100 sticky top-0 border-b border-slate-300">
                                    <tr class="text-slate-600">
                                        <th class="p-2 border-r font-bold">사이트명</th>
                                        <th class="p-2 border-r font-bold text-center">예약일</th>
                                        <th class="p-2 border-r font-bold text-center">박수</th>
                                        <th class="p-2 border-r font-bold text-center">요청수</th>
                                        <th class="p-2 font-bold text-center">상태</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y" id="monitoring-list">
                                    <tr class="hover:bg-slate-50 EMPTY-ROW">
                                        <td class="p-2 text-center text-green-600 font-bold italic" colspan="5">감시 중인 항목이 없습니다.</td>
                                        <!--
                                            <td class="p-2 border-r font-bold">연천 한탄강오토캠핑장</td>
                                            <td class="p-2 border-r text-center">2026-05-03</td>
                                            <td class="p-2 border-r text-center">1</td>
                                            <td class="p-2 border-r text-center font-bold text-indigo-600">12</td>
                                            <td class="p-2 text-center text-green-600 font-bold italic">Monitoring..</td>
                                            -->
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div class="p-3 border-t bg-slate-50 flex justify-center">
                            <button class="px-6 py-2 bg-red-50 border border-red-200 text-red-600 font-black rounded hover:bg-red-100 transition text-sm" id="stopWatchBtn">감지 중지</button>
                        </div>
                    </section>
                </div>

                <div id="footer-resizer" class="h-1 bg-slate-700 hover:bg-indigo-500 cursor-ns-resize transition-colors z-30"></div>
                <footer id="main-footer" style="height: 176px" class="bg-[#1e1e1e] text-[#d4d4d4] p-3 font-mono text-[11px] overflow-y-auto border-t-2 border-indigo-500">
                    <div class="flex items-center justify-between mb-2 text-slate-500 border-b border-slate-800 pb-1">
                        <span><i class="fa-solid fa-terminal mr-1"></i> LOG CONSOLE</span>
                        <span class="text-[10px] uppercase opacity-50">v1.4.2 build 20260428</span>
                    </div>
                    <div class="space-y-0.5" id="log-container">
                        <!--
                            <p><span class="text-slate-500">[ 2026-04-28 14:23:16 INFO ]</span> - [ 연천 한탄강오토캠핑장 ] 2026-05-03 1박 예약 자리 없음</p>
                            <p><span class="text-slate-500">[ 2026-04-28 14:23:09 INFO ]</span> - [ 연천 한탄강오토캠핑장 ] 검색 사이트 : 언덕야영장(파쇄석), 강변야영장(파쇄석)...</p>
                            <p class="text-emerald-400 font-bold underline underline-offset-2">▶ [ 2026-04-28 14:23:00 INFO ] - 다음 감시 대기 중... (7초)</p>
                            -->
                    </div>
                </footer>
            </main>
        </div>

        <div id="menuLayer" class="fixed inset-y-0 right-0 w-72 bg-white shadow-2xl z-30 p-6 hidden-layer border-l">
            <div class="flex justify-between items-center mb-8">
                <h2 class="text-lg font-black text-slate-800 italic">SYSTEM MENU</h2>
                <button onclick="toggleMenu()" class="text-slate-400 hover:text-slate-800">
                    <i class="fa-solid fa-xmark text-xl"></i>
                </button>
            </div>
            <ul class="space-y-4 font-bold text-sm text-slate-600">
                <li class="flex items-center p-2 hover:bg-slate-50 rounded cursor-pointer transition"><i class="fa-solid fa-gear w-8 text-indigo-500"></i><span>환경 설정</span></li>
                <li class="flex items-center p-2 hover:bg-slate-50 rounded cursor-pointer transition"><i class="fa-solid fa-bell w-8 text-indigo-500"></i><span>텔레그램 봇 연동</span></li>
                <li class="flex items-center p-2 hover:bg-slate-50 rounded cursor-pointer transition border-t pt-4 mt-4"><i class="fa-solid fa-circle-info w-8 text-slate-400"></i><span>도움말 및 정보</span></li>
            </ul>
        </div>
        <div id="overlay" onclick="toggleMenu()" class="fixed inset-0 bg-black/30 backdrop-blur-sm z-20 hidden"></div>
        <div id="toast-container" class="fixed bottom-5 right-5 z-50 flex flex-col gap-2"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/moment.min.js"></script>
        <script>
            const campsiteData = {{ campsites | tojson }};
        </script>
        <script src="/static/js/script.js"></script>
        <script>
            document.addEventListener("DOMContentLoaded", () => {
                Comp.init();
                Logger.init();
                Alert.init();
            });
        </script>
    </body>
</html>
```
