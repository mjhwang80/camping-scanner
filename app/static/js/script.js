const resizer = document.getElementById("footer-resizer");
const footer = document.getElementById("main-footer");

let isResizing = false;
if (resizer) {
    resizer.addEventListener("mousedown", (e) => {
        isResizing = true;
        document.body.style.userSelect = "none";
        resizer.classList.add("bg-indigo-500");
    });
}

document.addEventListener("mousemove", (e) => {
    if (!isResizing) return;
    // 다단 그리드 축소 확장에 무리 없는 높이 제한 계산 수식 적용
    const newHeight = window.innerHeight - e.clientY;
    if (newHeight > 60 && newHeight < window.innerHeight * 0.7) {
        footer.style.height = `${newHeight}px`;
    }
});

document.addEventListener("mouseup", () => {
    isResizing = false;
    document.body.style.userSelect = "auto";
    if (resizer) resizer.classList.remove("bg-indigo-500");
});

function toggleMenu() {
    document.getElementById("menuLayer").classList.toggle("hidden-layer");
    document.getElementById("overlay").classList.toggle("hidden");
}

function openTgModal() {
    document.getElementById("telegramModal").classList.remove("hidden");
    toggleMenu();
}

function closeTgModal() {
    document.getElementById("telegramModal").classList.add("hidden");
}

// 도구 레이어 토글 함수
function toggleToolLayer() {
    const layer = document.getElementById("downloader-layer");
    if (layer.style.display === "none") {
        layer.style.display = "block";
    } else {
        layer.style.display = "none";
    }
}

// 백엔드 서버에 다운로드 요청 전송
async function requestDownload() {
    const dlType = document.getElementById("download-type").value;
    const dlUrl = document.getElementById("download-url").value.trim();

    if (!dlUrl) {
        alert("다운로드할 URL 주소를 입력해주세요.");
        return;
    }

    try {
        const response = await fetch("/api/tools/download", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                type: dlType,
                url: dlUrl
            })
        });

        const result = await response.json();

        if (result.status === "success") {
            alert(result.message);
            // 요청 성공 시 입력창 초기화
            document.getElementById("download-url").value = "";
        } else {
            alert("요청 실패: " + result.message);
        }
    } catch (error) {
        console.error("다운로드 요청 중 서버 통신 에러:", error);
        alert("서버와 연결할 수 없습니다.");
    }
}

