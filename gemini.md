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
- /camping-scanner/app/core/browser_handler.py # Playwright 기반 보안 통과
- /camping-scanner/app/platforms # 사이트별 크롤링 모듈 (전략 패턴)
- /camping-scanner/app/platforms/base.py # 추상 베이스 클래스
- /camping-scanner/app/platforms/interpark.py # 인터파크 크롤링 로직
- /camping-scanner/app/platforms/interpark_reserver.py # 자동예약처리 로직
- /camping-scanner/app/platforms/mirihae.py # 미래해 크롤링 로직
- /camping-scanner/app/platforms/thankq.py # 땡큐캠핑 크롤링 로직
- /camping-scanner/app/platforms/maketicket.py # 메이크티켓 크롤링 로직
- /camping-scanner/app/platforms/xticket.py # X티켓 크롤링 로직
- /camping-scanner/app/platforms/dugsan.py # 덕산 크롤링 로직
- /camping-scanner/app/platforms/camplink.py # camplink 크롤링 로직
- /camping-scanner/app/platforms/pubcamping.py # pubcamping 크롤링 로직
- /camping-scanner/app/services # 비즈니스 로직 처리 (모니터링 서비스 등)
- /camping-scanner/app/services/monitor_service.py
- /camping-scanner/app/services/notification.py
- /camping-scanner/app/static # CSS, JS, Image 등 정적 파일
- /camping-scanner/app/static/css/style.css
- /camping-scanner/app/static/js/script.js # 프론트엔드 메인 로직
- /camping-scanner/app/templates # HTML 템플릿 (Jinja2)
- /camping-scanner/app/templates/index.html # 웹 초기 화면
- /camping-scanner/app/templates/pubcamping_gateway.html # 예약 페이지 이동을 위한 게이트웨이
- /camping-scanner/app/templates/gugu_gateway.html # 예약 페이지 이동을 위한 게이트웨이
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
- /camping-scanner/data/pubcamping-campsite.xml
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
- **특징:** 반응형 웹어플리케이션

## 2. 질문 사항

- index.html에 예약실행 필드를 두고 지정된 특정 시간에 감시가 시작 되도록 하고 싶어.

## 3. 분석 대상 코드

### [/camping-scanner/app/static/css/style.css]

```css
@import url("https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;900&display=swap");

body {
    font-family:
        "Pretendard",
        -apple-system,
        sans-serif;
    -webkit-tap-highlight-color: transparent; /* 터치 하이라이트 제거 */
}

/* 모바일 스크롤바 가독성 */
.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
    height: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: #e2e8f0;
    border-radius: 10px;
}

.hidden-layer {
    transform: translateX(100%);
}

#menuLayer {
    transition: transform 0.3s ease-in-out;
}

/* 폼 요소 모바일 최적화 (Safari 줌 방지) */
select,
input {
    border: 1px solid #e2e8f0 !important;
    font-size: 16px !important; /* iOS 포커스 시 자동 확대 방지 */
}

/* 리스트 항목 터치 영역 확대 */
#campsiteList li {
    padding: 14px 12px;
}

/* 토스트 메시지 모바일 대응 */
#toast-container {
    max-width: 100%;
}

@media (max-width: 768px) {
    /* 모바일에서는 리사이저 숨김 */
    #footer-resizer {
        display: none !important;
    }

    /* 모달 창 크기 조절 */
    .fixed.inset-0 > div {
        width: 90% !important;
        max-height: 85vh;
        overflow-y: auto;
    }
}
```

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

// 2. 모달 제어 함수 (전역으로 선언)
function openTgModal() {
    document.getElementById("telegramModal").classList.remove("hidden");
    toggleMenu(); // 사이드 메뉴 닫기
}

function closeTgModal() {
    document.getElementById("telegramModal").classList.add("hidden");
}

