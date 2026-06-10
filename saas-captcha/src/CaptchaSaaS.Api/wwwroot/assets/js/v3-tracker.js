/**
 * Captcha V3 - Client-side Interaction & Fingerprint Tracker
 */
class CaptchaV3Tracker {
    constructor() {
        this.mouseActions = [];
        this.keyActions = [];
        this.clickActions = [];
        this.scrollActions = [];
        this.startTime = Date.now();
        
        // Cấu hình giới hạn ghi log
        this.maxMousePoints = 150;
        this.maxKeyActions = 50;
        this.maxClicks = 10;
        this.maxScrolls = 20;
        this.mouseThrottleMs = 15; // Lưu điểm chuột sau mỗi 15ms
        this.lastMouseTime = 0;
        
        this.initListeners();
    }

    initListeners() {
        // Ghi nhận di chuyển chuột
        document.addEventListener('mousemove', (e) => {
            const now = Date.now();
            if (now - this.lastMouseTime > this.mouseThrottleMs) {
                if (this.mouseActions.length < this.maxMousePoints) {
                    this.mouseActions.push({
                        x: e.clientX,
                        y: e.clientY,
                        t: now - this.startTime
                    });
                }
                this.lastMouseTime = now;
            }
        });

        // Ghi nhận click chuột
        document.addEventListener('mousedown', (e) => {
            if (this.clickActions.length < this.maxClicks) {
                let targetId = e.target.id || e.target.className || e.target.tagName;
                if (typeof targetId === 'string' && targetId.length > 50) {
                    targetId = targetId.substring(0, 50);
                }
                this.clickActions.push({
                    x: e.clientX,
                    y: e.clientY,
                    target: String(targetId),
                    t: Date.now() - this.startTime
                });
            }
        });

        // Ghi nhận gõ bàn phím
        document.addEventListener('keydown', (e) => {
            if (this.keyActions.length < this.maxKeyActions) {
                this.keyActions.push({
                    key: e.key,
                    type: 'keydown',
                    t: Date.now() - this.startTime
                });
            }
        });

        document.addEventListener('keyup', (e) => {
            if (this.keyActions.length < this.maxKeyActions) {
                this.keyActions.push({
                    key: e.key,
                    type: 'keyup',
                    t: Date.now() - this.startTime
                });
            }
        });

        // Ghi nhận cuộn trang
        window.addEventListener('scroll', () => {
            const now = Date.now();
            if (this.scrollActions.length < this.maxScrolls) {
                this.scrollActions.push({
                    scrollTop: window.scrollY || document.documentElement.scrollTop,
                    t: now - this.startTime
                });
            }
        }, { passive: true });
    }

    // Sinh dấu vân tay Canvas
    getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 200;
            canvas.height = 50;
            const ctx = canvas.getContext('2d');
            if (!ctx) return 'canvas_unsupported';
            
            // Vẽ các khối màu và chữ với font cụ thể
            ctx.textBaseline = "top";
            ctx.font = "14px 'Arial'";
            ctx.textBaseline = "alphabetic";
            ctx.fillStyle = "#f60";
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = "#069";
            ctx.fillText("CaptchaResearch, v3.0 \uD83D\uDE03", 2, 15);
            ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
            ctx.fillText("CaptchaResearch, v3.0 \uD83D\uDE03", 4, 17);
            
            const dataUrl = canvas.toDataURL();
            
            // Hàm băm đơn giản (djb2 hash) chuỗi base64 của canvas
            let hash = 0;
            for (let i = 0; i < dataUrl.length; i++) {
                const char = dataUrl.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32bit integer
            }
            return Math.abs(hash).toString(16);
        } catch (e) {
            return 'canvas_error';
        }
    }

    // Thu thập toàn bộ telemetry
    getTelemetry() {
        const fp = {
            userAgent: navigator.userAgent,
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            webdriver: !!navigator.webdriver,
            canvasHash: this.getCanvasFingerprint(),
            timezoneOffset: new Date().getTimezoneOffset(),
            languages: navigator.languages ? navigator.languages.join(',') : (navigator.language || ''),
            isHeadless: this.checkHeadless()
        };

        return {
            mouseActions: this.mouseActions,
            keyActions: this.keyActions,
            clickActions: this.clickActions,
            scrollActions: this.scrollActions,
            fingerprint: fp
        };
    }

    checkHeadless() {
        // Một số cách cơ bản kiểm tra Headless Chrome ở Client
        const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
        if (isChrome) {
            // Chrome headless thường không có Plugins
            if (navigator.plugins && navigator.plugins.length === 0) {
                return true;
            }
            // navigator.languages không được định nghĩa hoặc trống trong các phiên bản headless cũ
            if (!navigator.languages || navigator.languages.length === 0) {
                return true;
            }
        }
        
        // Kiểm tra biến window đặc trưng của các công cụ test tự động
        if (window._phantom || window.callPhantom || window.__phantomas) return true;
        if (window.Buffer) return true; // Node.js environments (jsdom)
        if (document.documentElement.getAttribute('webdriver')) return true;
        
        return false;
    }

    // Reset lại bộ đệm sự kiện
    reset() {
        this.mouseActions = [];
        this.keyActions = [];
        this.clickActions = [];
        this.scrollActions = [];
        this.startTime = Date.now();
    }
}

// Khởi tạo đối tượng toàn cục
window.captchaV3Tracker = new CaptchaV3Tracker();
