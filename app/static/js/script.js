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

// 2. 모달 제어 함수 (전역으로 선언)
function openTgModal() {
    document.getElementById("telegramModal").classList.remove("hidden");
    toggleMenu(); // 사이드 메뉴 닫기
}

function closeTgModal() {
    document.getElementById("telegramModal").classList.add("hidden");
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
        this.restoreMonitoringList();
    },

    bindEvents: function () {
        document.getElementById("platformSelect").addEventListener("change", this.changeFlatform);
        document.getElementById("watchBtn").addEventListener("click", this.watchCampsite);
        document.getElementById("stopWatchBtn").addEventListener("click", () => this.stopWatching()); //감시중지
        document.getElementById("homePageBtn").addEventListener("click", () => this.openHomePage()); //홈페이지 열기
        document.getElementById("watchDate").addEventListener("change", () => this.onChangeWatchDate()); //날짜 변경 체크(인터파크)
        document.getElementById("telegramConfigBtn").addEventListener("click", () => this.openTgModal()); //텔레그램 설정
        document.getElementById("settingConfigBtn").addEventListener("click", () => this.openSettingsModal()); //환경설정 설정
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
    //실행중인 감시 목록 조회
    restoreMonitoringList: async function () {
        const response = await fetch("/api/monitor/list");
        const jobs = await response.json();
        jobs.forEach((job) => this.addMonitoringEntry(job));
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

        const findNextRunChecked = document.getElementById("findNextRun").checked;
        const findNextRunValue = findNextRunChecked ? "N" : "Y";

        if (parent.checkExistingMonitoring(watchUuid)) {
            alert("이미 동일한 감시 항목이 존재합니다.");
            return;
        }

        const selectedSites = Array.from(document.querySelectorAll(".site-item:checked")).map((cb) => cb.value);

        if (selectedSites.length === 0) {
            alert("최소 하나 이상의 사이트를 선택해주세요.");
            return;
        }

        let groupCode = "";
        const groupCodeElement = currentCampsite.getElementsByTagName("groupCode");
        if (groupCodeElement.length > 0) {
            groupCode = groupCodeElement[0].textContent || "";
        }

        const requestData = {
            type: type, // "THANKQ"
            campsiteName: campsiteName, // "THANKQ"
            camp_id: campId, // "3446"
            date: watchDate, // "2026-04-28"
            stay_day: stayDay, // 1
            findNextRun: findNextRunValue,
            requestInterval: requestInterval, // 1
            watchUuid: watchUuid, // UUID for tracking the monitoring session
            groupCode: groupCode, //그룹코드 하위 그룹이 있을 경우
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
    // 텔레그램 설정 저장
    saveTgSettings: async function () {
        const useYn = document.getElementById("tgUseYn").value;
        const token = document.getElementById("tgToken").value;
        const chatIdsStr = document.getElementById("tgChatIds").value;

        // 문자열을 배열로 변환 (공백 제거)
        const chatIds = chatIdsStr
            .split(",")
            .map((id) => id.trim())
            .filter((id) => id !== "");

        const response = await fetch("/api/settings/telegram", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ use_yn: useYn, token: token, chat_ids: chatIds })
        });

        if (response.ok) {
            Logger.addLog("텔레그램 설정이 성공적으로 저장되었습니다.");
            closeTgModal();
        }
    },
    // 모달 열기 및 데이터 로드
    openSettingsModal: async function () {
        try {
            const response = await fetch("/api/settings");
            const data = await response.json();

            // Form에 데이터 채우기
            const form = document.getElementById("infoSettingsForm");
            for (const [key, value] of Object.entries(data.info)) {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) input.value = value;
            }

            document.getElementById("settingsModal").classList.remove("hidden");
            toggleMenu();
        } catch (e) {
            alert("설정을 불러오는데 실패했습니다.");
        }
    },

    closeSettingsModal: function () {
        document.getElementById("settingsModal").classList.add("hidden");
    },

    // 환경설정(Info) 저장
    saveInfoSettings: async function () {
        const form = document.getElementById("infoSettingsForm");
        const inputs = form.querySelectorAll("input");
        const infoData = {};

        inputs.forEach((input) => {
            // 숫자형 데이터 변환 처리
            const val = input.type === "number" ? parseInt(input.value) : input.value;
            infoData[input.name] = val;
        });

        const response = await fetch("/api/settings/info", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(infoData)
        });

        if (response.ok) {
            Logger.addLog("시스템 환경설정이 저장되었습니다.");
            this.closeSettingsModal();
        }
    },

    // 텔레그램 모달 열기 시 기존 값 세팅 (수정)
    openTgModal: async function () {
        const response = await fetch("/api/settings");
        const data = await response.json();

        document.getElementById("tgUseYn").value = data.telegram.use_yn || "N";
        document.getElementById("tgToken").value = data.telegram.token || "";
        // 배열을 콤마 구분 문자열로 변환하여 표시
        document.getElementById("tgChatIds").value = (data.telegram.chat_ids || []).join(", ");

        document.getElementById("telegramModal").classList.remove("hidden");
        toggleMenu();
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
            const count = data.count || 0;
            const row = document.querySelector(`tr[data-watchuuid="${uuid}"]`);

            // debugger;

            if (row) {
                //let currentCount = row.dataset.reqcnt;
                //let numericCount = parseInt(currentCount || 0, 10) + 1;
                //row.dataset.reqcnt = numericCount;
                const countCell = row.querySelector("td.MNT-COUNT");
                if (countCell) {
                    countCell.innerText = count;
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

        if (data.link) {
            window.open(data.link);
        }

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