window.addEventListener("popstate", function () {
    if (!document.getElementById("menuLayer").classList.contains("hidden-layer")) {
        toggleMenu();
    }
});

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
                </div>`;
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
    interparkStayOption: {},
    selectedMonitoringUuid: null,

    init: function () {
        this.initComponent();
        this.bindEvents();
        this.changeFlatform();
        this.restoreMonitoringList();
    },

    bindEvents: function () {
        document.getElementById("platformSelect").addEventListener("change", () => this.changeFlatform());
        document.getElementById("watchBtn").addEventListener("click", () => this.watchCampsite());
        document.getElementById("homePageBtn").addEventListener("click", () => this.openHomePage());
        document.getElementById("weatherPageBtn").addEventListener("click", () => window.open("https://www.windy.com/ko?37.549,126.658,5,p:cities"));
        document.getElementById("seaPageBtn").addEventListener("click", () => window.open("https://www.badatime.com/"));
        document.getElementById("watchDate").addEventListener("change", () => this.onChangeWatchDate());
        document.getElementById("telegramConfigBtn").addEventListener("click", () => openTgModal());
        document.getElementById("settingConfigBtn").addEventListener("click", () => this.openSettingsModal());
        document.getElementById("execTypeSelect").addEventListener("change", () => this.onChangeExecType());
    },

    initComponent: function () {
        const dateInput = document.getElementById("watchDate");
        const tomorrow = moment().add(1, "days").format("YYYY-MM-DD");
        dateInput.min = tomorrow;
        dateInput.value = tomorrow;

        const reservedInput = document.getElementById("reservedDateTime");
        if (reservedInput) {
            reservedInput.value = moment().format("YYYY-MM-DDTHH:mm:ss");
        }
    },

    changeFlatform: async function () {
        const selectEl = document.getElementById("platformSelect");
        const listContainer = document.getElementById("campsiteList");
        const filename = selectEl.value;

        listContainer.innerHTML = '<li class="p-4 text-center text-slate-400">XML 데이터 파싱중...</li>';

        try {
            const response = await fetch(`/api/campsites/${filename}`);
            if (!response.ok) throw new Error("네트워크 응답 에러");

            const xmlText = await response.text();
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xmlText, "text/xml");

            Comp.renderCampsiteList(xmlDoc);
        } catch (error) {
            console.error("데이터 로드 중 오류 발생:", error);
            listContainer.innerHTML = '<li class="p-4 text-center text-red-500">데이터를 불러오지 못했습니다.</li>';
        }
    },

    restoreMonitoringList: async function () {
        try {
            const response = await fetch("/api/monitor/list");
            const jobs = await response.json();
            const monitoringList = document.getElementById("monitoring-list");

            monitoringList.innerHTML = "";
            if (jobs.length === 0) {
                monitoringList.innerHTML = `
                <tr class="hover:bg-slate-50 EMPTY-ROW">
                    <td class="p-2 text-center text-green-600 font-bold italic" colspan="5">감시 중인 항목이 없습니다.</td>
                </tr>`;
                return;
            }
            jobs.forEach((job) => this.addMonitoringEntry(job));
        } catch (e) {
            console.error("감시 목록을 동기화 조회하지 못했습니다:", e);
        }
    },

    renderCampsiteList: function (xmlDoc) {
        const listContainer = document.getElementById("campsiteList");
        listContainer.innerHTML = "";

        const campsites = xmlDoc.getElementsByTagName("campsite");
        const type = xmlDoc.getElementsByTagName("type");
        const homepage = xmlDoc.getElementsByTagName("homepage");

        Array.from(campsites).forEach((site, index) => {
            const nameNode = site.getElementsByTagName("name")[0];
            const name = nameNode ? nameNode.textContent : "이름 없음";

            const typeElement = xmlDoc.createElement("type");
            typeElement.textContent = type[0].textContent;
            site.appendChild(typeElement);

            if (homepage.length > 0) {
                const homepageElement = xmlDoc.createElement("homepage");
                homepageElement.textContent = homepage[0].textContent;
                site.appendChild(homepageElement);
            }

            const li = document.createElement("li");
            li.className = "p-3 hover:bg-indigo-50 cursor-pointer border-b border-slate-100 transition text-xs font-semibold rounded";
            li.innerHTML = `
                <div class="flex flex-col">
                  <span class="text-slate-800">${index + 1}. ${name}</span>
                </div>`;

            li.onclick = () => {
                this.highlightSelection(li);
                this.updateDetailPanel(site);
            };

            listContainer.appendChild(li);

            if (index == 0) {
                this.highlightSelection(li);
                this.updateDetailPanel(site);
            }
        });
    },

    highlightSelection: function (element) {
        document.querySelectorAll("#campsiteList li").forEach((el) => el.classList.remove("bg-indigo-100", "text-indigo-700"));
        element.classList.add("bg-indigo-100", "text-indigo-700");
    },

    updateDetailPanel: function (site) {
        this.currentCampsiteData = site;

        const name = site.getElementsByTagName("name")[0]?.textContent || "이름 없음";
        const type = site.getElementsByTagName("type")[0]?.textContent || "정보 없음";

        document.getElementById("campsiteName").textContent = name;
        document.getElementById("platformName").textContent = type;

        const showLogin = site.getElementsByTagName("showLoginField")[0]?.textContent || "N";
        const loginArea = document.getElementById("loginFields");
        if (showLogin === "Y") {
            loginArea.classList.remove("hidden");
        } else {
            loginArea.classList.add("hidden");
        }

        const supportAuto = site.getElementsByTagName("isSupportAutoReservation")[0]?.textContent || "N";
        const autoReserveArea = document.getElementById("autoReserveField");
        if (supportAuto === "Y") {
            autoReserveArea.classList.remove("hidden");
        } else {
            autoReserveArea.classList.add("hidden");
        }

        const authPanel = document.getElementById("interparkAuthPanel");
        if (type === "Interpark" && supportAuto === "Y") {
            authPanel.classList.remove("hidden");
        } else {
            authPanel.classList.add("hidden");
        }

        this.generatorMaxDayOption(site);
        this.generatorSiteChecker(site);

        if (window.innerWidth < 768) {
            document.getElementById("reservationPanel").scrollIntoView({ behavior: "smooth" });
        }
    },

    onChangeWatchDate: function () {
        const type = Comp.currentCampsiteData.getElementsByTagName("type")[0]?.textContent;
        if (type === "Interpark") {
            const goodsCode = Comp.currentCampsiteData.getElementsByTagName("code")[0]?.textContent;
            const selectedDate = document.getElementById("watchDate").value;
            const start_date = moment(selectedDate).format("YYYYMMDD");
            Comp.generatorInterparkDayOption(start_date, Comp.interparkStayOption[goodsCode]);
        }
    },

    generatorMaxDayOption: function (site) {
        const dayCountSelect = document.getElementById("dayCountSelect");
        dayCountSelect.innerHTML = "";

        const type = site.getElementsByTagName("type")[0]?.textContent || "";
        if (type === "Interpark") {
            const goodsCode = site.getElementsByTagName("code")[0]?.textContent;
            const watchDate = document.getElementById("watchDate").value;
            const start_date = moment(watchDate).format("YYYYMMDD");
            if (goodsCode in Comp.interparkStayOption) {
                Comp.generatorInterparkDayOption(start_date, Comp.interparkStayOption[goodsCode]);
            } else {
                const end_date = moment(watchDate).add(2, "months").format("YYYYMMDD");
                Comp.fetchInterParkStayDayOption(goodsCode, start_date, end_date);
            }
        } else {
            const maxStayDay = site.getElementsByTagName("maxStayDay")[0]?.textContent || 2;
            for (let i = 0; i < maxStayDay; i++) {
                const option = document.createElement("option");
                option.value = `${i + 1}`;
                option.textContent = `${i + 1}박`;
                dayCountSelect.appendChild(option);
            }
        }
    },

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
            if (result.common.message === "success" && result.data) {
                Comp.interparkStayOption[goodsCode] = result.data;
                Comp.generatorInterparkDayOption(start_date, Comp.interparkStayOption[goodsCode]);
            }
        } catch (error) {
            console.error("서버 통신 오류:", error);
        }
    },

    generatorSiteChecker: function (site) {
        const siteCheckerContainer = document.getElementById("siteCheckerContainer");
        const labelArea = document.querySelector("#reservationPanel label.border-b");
        if (!labelArea) return;

        const oldAllCheck = document.getElementById("allCheckWrapper");
        if (oldAllCheck) oldAllCheck.remove();

        const allCheckWrapper = document.createElement("span");
        allCheckWrapper.id = "allCheckWrapper";
        allCheckWrapper.className = "ml-auto flex items-center text-[10px] font-normal cursor-pointer text-slate-500";
        allCheckWrapper.innerHTML = `
            <input type="checkbox" id="allCheck" class="mr-1 w-3 h-3 accent-indigo-600" checked />
            전체 선택`;

        labelArea.classList.add("flex", "items-center", "justify-between");
        labelArea.appendChild(allCheckWrapper);
        siteCheckerContainer.innerHTML = "";

        const groupsWrapper = site.getElementsByTagName("groups")[0];
        if (groupsWrapper) {
            const groups = groupsWrapper.getElementsByTagName("group");
            if (groups.length > 0) {
                const groupTitle = document.createElement("div");
                groupTitle.className = "col-span-2 text-[10px] font-black text-indigo-400 mt-2 border-b border-slate-200 pb-0.5";
                groupTitle.innerHTML = `<i class="fa-solid fa-layer-group mr-1"></i> 사이트 그룹`;
                siteCheckerContainer.appendChild(groupTitle);

                Array.from(groups).forEach((group) => {
                    const groupCode = group.getAttribute("code");
                    const groupName = group.textContent;

                    const label = document.createElement("label");
                    label.className = "flex items-center p-1 bg-indigo-50/50 rounded cursor-pointer hover:bg-indigo-50 transition";
                    label.innerHTML = `
                        <input type="checkbox" checked class="group-item mr-2 accent-indigo-600" data-group-code="${groupCode}" />
                        <span class="text-xs font-bold text-indigo-700">${groupName}</span>`;
                    siteCheckerContainer.appendChild(label);
                });
            }
        }

        const sites = site.getElementsByTagName("site");
        if (sites.length > 0) {
            const siteTitle = document.createElement("div");
            siteTitle.className = "col-span-2 text-[10px] font-black text-slate-400 mt-2 border-b border-slate-200 pb-0.5";
            siteTitle.innerHTML = `<i class="fa-solid fa-list mr-1"></i> 사이트 목록`;
            siteCheckerContainer.appendChild(siteTitle);

            Array.from(sites).forEach((element) => {
                const code = element.getAttribute("code") || "";
                const groupAttr = element.getAttribute("group") || "";
                const name = element.textContent || "";

                const label = document.createElement("label");
                label.className = "flex items-center p-1 cursor-pointer hover:bg-slate-100 rounded transition";
                label.innerHTML = `
                    <input type="checkbox" checked class="site-item mr-2 accent-indigo-600" value="${code}" data-parent-group="${groupAttr}" />
                    <span class="text-xs text-slate-700">${name}</span>`;
                siteCheckerContainer.appendChild(label);
            });
        }
        this.bindAllCheckEvent();
    },

    watchCampsite: async function () {
        const parent = Comp;
        const currentCampsite = Comp.currentCampsiteData;
        if (!currentCampsite) return;

        const watchDate = document.getElementById("watchDate").value;
        const stayDay = document.getElementById("dayCountSelect").value;
        const type = currentCampsite.getElementsByTagName("type")[0]?.textContent;
        const campId = currentCampsite.getElementsByTagName("code")[0]?.textContent;
        const requestInterval = document.getElementById("requestInterval").value;
        const campsiteName = currentCampsite.getElementsByTagName("name")[0]?.textContent;

        const execType = document.getElementById("execTypeSelect").value;
        let reservedTime = null;
        if (execType === "RESERVED") {
            const reservedTimeVal = document.getElementById("reservedDateTime").value;
            if (!reservedTimeVal) {
                alert("예약 실행 시간을 입력해주세요.");
                return;
            }
            const reservedMoment = moment(reservedTimeVal);
            if (reservedMoment.isBefore(moment())) {
                alert("예약 시간은 현재 시간보다 이후여야 합니다.");
                return;
            }
            reservedTime = reservedMoment.format("YYYY-MM-DD HH:mm:ss");
        }

        const watchUuid = `${type}_${campId}_${watchDate}_${stayDay}`;
        const findNextRunChecked = document.getElementById("findNextRun").checked;
        const findNextRunValue = findNextRunChecked ? "N" : "Y";
        const autoReserveChecked = document.getElementById("autoReserve").checked;
        const autoReserveValue = autoReserveChecked ? "Y" : "N";

        if (parent.checkExistingMonitoring(watchUuid)) {
            alert("이미 동일한 감시 항목이 존재합니다.");
            return;
        }

        const selectedSites = Array.from(document.querySelectorAll(".site-item:checked")).map((cb) => cb.value);
        if (selectedSites.length === 0) {
            alert("최소 하나 이상의 구역 사이트를 선택해주세요.");
            return;
        }

        let groupCode = "";
        const groupCodeElement = currentCampsite.getElementsByTagName("groupCode");
        if (groupCodeElement.length > 0) groupCode = groupCodeElement[0].textContent || "";

        let hasCategory = currentCampsite.getElementsByTagName("groups").length > 0 ? "Y" : "N";
        const isShowLoginField = currentCampsite.getElementsByTagName("showLoginField")[0]?.textContent || "N";

        let userId = document.getElementById("userId").value.trim();
        let userPw = document.getElementById("userPw").value.trim();

        const loginFieldNode = currentCampsite.getElementsByTagName("showLoginField")[0];
        if (loginFieldNode && loginFieldNode.getAttribute("required") === "Y") {
            if (userId === "" || userPw === "") {
                alert("계정 정보(ID/PW)를 입력해야 동작하는 플랫폼입니다.");
                return;
            }
        }

        const requestData = {
            type: type,
            campsiteName: campsiteName,
            camp_id: campId,
            date: watchDate,
            stay_day: stayDay,
            findNextRun: findNextRunValue,
            requestInterval: requestInterval,
            watchUuid: watchUuid,
            groupCode: groupCode,
            hasCategory: hasCategory,
            autoReserve: autoReserveValue,
            execType: execType,
            reservedTime: reservedTime,
            userId: userId,
            userPw: userPw,
            site_group_codes: Array.from(document.querySelectorAll("#siteCheckerContainer .group-item:checked")).map((cb) => cb.dataset.groupCode),
            site_codes: selectedSites
        };

        try {
            const response = await fetch("/api/monitor/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData)
            });

            if (response.ok) {
                if (execType === "RESERVED") {
                    Logger.addLog(`${requestData.type} 감시가 예약되었습니다! (${reservedTime} 기동)`, "system");
                    requestData.isReservedState = true;
                } else {
                    Logger.addLog(`${requestData.type} 즉시 감시를 시작합니다.`, "system");
                }
                // 중요: 웹소켓을 타고 타 디바이스로 동시 유입될 예정이므로
                // 내 로컬 UI에서는 중복 삽입 방지 로직이 addMonitoringEntry 내부에 내장되어 있습니다.
                parent.addMonitoringEntry(requestData);
            }
        } catch (error) {
            console.error("요청 실패:", error);
        }
    },

    checkExistingMonitoring: function (watchUuid) {
        const monitoringList = document.getElementById("monitoring-list");
        return Array.from(monitoringList.children).some((tr) => tr.dataset.watchuuid === watchUuid);
    },

    addMonitoringEntry: function (entry) {
        const monitoringList = document.getElementById("monitoring-list");

        // 다중 기기 실시간 웹소켓 브로드캐스트 유입 시 중복 추가 차단 (Defensive)
        if (this.checkExistingMonitoring(entry.watchUuid)) return;

        const emptyRow = document.querySelector("#monitoring-list .EMPTY-ROW");
        if (emptyRow) emptyRow.remove();

        let displayStayDay = entry.stay_day;
        if (entry.type === "Interpark" && String(entry.stay_day).includes(",")) {
            displayStayDay = `${String(entry.stay_day).split(",").length}박`;
        } else if (!String(displayStayDay).includes("박")) {
            displayStayDay = `${displayStayDay}박`;
        }

        const isReserved = entry.isReservedState || entry.execType === "RESERVED";
        const statusHtml = isReserved ? `<span class="text-amber-500 font-bold italic text-[10px]">대기중 (${entry.reservedTime ? entry.reservedTime.split(" ")[1] : "예약"})</span>` : `<span class="text-green-600 font-bold italic text-[10px]">Monitoring..</span>`;

        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-50 group transition-all duration-300";
        tr.innerHTML = `
            <td class="p-2 border-r font-bold text-slate-700">${entry.campsiteName}</td>
            <td class="p-2 border-r text-center text-slate-500">${entry.date}</td>
            <td class="p-2 border-r text-center text-slate-500">${displayStayDay}</td>
            <td class="p-2 border-r text-center font-bold text-indigo-600 MNT-COUNT">0</td>
            <td class="p-2 text-center">
                <div class="flex items-center justify-center space-x-3">
                    ${statusHtml}
                    <button class="stop-row-btn px-2.5 py-1 bg-red-500 text-white text-[10px] font-black rounded shadow-sm hover:bg-red-600 transition" 
                            data-uuid="${entry.watchUuid}">
                        중지
                    </button>
                </div>
            </td>`;
        tr.dataset.watchuuid = entry.watchUuid;

        tr.onclick = (e) => {
            if (e.target.classList.contains("stop-row-btn")) return;
            this.highlightMonitoringRow(tr);
            this.selectedMonitoringUuid = entry.watchUuid;
        };

        const stopBtn = tr.querySelector(".stop-row-btn");
        stopBtn.onclick = (e) => {
            e.stopPropagation();
            this.stopWatchingRow(entry.watchUuid);
        };

        monitoringList.appendChild(tr);
    },

    stopWatchingRow: async function (watchUuid) {
        if (!watchUuid) return;
        if (confirm("이 캠핑장 감시 작업을 중지하시겠습니까?")) {
            try {
                const response = await fetch(`/api/monitor/stop/${watchUuid}`, { method: "POST" });
                if (response.ok) {
                    Logger.addLog(`감시 중단 명령 전송 완료: ${watchUuid}`, "system");
                    // 내 화면에서 지우는 로직은 아래 Alert 웹소켓 'remove_monitor' 수신 시 통합 처리해도 되고
                    // 즉각 제거되도록 연동해도 웹소켓 수신 시 row 검사 루프로 방어됩니다.
                }
            } catch (error) {
                console.error("중지 요청 실패:", error);
            }
        }
    },

    highlightMonitoringRow: function (element) {
        document.querySelectorAll("#monitoring-list tr").forEach((el) => el.classList.remove("bg-red-50"));
        element.classList.add("bg-red-50");
    },

    saveTgSettings: async function () {
        const useYn = document.getElementById("tgUseYn").value;
        const token = document.getElementById("tgToken").value;
        const chatIdsStr = document.getElementById("tgChatIds").value;

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
            Logger.addLog("텔레그램 연동 정보가 설정되었습니다.", "system");
            closeTgModal();
        }
    },

    openSettingsModal: async function () {
        try {
            const response = await fetch("/api/settings");
            const data = await response.json();
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

    onChangeExecType: function () {
        const execType = document.getElementById("execTypeSelect").value;
        const reservedTimeFields = document.getElementById("reservedTimeFields");
        const requestInterval = document.getElementById("requestInterval");

        if (execType === "RESERVED") {
            reservedTimeFields.classList.remove("hidden");
        } else {
            reservedTimeFields.classList.add("hidden");
        }

        Array.from(requestInterval.options).forEach((option) => {
            if (option.value === "3" || option.value === "1") {
                option.disabled = execType === "NOW";
            }
        });

        if (execType === "NOW" && (requestInterval.value === "3" || requestInterval.value === "1")) {
            requestInterval.value = "30";
            Logger.addLog("서버 부하 분산을 우회하기 위해 즉시 실행 모드 주기는 30초로 기본 복구됩니다.", "system");
        }
    },

    saveInfoSettings: async function () {
        const form = document.getElementById("infoSettingsForm");
        const inputs = form.querySelectorAll("input");
        const infoData = {};

        inputs.forEach((input) => {
            const val = input.type === "number" ? parseInt(input.value) : input.value;
            infoData[input.name] = val;
        });

        const response = await fetch("/api/settings/info", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(infoData)
        });

        if (response.ok) {
            Logger.addLog("시스템 사용자 환경설정이 파일로 저장되었습니다.", "system");
            this.closeSettingsModal();
        }
    },

    renewInterparkSession: async function () {
        if (!confirm("인터파크 계정 인증을 위한 제어용 브라우저를 띄우시겠습니까?")) return;
        Logger.addLog("인터파크 원격 세션 취득 프로세스 대기중...", "system");
        try {
            const response = await fetch("/api/auth/interpark-session", { method: "POST" });
            const result = await response.json();
            if (result.status === "success") {
                alert("인터파크 인증 파일이 정상 생성되었습니다.");
            }
        } catch (error) {
            Logger.addLog("인터파크 세션 취득 실패", "error");
        }
    },

    bindAllCheckEvent: function () {
        const allCheck = document.getElementById("allCheck");
        const groupChecks = document.querySelectorAll(".group-item");
        const siteChecks = document.querySelectorAll(".site-item");

        if (!allCheck) return;

        allCheck.addEventListener("change", function () {
            const isChecked = allCheck.checked;
            groupChecks.forEach((gc) => (gc.checked = isChecked));
            siteChecks.forEach((sc) => (sc.checked = isChecked));
        });

        groupChecks.forEach((gc) => {
            gc.addEventListener("change", function () {
                const groupCode = this.dataset.groupCode;
                const isChecked = this.checked;
                document.querySelectorAll(`.site-item[data-parent-group="${groupCode}"]`).forEach((sc) => {
                    sc.checked = isChecked;
                });
                updateAllCheckStatus();
            });
        });

        siteChecks.forEach((sc) => {
            sc.addEventListener("change", function () {
                const groupCode = this.dataset.parentGroup;
                if (groupCode) {
                    const checkedGroupSites = document.querySelectorAll(`.site-item[data-parent-group="${groupCode}"]:checked`);
                    const groupHeader = document.querySelector(`.group-item[data-group-code="${groupCode}"]`);
                    if (groupHeader) {
                        groupHeader.checked = checkedGroupSites.length > 0;
                    }
                }
                updateAllCheckStatus();
            });
        });

        function updateAllCheckStatus() {
            const allItems = document.querySelectorAll(".site-item");
            const checkedItems = document.querySelectorAll(".site-item:checked");
            allCheck.checked = allItems.length === checkedItems.length;
        }
    },

    openHomePage: function () {
        if (!this.currentCampsiteData) return;
        const homepageUrl = this.currentCampsiteData.getElementsByTagName("homepage")[0]?.textContent;
        const campId = this.currentCampsiteData.getElementsByTagName("code")[0]?.textContent;
        window.open(`${homepageUrl}${campId}`, "_blank");
    },

    changeMonitoringCount: function (data) {
        if (data) {
            const uuid = data.uuid || "";
            const count = data.count || 0;
            const row = document.querySelector(`tr[data-watchuuid="${uuid}"]`);
            if (row) {
                const countCell = row.querySelector("td.MNT-COUNT");
                if (countCell) {
                    countCell.innerText = count;
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
            this.retryCount = 0;
        };
        socket.onclose = () => {
            this.retryCount++;
            const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000);
            setTimeout(() => this.connect(), delay);
        };
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.messageType) {
                case "alert":
                    Toast.showToast(data.data);
                    break;
                case "monitor":
                    Comp.changeMonitoringCount(data.data);
                    break;

                /* [실시간 다중기기 동기화 핵심] 타 디바이스에서 추가 진입 시 내 목록 화면에 실시간 주입 */
                case "add_monitor":
                    if (data.data) {
                        Comp.addMonitoringEntry(data.data);
                    }
                    break;

                /* [실시간 다중기기 동기화 핵심] 어떤 기기에서든 감시 삭제 시 부드럽게 UI 파괴 동기화 */
                case "remove_monitor":
                    if (data.data && data.data.uuid) {
                        const uuid = data.data.uuid;
                        const row = document.querySelector(`tr[data-watchuuid="${uuid}"]`);
                        if (row) {
                            row.style.transition = "all 0.4s ease-out";
                            row.style.backgroundColor = "#fee2e2";
                            row.style.opacity = "0";
                            row.style.transform = "translateX(30px)";
                            setTimeout(() => {
                                row.remove();
                                const monitoringList = document.getElementById("monitoring-list");
                                if (monitoringList.children.length === 0) {
                                    monitoringList.innerHTML = `
                                    <tr class="hover:bg-slate-50 EMPTY-ROW">
                                        <td class="p-2 text-center text-green-600 font-bold italic" colspan="5">감시 중인 항목이 없습니다.</td>
                                    </tr>`;
                                }
                            }, 400);
                        }
                    }
                    break;
            }
        };
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
            this.retryCount = 0;
        };
        ws.onmessage = (event) => {
            this.addLog(event.data);
        };
        ws.onclose = () => {
            this.retryCount++;
            const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000);
            setTimeout(() => this.connect(), delay);
        };
    },
    addLog: function (message) {
        const logContainer = document.getElementById("log-container");
        if (!logContainer) return;
        const logLine = document.createElement("div");
        logLine.className = "border-b border-gray-800 py-0.5 opacity-0 transition-opacity duration-300 text-[10px] text-slate-300 font-mono";
        logLine.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;

        logContainer.appendChild(logLine);
        setTimeout(() => logLine.classList.remove("opacity-0"), 10);

        if (logContainer.children.length > this.MAX_LOG_COUNT) {
            logContainer.removeChild(logContainer.firstChild);
        }
        // 로그창 위치 변경에 따른 자동 가용 스크롤 추적 고정
        logContainer.scrollTop = logContainer.scrollHeight;
    }
};

const Toast = {
    showToast: function (data) {
        const container = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = "bg-white border-l-4 border-indigo-500 shadow-lg rounded-lg p-4 min-w-[280px] transform transition-all duration-300 translate-y-10 opacity-0 z-50";

        const siteNames = data.list.map((site) => site.site_name).join(", ");
        const findNextOpenBroswerChecked = document.getElementById("findNextOpenBroswer").checked;
        if (data.link && findNextOpenBroswerChecked) {
            window.open(data.link);
        }

        toast.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0 text-indigo-500"><i class="fa-solid fa-bell"></i></div>
            <div class="ml-3">
                <p class="text-xs font-black text-slate-800">빈자리 검출 성공!</p>
                <p class="text-[10px] text-slate-500 mt-0.5">${data.res_dt} (${data.res_days}박)</p>
                <p class="text-xs font-bold text-indigo-600 truncate max-w-[200px]">${siteNames}</p>
                <p class="text-[10px] font-black text-slate-400 mt-1"><a href="${data.link}" target="_blank" class="underline hover:text-indigo-600">예약 사이트 바로가기</a></p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-auto text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
        </div>`;
        container.appendChild(toast);
        setTimeout(() => toast.classList.remove("translate-y-10", "opacity-0"), 10);
        setTimeout(() => {
            toast.classList.add("opacity-0");
            setTimeout(() => toast.remove(), 300);
        }, 1000 * 60);
    }
};