// [추가] 모바일에서 뒤로가기 버튼 등으로 메뉴 닫기 대응
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
        //document.getElementById("stopWatchBtn").addEventListener("click", () => this.stopWatching()); //감시중지
        document.getElementById("homePageBtn").addEventListener("click", () => this.openHomePage()); //홈페이지 열기
        document.getElementById("weatherPageBtn").addEventListener("click", () => window.open("https://www.windy.com/ko?37.549,126.658,5,p:cities")); //홈페이지 열기
        document.getElementById("seaPageBtn").addEventListener("click", () => window.open("https://www.badatime.com/")); //홈페이지 열기
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
        const type = site.getElementsByTagName("type")[0]?.textContent || "정보 없음";

        document.getElementById("campsiteName").textContent = site.getElementsByTagName("name")[0]?.textContent || "";
        document.getElementById("platformName").textContent = site.getElementsByTagName("type")[0]?.textContent || "";
        //campsiteName

        // 1. 로그인 필드 제어 (showLoginField)
        const showLogin = site.getElementsByTagName("showLoginField")[0]?.textContent || "N";
        const loginArea = document.getElementById("loginFields");
        if (showLogin === "Y") {
            loginArea.classList.remove("hidden");
        } else {
            loginArea.classList.add("hidden");
        }

        // 2. 자동 예약 체크박스 제어 (isSupportAutoReservation)
        const supportAuto = site.getElementsByTagName("isSupportAutoReservation")[0]?.textContent || "N";
        const autoReserveArea = document.getElementById("autoReserveField");
        if (supportAuto === "Y") {
            autoReserveArea.classList.remove("hidden");
        } else {
            autoReserveArea.classList.add("hidden");
        }

        // 인터파크일 때만 패널 노출
        const authPanel = document.getElementById("interparkAuthPanel");
        if (type === "Interpark" && supportAuto === "Y") {
            authPanel.classList.remove("hidden");
        } else {
            authPanel.classList.add("hidden");
        }

        this.generatorMaxDayOption(site);
        this.generatorSiteChecker(site);

        // [추가] 모바일 대응: 캠핑장 선택 시 상세 패널로 자동 스크롤
        if (window.innerWidth < 768) {
            document.getElementById("reservationPanel").scrollIntoView({ behavior: "smooth" });
        }
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
        const labelArea = document.querySelector("label.border-b");

        // 1. 전체 체크박스 초기화 및 생성
        const oldAllCheck = document.getElementById("allCheckWrapper");
        if (oldAllCheck) oldAllCheck.remove();

        const allCheckWrapper = document.createElement("span");
        allCheckWrapper.id = "allCheckWrapper";
        allCheckWrapper.className = "ml-auto flex items-center text-[10px] font-normal cursor-pointer text-slate-500";
        allCheckWrapper.innerHTML = `
            <input type="checkbox" id="allCheck" class="mr-1 w-3 h-3 accent-indigo-600" checked />
            전체 선택
        `;
        labelArea.classList.add("flex", "items-center", "justify-between");
        labelArea.appendChild(allCheckWrapper);

        siteCheckerContainer.innerHTML = "";

        // 2. 사이트 그룹(groups) 렌더링
        const groupsWrapper = site.getElementsByTagName("groups")[0];
        if (groupsWrapper) {
            const groups = groupsWrapper.getElementsByTagName("group");
            if (groups.length > 0) {
                // 그룹 섹션 타이틀
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
                        <span class="text-xs font-bold text-indigo-700">${groupName}</span>
                    `;
                    siteCheckerContainer.appendChild(label);
                });
            }
        }

        // 3. 개별 사이트(sites) 렌더링
        const sites = site.getElementsByTagName("site");
        if (sites.length > 0) {
            const siteTitle = document.createElement("div");
            siteTitle.className = "col-span-2 text-[10px] font-black text-slate-400 mt-2 border-b border-slate-200 pb-0.5";
            siteTitle.innerHTML = `<i class="fa-solid fa-list mr-1"></i> 사이트 목록`;
            siteCheckerContainer.appendChild(siteTitle);

            Array.from(sites).forEach((element) => {
                const code = element.getAttribute("code") || "";
                const groupAttr = element.getAttribute("group") || ""; // 그룹 속성 확인
                const name = element.textContent || "";

                const label = document.createElement("label");
                label.className = "flex items-center p-1 cursor-pointer hover:bg-slate-100 rounded transition";
                label.innerHTML = `
                    <input type="checkbox" checked class="site-item mr-2 accent-indigo-600" 
                           value="${code}" data-parent-group="${groupAttr}" />
                    <span class="text-xs text-slate-700">${name}</span>
                `;
                siteCheckerContainer.appendChild(label);
            });
        }

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

        //자동 예약
        const autoReserveChecked = document.getElementById("autoReserve").checked;
        const autoReserveValue = autoReserveChecked ? "Y" : "N";

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
        const groupsElement = currentCampsite.getElementsByTagName("groups");
        let hasCategory = "N"; //사이트 그룹의 카테고리 항목 존재 유무 판단.
        if (groupsElement.length > 0) {
            hasCategory = "Y";
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
            hasCategory: hasCategory, //사이트 목록의 상위 그룹이 포함된건지 체크
            autoReserve: autoReserveValue, //자동 예약 수행 여부
            // 체크박스에서 선택된 구역 코드들을 배열(List)로 수집
            //site_codes: Array.from(document.querySelectorAll("#siteCheckerContainer input:checked")).map((cb) => cb.value)
            site_group_codes: Array.from(document.querySelectorAll("#siteCheckerContainer .group-item:checked")).map((cb) => cb.dataset.groupCode),
            site_codes: Array.from(document.querySelectorAll("#siteCheckerContainer .site-item:checked")).map((cb) => cb.value)
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

        let displayStayDay = entry.stay_day;

        // Interpark 타입이고 stay_day에 콤마(,)가 포함된 경우 개수를 세어 "N박"으로 변환
        if (entry.type === "Interpark" && String(entry.stay_day).includes(",")) {
            const dayCount = String(entry.stay_day).split(",").length;
            displayStayDay = `${dayCount}박`;
        } else if (!String(displayStayDay).includes("박")) {
            // 기존 숫자만 들어오는 경우를 위해 '박'이 없으면 붙여줌 (선택 사항)
            displayStayDay = `${displayStayDay}박`;
        }

        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-50 group"; // group 클래스 추가 (호버 시 버튼 강조용)
        tr.innerHTML = `
        <td class="p-2 border-r font-bold">${entry.campsiteName}</td>
        <td class="p-2 border-r text-center">${entry.date}</td>
        <td class="p-2 border-r text-center">${displayStayDay}</td>
        <td class="p-2 border-r text-center font-bold text-indigo-600 MNT-COUNT">0</td>
        <td class="p-2 text-center">
            <div class="flex items-center justify-center space-x-3">
                <span class="text-green-600 font-bold italic text-[10px]">Monitoring..</span>
                <button class="stop-row-btn px-3 py-1 bg-red-500 text-white text-[10px] font-black rounded shadow-sm hover:bg-red-600 transition-colors" 
                        data-uuid="${entry.watchUuid}">
                    중지
                </button>
            </div>
        </td>
    `;
        tr.dataset.watchuuid = entry.watchUuid;

        // 행 클릭 시 하이라이트 유지 (기존 로직)
        tr.onclick = (e) => {
            // 버튼 클릭 시에는 행 클릭 이벤트가 발생하지 않도록 방지
            if (e.target.classList.contains("stop-row-btn")) return;
            this.highlightMonitoringRow(tr);
            this.selectedMonitoringUuid = entry.watchUuid;
        };

        // 중지 버튼에 이벤트 리스너 추가
        const stopBtn = tr.querySelector(".stop-row-btn");
        stopBtn.onclick = (e) => {
            e.stopPropagation(); // 행 클릭 이벤트 전파 방지
            this.stopWatchingRow(entry.watchUuid);
        };

        monitoringList.appendChild(tr);
    },
    stopWatchingRow: async function (watchUuid) {
        if (!watchUuid) return;

        if (confirm("이 감시 작업을 중지하시겠습니까?")) {
            try {
                const response = await fetch(`/api/monitor/stop/${watchUuid}`, {
                    method: "POST"
                });

                if (response.ok) {
                    // 해당 행 삭제
                    const row = document.querySelector(`tr[data-watchuuid="${watchUuid}"]`);
                    if (row) {
                        row.style.transition = "all 0.3s";
                        row.style.opacity = "0";
                        row.style.transform = "translateX(20px)";

                        setTimeout(() => {
                            row.remove();
                            // 목록이 비었는지 확인
                            const monitoringList = document.getElementById("monitoring-list");
                            if (monitoringList.children.length === 0) {
                                monitoringList.innerHTML = `
                                <tr class="hover:bg-slate-50 EMPTY-ROW">
                                    <td class="p-2 text-center text-green-600 font-bold italic" colspan="5">감시 중인 항목이 없습니다.</td>
                                </tr>`;
                            }
                        }, 300);
                    }

                    if (this.selectedMonitoringUuid === watchUuid) {
                        this.selectedMonitoringUuid = null;
                    }

                    Logger.addLog(`감시 중단 완료: ${watchUuid}`);
                }
            } catch (error) {
                console.error("중지 요청 실패:", error);
                alert("서버 통신 오류가 발생했습니다.");
            }
        }
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
    //인터파크 모달창
    renewInterparkSession: async function () {
        if (!confirm("로그인 브라우저를 실행하시겠습니까? \n로그인 완료 후 브라우저 창을 직접 닫아주세요.")) return;

        Logger.addLog("인터파크 로그인 세션 갱신 시작...", "system");

        try {
            const response = await fetch("/api/auth/interpark-session", { method: "POST" });
            const result = await response.json();

            if (result.status === "success") {
                Logger.addLog("세션 저장 완료", "info");
                alert("로그인 세션이 성공적으로 저장되었습니다.");
            }
        } catch (error) {
            Logger.addLog("세션 갱신 실패", "error");
        }
    },
    bindAllCheckEvent: function () {
        const allCheck = document.getElementById("allCheck");
        const groupChecks = document.querySelectorAll(".group-item");
        const siteChecks = document.querySelectorAll(".site-item");

        // 1) 전체 선택 이벤트
        allCheck.addEventListener("change", function () {
            const isChecked = allCheck.checked;
            groupChecks.forEach((gc) => (gc.checked = isChecked));
            siteChecks.forEach((sc) => (sc.checked = isChecked));
        });

        // 2) 그룹 선택 이벤트 (사이트 일괄 제어)
        groupChecks.forEach((gc) => {
            gc.addEventListener("change", function () {
                const groupCode = this.dataset.groupCode;
                const isChecked = this.checked;

                // 해당 그룹 코드를 부모로 가진 사이트들만 필터링하여 체크
                document.querySelectorAll(`.site-item[data-parent-group="${groupCode}"]`).forEach((sc) => {
                    sc.checked = isChecked;
                });

                // 전체 선택 상태 업데이트
                updateAllCheckStatus();
            });
        });

        // 3) 개별 사이트 선택 이벤트 (그룹 및 전체 선택 상태 업데이트)
        siteChecks.forEach((sc) => {
            sc.addEventListener("change", function () {
                const groupCode = this.dataset.parentGroup;

                if (groupCode) {
                    // 동일한 그룹에 속한 전체 사이트 체크박스들
                    const sameGroupSites = document.querySelectorAll(`.site-item[data-parent-group="${groupCode}"]`);
                    // 동일한 그룹에 속한 체크박스 중 현재 '체크된' 것들
                    const checkedGroupSites = document.querySelectorAll(`.site-item[data-parent-group="${groupCode}"]:checked`);
                    // 상위 그룹 헤더 체크박스
                    const groupHeader = document.querySelector(`.group-item[data-group-code="${groupCode}"]`);

                    if (groupHeader) {
                        // [수정 핵심]: 상위 그룹 헤더의 체크 상태는 현재 그룹 내 체크된 사이트가 1개 이상일 때 true가 됩니다.
                        // 자바의 `checkedGroupSites.size() > 0`과 동일한 논리입니다.
                        groupHeader.checked = checkedGroupSites.length > 0;
                    }
                }

                // 전체 선택(#allCheck) 상태도 유기적으로 함께 업데이트합니다.
                updateAllCheckStatus();
            });
        });

        // 4) 공통 상태 업데이트 함수
        function updateAllCheckStatus() {
            const allItems = document.querySelectorAll(".site-item");
            const checkedItems = document.querySelectorAll(".site-item:checked");
            allCheck.checked = allItems.length === checkedItems.length;
        }
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

        logLine.className = "border-b border-gray-800 py-1 opacity-0 transition-opacity duration-300";
        logLine.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;

        // 1. 하단에 로그 추가 (append)
        logContainer.appendChild(logLine);

        // 애니메이션 효과
        setTimeout(() => logLine.classList.remove("opacity-0"), 10);

        // 2. 최대 로그 개수 유지 (오래된 로그는 상단에서 삭제)
        if (logContainer.children.length > this.MAX_LOG_COUNT) {
            logContainer.removeChild(logContainer.firstChild);
        }

        // 3. 자동 스크롤 (사용자가 위로 올려보고 있지 않을 때만 내리는 로직 추가 가능)
        const footer = document.getElementById("main-footer");
        footer.scrollTo({
            top: footer.scrollHeight,
            behavior: "smooth" // 부드럽게 스크롤
        });
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

        const findNextOpenBroswerChecked = document.getElementById("findNextOpenBroswer").checked;
        if (data.link && findNextOpenBroswerChecked) {
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
    <body class="flex flex-col h-screen overflow-hidden" md:overflow-auto">

        <header class="w-full h-14 bg-white border-b shadow-sm flex items-center justify-between px-4 md:px-6 z-20">
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

        <div class="flex flex-col md:flex-row flex-1 overflow-hidden">
            <aside id="asideList" class="w-full md:w-64 bg-white border-b md:border-r flex flex-col shadow-inner h-1/3 md:h-full transition-all">
                <div class="p-3 md:p-4 space-y-4">
                    <div class="space-y-2">
                        <label class="text-[10px] md:text-xs font-black text-indigo-600 uppercase">Camping Platform</label>
                        <select id="platformSelect" class="w-full p-2 text-sm font-bold bg-slate-50 rounded border-slate-300">
                            {% for platform in platform_list %}
                            <option value="{{ platform.filename }}">{{ platform.typeName }}</option>
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

            <main class="flex-1 flex flex-col overflow-hidden bg-slate-50">
                <div class="flex-1 p-2 md:p-4 grid grid-cols-12 gap-2 md:gap-4 overflow-y-auto custom-scrollbar">
                    <section id="reservationPanel" class="col-span-12 lg:col-span-5 bg-white rounded border border-slate-300 flex flex-col shadow-sm">
                        <div class="p-3 border-b bg-slate-50 flex justify-between items-center">
                            <h2 class="font-black text-slate-700 text-sm"><i class="fa-solid fa-pen-to-square mr-1"></i> 예약 정보</h2>
                            <button class="px-4 py-1.5 bg-indigo-600 text-white text-xs font-black rounded-lg hover:bg-indigo-700 shadow-md transition-all" id="watchBtn">감시 시작</button>
                        </div>

                        <div class="px-4 py-2 border-b bg-white flex flex-wrap gap-1">
                            <button class="flex-1 px-2 py-1.5 bg-slate-100 text-slate-600 text-[10px] font-bold rounded hover:bg-slate-200" id="homePageBtn">홈페이지</button>
                            <button class="flex-1 px-2 py-1.5 bg-slate-100 text-slate-600 text-[10px] font-bold rounded hover:bg-slate-200" id="weatherPageBtn">날씨</button>
                            <button class="flex-1 px-2 py-1.5 bg-slate-100 text-slate-600 text-[10px] font-bold rounded hover:bg-slate-200" id="seaPageBtn">바다</button>
                        </div>

                        <div id="interparkAuthPanel" class="mx-4 mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg hidden">
                            <div class="flex items-center justify-between">
                                <span class="text-[11px] font-bold text-amber-800"> <i class="fa-solid fa-key mr-1"></i> 로그인 세션이 만료되었나요? </span>
                                <button onclick="Comp.renewInterparkSession()" class="px-2 py-1 bg-amber-600 text-white text-[10px] font-black rounded hover:bg-amber-700 transition shadow-sm">브라우저 열기 & 로그인</button>
                            </div>
                            <p class="text-[10px] text-amber-600 mt-1.5 leading-tight">
                                * 버튼 클릭 후 열리는 창에서 로그인 완료 후, <br />
                                &nbsp;&nbsp;메인 화면이 나오면 브라우저 창을 <b>직접 닫아주세요.</b>
                            </p>
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
                                        <option value="30" selected>30초</option>
                                        <option value="10">10초</option>
                                    </select>
                                </div>
                                <div id="loginFields" class="hidden space-y-3 pt-2">
                                    <!-- 기본적으로 숨김 -->
                                    <div class="flex items-center">
                                        <label class="w-24 font-bold text-slate-600 text-xs">아이디</label>
                                        <input type="text" id="userId" class="flex-1 p-1 border rounded text-xs" />
                                    </div>
                                    <div class="flex items-center">
                                        <label class="w-24 font-bold text-slate-600 text-xs">비밀번호</label>
                                        <input type="password" id="userPw" class="flex-1 p-1 border rounded text-xs" />
                                    </div>
                                </div>

                                <div class="flex items-center justify-end space-x-4">
                                    <!-- space-x-4 추가로 간격 조절 -->
                                    <label class="flex items-center font-bold text-slate-600 text-xs cursor-pointer">
                                        <input type="checkbox" checked id="findNextRun" class="mr-1 w-4 h-4 accent-indigo-600" />
                                        검색후 감시 종료
                                    </label>

                                    <label class="flex items-center font-bold text-slate-600 text-xs cursor-pointer">
                                        <input type="checkbox" checked id="findNextOpenBroswer" class="mr-1 w-4 h-4 accent-indigo-600" />
                                        검색후 브라우저 열기
                                    </label>

                                    <!-- 기존 자동 예약 요청 -->
                                    <div id="autoReserveField" class="hidden">
                                        <label class="flex items-center font-bold text-red-600 text-xs cursor-pointer">
                                            <input type="checkbox" id="autoReserve" name="autoReserve" class="mr-1 w-4 h-4" />
                                            자동 예약 요청
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section class="col-span-12 lg:col-span-7 bg-white rounded border border-slate-300 flex flex-col shadow-sm">
                        <div class="p-3 border-b bg-slate-50">
                            <h2 class="font-black text-slate-700 text-sm">감시 정보</h2>
                        </div>
                        <div class="flex-1 overflow-x-auto">
                            <table class="w-full text-[11px] md:text-xs text-left border-collapse min-w-[500px]">
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
                        <!--
                        <div class="p-3 border-t bg-slate-50 flex justify-center">
                            <button class="px-6 py-2 bg-red-50 border border-red-200 text-red-600 font-black rounded hover:bg-red-100 transition text-sm" id="stopWatchBtn">감지 중지</button>
                        </div>
                        -->
                    </section>
                </div>

                <div id="footer-resizer" class="hidden md:block h-1 bg-slate-700 hover:bg-indigo-500 cursor-ns-resize"></div>
                <footer id="main-footer" class="h-32 md:h-44 bg-[#1e1e1e] text-[#d4d4d4] p-3 font-mono text-[10px] overflow-y-auto">
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
                <li class="flex items-center p-2 hover:bg-slate-50 rounded cursor-pointer transition" id="settingConfigBtn"><i class="fa-solid fa-gear w-8 text-indigo-500"></i><span>환경 설정</span></li>
                <li class="flex items-center p-2 hover:bg-slate-50 rounded cursor-pointer transition" id="telegramConfigBtn"><i class="fa-solid fa-bell w-8 text-indigo-500"></i><span>텔레그램 봇 연동</span></li>
                <li class="flex items-center p-2 hover:bg-slate-50 rounded cursor-pointer transition border-t pt-4 mt-4"><i class="fa-solid fa-circle-info w-8 text-slate-400"></i><span>도움말 및 정보</span></li>
            </ul>
        </div>
        <div id="overlay" onclick="toggleMenu()" class="fixed inset-0 bg-black/30 backdrop-blur-sm z-20 hidden"></div>
        <div id="toast-container" class="fixed bottom-5 right-5 z-50 flex flex-col gap-2"></div>

        <!-- 텔레그램 연동 화면 -->
        <div id="telegramModal" class="fixed inset-0 bg-black/50 hidden z-50 flex items-center justify-center backdrop-blur-sm">
            <div class="bg-white p-6 rounded-xl w-96 shadow-2xl border border-slate-200">
                <h2 class="text-lg font-black text-slate-800 italic mb-6">TELEGRAM BOT SETTING</h2>
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <label class="text-[10px] font-black text-indigo-600">사용 여부</label>
                        <select id="tgUseYn" class="text-xs border rounded p-1">
                            <option value="Y">사용 (Y)</option>
                            <option value="N">미사용 (N)</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-[10px] font-black text-indigo-600 uppercase">Bot Token</label>
                        <input type="password" id="tgToken" class="w-full p-2 border rounded text-xs font-mono" />
                    </div>
                    <div>
                        <label class="text-[10px] font-black text-indigo-600 uppercase">Chat IDs (콤마구분)</label>
                        <textarea id="tgChatIds" class="w-full p-2 border rounded text-xs font-mono h-20" placeholder="12345, 67890"></textarea>
                    </div>
                </div>
                <div class="flex justify-end mt-8 space-x-2">
                    <button onclick="closeTgModal()" class="px-4 py-2 text-xs font-bold text-slate-400">취소</button>
                    <button onclick="Comp.saveTgSettings()" class="px-6 py-2 text-xs font-black bg-indigo-600 text-white rounded-lg">저장</button>
                </div>
            </div>
        </div>
        <!-- 텔레그램 연동 화면 -->

        <!-- 환경 설정 모달 -->
        <div id="settingsModal" class="fixed inset-0 bg-black/50 hidden z-50 flex items-center justify-center backdrop-blur-sm">
            <div class="bg-white p-6 rounded-xl w-[500px] shadow-2xl border border-slate-200">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-lg font-black text-slate-800 italic">SYSTEM CONFIGURATION</h2>
                    <button onclick="Comp.closeSettingsModal()" class="text-slate-400 hover:text-slate-800"><i class="fa-solid fa-xmark text-xl"></i></button>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm" id="infoSettingsForm">
                    <!-- JS에서 동적 생성하거나 직접 작성 -->
                    <div class="col-span-2"><label class="text-[10px] font-black text-indigo-600 uppercase">이메일</label> <input type="text" name="email" class="w-full p-2 border rounded text-xs" /></div>
                    <div><label class="text-[10px] font-black text-indigo-600 uppercase">이름</label> <input type="text" name="name" class="w-full p-2 border rounded text-xs" /></div>
                    <div><label class="text-[10px] font-black text-indigo-600 uppercase">닉네임</label> <input type="text" name="nickname" class="w-full p-2 border rounded text-xs" /></div>
                    <div><label class="text-[10px] font-black text-indigo-600 uppercase">생년월일(YYMMDD)</label> <input type="text" name="birth_date" class="w-full p-2 border rounded text-xs" /></div>
                    <div><label class="text-[10px] font-black text-indigo-600 uppercase">전화번호</label> <input type="text" name="phone" class="w-full p-2 border rounded text-xs" /></div>
                    <div><label class="text-[10px] font-black text-indigo-600 uppercase">차량번호</label> <input type="text" name="car_number" class="w-full p-2 border rounded text-xs" /></div>
                    <div class="flex space-x-2">
                        <div class="flex-1"><label class="text-[10px] font-black text-indigo-600 uppercase">성인</label> <input type="number" name="member_adult" class="w-full p-2 border rounded text-xs" /></div>
                        <div class="flex-1"><label class="text-[10px] font-black text-indigo-600 uppercase">학생</label> <input type="number" name="member_teen" class="w-full p-2 border rounded text-xs" /></div>
                        <div class="flex-1"><label class="text-[10px] font-black text-indigo-600 uppercase">미취학</label> <input type="number" name="member_child" class="w-full p-2 border rounded text-xs" /></div>
                    </div>
                </div>
                <div class="flex justify-end mt-8 space-x-2">
                    <button onclick="Comp.closeSettingsModal()" class="px-4 py-2 text-xs font-bold text-slate-400 hover:bg-slate-50 rounded-lg transition">취소</button>
                    <button onclick="Comp.saveInfoSettings()" class="px-6 py-2 text-xs font-black bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md transition">설정 저장</button>
                </div>
            </div>
        </div>
        <!-- 환경 설정 모달 종료 -->

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

### [/camping-scanner/app/main.py]

```python
import os
import sys
import yaml
import signal
import webbrowser
import xml.etree.ElementTree as ET
from threading import Timer, Thread  # Thread 추가 임포트
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi import Request, HTTPException
from datetime import datetime

from core.config_loader import get_resource_path, get_external_path

from core.logger import log_queue, logger
from core.config_loader import CONFIG
import httpx
import asyncio

from platforms.thankq import ThankQMonitor
from platforms.interpark import InterparkMonitor
from platforms.mirihae import MirihaeMonitor
from platforms.maketicket import MaketicketMonitor
from platforms.xticket import XticketMonitor
from platforms.campingtalk import CampingtalkQMonitor
from platforms.camplink import CamplinkMonitor
from platforms.dugsan import DugsanMonitor
from platforms.pubcamping import PubcampingMonitor

from core.tray_icon import TrayIcon

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.scheduler import scheduler, start_scheduler
from core.websocket_manager import ws_manager

from core.config_loader import load_full_config, save_config
from core.browser_handler import get_browser_path

from playwright.async_api import async_playwright

import logging

try:
    path = get_browser_path()
    print(f"[*] 브라우저 경로 설정 완료: {path}")
except Exception as e:
    print(f"[!] 브라우저 경로 설정 실패: {e}")

# 전역 객체
app = FastAPI()
tray_manager = None #트레이 관리자
active_monitors = {} #현재 실행 중인 감시 정보 저장소 (메모리)


@app.on_event("startup")
async def start_demo_logging():

    start_scheduler()

    async def simulate_logging():
        while True:
            logger.info("서버가 정상 기동중...")
            await asyncio.sleep(60 * 3)
    asyncio.create_task(simulate_logging())

@app.on_event("shutdown")
async def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[*] 스케줄러가 성공적으로 종료되었습니다.")

def run_server():
    """FastAPI 서버를 실행하는 함수 (백그라운드 스레드용)"""
    target_port = int(CONFIG['server']['port'])
    target_host = CONFIG['server']['host']
    uvicorn.run(app, host="127.0.0.1", port=target_port, log_config=None, workers=1)
    #uvicorn.run("main:app", host="127.0.0.1", port=target_port, log_config=None, reload=True)


def stop_server():
    """종료 콜백"""
    os.kill(os.getpid(), signal.SIGTERM)

# 1. CORS 설정 (가장 유력한 에러 원인 해결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 로그를 가로챌 큐와 핸들러 (Java의 Appender 역할)
log_queue = asyncio.Queue()

class WSLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        # 루프가 실행 중일 때만 큐에 넣음
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(log_queue.put(msg))
        except RuntimeError:
            pass

# 로거 세팅
logger = logging.getLogger("camping")
logger.setLevel(logging.INFO)
handler = WSLogHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(handler)

# [경로 설정]
def get_base_path():
    """
    프로젝트 루트 경로를 반환합니다.
    - 배포 시: .exe 파일이 있는 폴더
    - 개발 시: app/ 폴더의 부모 폴더 (camping-scanner/)
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)

    # 현재 파일(main.py)의 부모(app)의 부모(root) 경로를 계산
    current_file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_file_path) # app/
    root_dir = os.path.dirname(parent_dir)         # camping-scanner/
    return root_dir


def load_campsites():
    """
    프로젝트 루트의 data/ 폴더에서 XML 파일들을 읽어
    { '플랫폼명': ['캠핑장1', '캠핑장2'] } 구조로 반환합니다.
    """
    # [참고] Java의 ResourceLoader처럼 물리적 경로 계산
    base_path = get_base_path()
    data_dir = os.path.join(base_path, "data")

    # 전달해주신 파일명 리스트 매핑
    campsite_files = {
        "인터파크": "interpark-campsite.xml",
        "메이킹티켓": "maketicket-campsite.xml",
        "X티켓": "xticket-campsite.xml",
        "캠프링크": "camplink-campsite.xml",
        "숲나들e": "foresttrip-campsite.xml",
        "땡큐캠핑": "thankqcamping-campsite.xml",
        "캠핑톡": "campingtalk-campsite.xml",
        "네이버": "naver-campsite.xml",
        "캠핏": "camfit-campsite.xml",
        "미리해": "mirihae-campsite.xml",
        "기타": "etc-campsite.xml"
    }

    result = {}

    # 1. data 폴더 존재 유무 확인 (Java의 익셉션 핸들링 대신 가벼운 체크)
    if not os.path.exists(data_dir):
        print(f"[!] 데이터 폴더를 찾을 수 없습니다: {data_dir}")
        return result

    for platform, filename in campsite_files.items():
        file_path = os.path.join(data_dir, filename)
        result[platform] = []

        if os.path.exists(file_path):
            try:
                # XML 파싱 시작 (DOM 파서와 유사)
                tree = ET.parse(file_path)
                root = tree.getroot()

                # <campsite> 태그 내부의 <name> 추출
                for site in root.findall('campsite'):
                    name_node = site.find('name')
                    if name_node is not None and name_node.text:
                        result[platform].append(name_node.text.strip())
            except Exception as e:
                print(f"[!] {filename} 파싱 에러: {e}")
        else:
            # 파일이 없으면 빈 리스트 유지
            print(f"[-] 파일을 찾을 수 없음 (무시됨): {filename}")

    return result

# [설정 로드] - 호출 시점에 읽도록 수정
def load_config():
    """외부 config/config.yaml 로드"""
    base_path = get_base_path()
    # base_path가 이미 프로젝트 루트이므로 바로 config 폴더 결합
    config_path = os.path.join(base_path, "config", "config.yaml")

    print(f"[*] 설정 파일을 찾는 중: {config_path}") # 경로 확인용 출력

    default_config = {"server": {"port": 8000, "host": "127.0.0.1"}}

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                return content if content else default_config
        except Exception as e:
            print(f"[!] 설정 로드 실패: {e}")
    else:
        print(f"[!] 설정 파일을 찾지 못했습니다: {config_path}")

    return default_config

def get_xml_content(filename: str):
    """data/ 폴더에서 XML 파일의 원문을 문자열로 읽어옵니다."""
    # os.path.join은 Java의 Paths.get()과 유사한 역할을 합니다.
    file_path = os.path.join("data", filename)

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# static 폴더 경로 설정 (빌드 대응)
static_path = get_resource_path(os.path.join("app", "static"))
app.mount("/static", StaticFiles(directory=static_path), name="static")

template_path = get_resource_path(os.path.join("app", "templates"))
templates = Jinja2Templates(directory=template_path)

# [브라우저 오픈] - 호출될 때 config를 다시 확인
def open_browser(host, port):
    webbrowser.open(f"http://{host}:{port}")

def get_platform_info():
    """
    data 폴더 내의 모든 *-campsite.xml 파일을 읽어
    typeOrder 기준 오름차순으로 정렬된 리스트를 반환합니다.
    """
    base_path = get_base_path() # 기존에 정의하신 경로 계산 함수 사용
    data_dir = os.path.join(base_path, "data")
    platforms = []

    if not os.path.exists(data_dir):
        return platforms

    for filename in os.listdir(data_dir):
        if filename.endswith("-campsite.xml"):
            file_path = os.path.join(data_dir, filename)
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                # <typeName> 및 <typeOrder> 추출
                type_name = root.findtext('typeName', '이름 없음').strip()
                # typeOrder가 없으면 가장 뒤로 보냄 (기본값 999)
                type_order = int(root.findtext('typeOrder', '999').strip())

                platforms.append({
                    "filename": filename,
                    "typeName": type_name,
                    "typeOrder": type_order
                })
            except Exception as e:
                logger.error(f"[!] {filename} 파싱 에러: {e}")

    # typeOrder 기준으로 오름차순 정렬 (1이 가장 상단)
    platforms.sort(key=lambda x: x['typeOrder'])
    return platforms

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    sorted_platforms = get_platform_info()

    campsite_list = load_campsites()

    # 이제 templates 폴더 내부의 'index.html'을 찾습니다.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "campsites": campsite_list, "platform_list": sorted_platforms, "port": CONFIG['server']['port'] }
    )

@app.get("/gateway/gugu", response_class=HTMLResponse)
async def index(request: Request):

    sorted_platforms = get_platform_info()

    campsite_list = load_campsites()

    # 이제 templates 폴더 내부의 'index.html'을 찾습니다.
    return templates.TemplateResponse(
        request=request,
        name="gugu_gateway.html",
        context={"request": request, "port": CONFIG['server']['port'] }
    )

# API: 플랫폼 변경 시 호출될 엔드포인트 (AJAX용)
@app.get("/api/campsites/{filename}", response_class=PlainTextResponse)
async def get_campsite_list(filename: str):

    # data/ 폴더의 경로를 빌드 환경에 맞게 계산
    file_path = get_external_path(os.path.join("data", filename))

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitor/start")
async def start_monitor(params: dict = Body(...), background_tasks: BackgroundTasks = None):

    print(f"[*] 요청 수신: {params}")

    logger.info(f"Monitor started for: {params.get('camp_id')}")

    """
    request_data: JSON Body가 Python dict(Map)으로 자동 매핑됨
    예: {"type": "THANKQ", "camp_id": "3446", "date": "2026-04-28", "site_codes": ["14147"]}
    """
    platform_type = params.get("type")
    interval = int(params.get("requestInterval", 60))
    job_id = params.get("watchUuid")

    # 전략 패턴을 이용한 인스턴스 생성

    if platform_type == "Thankqcamping":
        monitor = ThankQMonitor()
    elif platform_type == "Interpark":
        monitor = InterparkMonitor()
    elif platform_type == "Mirihae":
        monitor = MirihaeMonitor()
    elif platform_type == "Maketicket":
        monitor = MaketicketMonitor()
    elif platform_type == "Xticket":
        monitor = XticketMonitor()
    elif platform_type == "Campingtalk":
        monitor = CampingtalkQMonitor()
    elif platform_type == "Camplink":
        monitor = CamplinkMonitor()
    elif platform_type == "Dugsan":
            monitor = DugsanMonitor()
    elif platform_type == "Pubcamping":
            monitor = PubcampingMonitor()

    else:
        return {"status": "error", "message": "지원하지 않는 플랫폼입니다."}

    # 인터벌의 20% 정도를 무작위 변동폭(jitter)으로 설정
    # 예: 60초 설정 시, 60 ± 12초 사이에서 랜덤하게 실행됨
    dynamic_jitter = int(interval * 0.2)

    # 백그라운드에서 감시 시작 (Spring의 @Async와 유사)
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        return {"status": "success", "message": f"이미 실행중인 작업입니다."}

    # 런타임에 스케줄링 작업 등록 (Spring의 dynamic scheduling과 유사)
    scheduler.add_job(
        monitor.check_availability,  # 실행할 함수
        'interval',
        seconds=interval,
        jitter=dynamic_jitter,       # 실행 시점마다 무작위 지연 추가
        args=[params],               # 함수에 넘길 파라미터(Map/dict)
        id=job_id,
        next_run_time=datetime.now() # 즉시 실행
    )

    # [추가] 서버 메모리에 감시 정보 저장
    active_monitors[job_id] = params

    return {"status": "success", "message": f"{platform_type} 감시 시작"}

@app.post("/api/monitor/stop/{watch_uuid}")
async def stop_monitor(watch_uuid: str):
    try:

        # 등록된 스케줄러 작업 삭제 (Java의 scheduler.cancel(jobId) 역할)
        scheduler.remove_job(watch_uuid)
        logger.info(f"Monitor stopped for: {watch_uuid}")

        # 저장소에서도 삭제
        if watch_uuid in active_monitors:
            del active_monitors[watch_uuid]

        return {"status": "success", "message": f"Job {watch_uuid} stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def monitor_loop(monitor, params):
    import asyncio
    while True:
        found = await monitor.check_availability(params)
        if found:
            # 알림 발송 로직 호출
            print("빈자리 발견!")
            break
        await asyncio.sleep(60 * 5) # 5분 대기

@app.get("/api/monitor/list")
async def get_monitor_list():
    # 현재 스케줄러에서 실제로 돌아가고 있는 작업만 필터링하여 반환
    running_jobs = []
    for job_id, params in active_monitors.items():
        if scheduler.get_job(job_id):
            running_jobs.append(params)
    return running_jobs

@app.post("/api/shutdown")
async def shutdown():
    logger.info("[*] 애플리케이션 종료 요청을 받았습니다.")

    def kill_process():
        # 윈도우와 리눅스 모두에서 작동하도록 SIGINT(Ctrl+C 효과)를 먼저 시도하고 안되면 SIGTERM을 보냅니다.
        try:
            # 윈도우의 경우 CTRL_C_EVENT를 사용할 수도 있지만 SIGTERM이 일반적입니다.
            os.kill(os.getpid(), signal.SIGTERM)
        except Exception as e:
            # 강제 종료
            os._exit(0)

    Timer(1.0, kill_process).start()
    return {"status": "success", "message": "프로그램을 종료합니다."}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 큐에 로그가 들어올 때까지 대기 (Java의 queue.take())
            log_msg = await log_queue.get()
            await websocket.send_text(log_msg)
    except WebSocketDisconnect:
        print("로그 웹소켓 연결 종료")

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    try:
        # 2. 중요: 무한 루프를 통해 연결 상태를 유지합니다.
        # 이 루프가 있어야 함수가 종료되지 않고 '감시' 상태를 유지합니다.
        while True:
            # 클라이언트로부터 메시지를 기다림 (연결 유지를 위한 통신)
            # 수신할 데이터가 없더라도 이 대기 상태가 필요합니다.
            data = await websocket.receive_text()

    except WebSocketDisconnect:
        # 3. 브라우저 창을 닫으면 리스트에서 제거
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"웹소켓 에러: {e}")
        ws_manager.disconnect(websocket)


@app.get("/api/interpark/play-seq")
async def proxy_interpark_api(goodsCode: str, start_date: str, end_date: str):
    url = f"https://api-ticketfront.interpark.com/v1/goods/{goodsCode}/playSeq"
    params = {
        "goodsCode": goodsCode,
        "startDate": start_date,
        "endDate": end_date,
        "isBookableDate": "true",
        "page": 1,
        "pageSize": 1550
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": f"https://tickets.interpark.com/goods/{goodsCode}"
    }

    async with httpx.AsyncClient() as client:
        # 서버가 대신 인터파크에 물어봅니다.
        response = await client.get(url, params=params, headers=headers)
        return response.json()

@app.post("/api/settings/telegram")
async def save_telegram_settings(settings: dict = Body(...)):
    """config.yaml 파일의 텔레그램 설정을 업데이트함"""
    try:
        from core.config_loader import save_config
        # 기존 CONFIG 객체 업데이트 및 파일 저장
        save_config({"telegram": settings})
        return {"status": "success", "message": "설정이 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 환경 설정 정보 조회 API
@app.get("/api/settings")
async def get_settings():
    """현재 config.yaml의 텔레그램 및 Info 설정을 반환합니다."""
    return {
        "telegram": CONFIG.get("telegram", {"use_yn": "N", "token": "", "chat_ids": []}),
        "info": CONFIG.get("info", {})
    }

@app.post("/api/settings/telegram")
async def save_telegram(settings: dict = Body(...)):
    # settings 예: {"use_yn": "Y", "token": "...", "chat_ids": ["id1", "id2"]}
    save_config({"telegram": settings})
    logger.info("[*] 텔레그램 설정이 업데이트되었습니다.")
    return {"status": "success"}

@app.post("/api/settings/info")
async def save_info(info: dict = Body(...)):
    save_config({"info": info})
    logger.info("[*] 시스템 환경설정이 업데이트되었습니다.")
    return {"status": "success"}

@app.post("/api/auth/interpark-session")
async def create_interpark_session():
    async with async_playwright() as p:
        # 1. 브라우저 실행 (사용자가 봐야 하므로 headless=False)
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context()
        page = await context.new_page()

        # 브라우저가 닫혔는지 확인할 플래그
        closed_event = asyncio.Event()

        # 사용자가 브라우저 탭이나 창을 닫을 때 실행될 콜백
        async def on_close(p):
            print("[*] 사용자가 브라우저를 닫았습니다. 세션을 저장합니다.")
            # 창이 닫히기 직전 혹은 직후에 상태 저장
            await context.storage_state(path="interpark_auth.json")
            closed_event.set()

        page.on("close", on_close)

        # 2. 인터파크 상품 페이지로 이동
        await page.goto("https://nol.interpark.com/ticket")

        # 3. 브라우저가 닫힐 때까지 대기 (사용자가 로그인을 완료하고 직접 브라우저를 닫음)
        # 또는 특정 성공 페이지 URL이 나타날 때까지 대기하도록 설정 가능
        print("[*] 사용자의 로그인 작업 대기 중...")

        # 3. 사용자가 창을 닫을 때까지 비동기로 무한 대기
        await closed_event.wait()

        await browser.close()

        return {"status": "success", "message": "interpark_auth.json 저장 완료"}

def check_expiration():
    # 현재 시간 확인
    expiration_date = datetime(2026, 7, 30)

    if datetime.now() > expiration_date:
        # 2. strptime -> strftime으로 수정하여 날짜 객체를 문자열로 포맷팅합니다.
        formatted_date = expiration_date.strftime('%Y-%m-%d')
        print(f"[!] 프로그램 사용 기간이 만료되었습니다. (종료일: {formatted_date})")
        sys.exit()  # 프로그램 강제 종료

if __name__ == "__main__":

    # 앱 시작 시 호출
    check_expiration()

    # 브라우저 환경 설정
    get_browser_path()

    target_port = int(CONFIG['server']['port'])
    target_host = CONFIG['server']['host']

    # 2. FastAPI 서버를 백그라운드 스레드에서 시작
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()

    Timer(2.0, open_browser, args=["127.0.0.1", target_port]).start()

    # 3. 트레이 아이콘을 메인 스레드에서 실행 (Mac 오류 해결의 핵심)
    tray_manager = TrayIcon("127.0.0.1", target_port, stop_server)
    tray_manager.run()

    print(f"[*] Starting server on {target_host}:{target_port}")

    tray_manager.run()



```
