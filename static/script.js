/**
 * 智能图片检测应用 — 前端交互逻辑
 * ========================================
 * 这个文件负责网页上所有的"交互"：
 * - 点击/拖拽上传图片
 * - 点击"开始检测"按钮
 * - 显示检测结果和标注图片
 */

// ========== 1. 获取页面上的关键元素 ==========
// 这些是我们要操作的 HTML 元素
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const previewSection = document.getElementById("previewSection");
const originalPreview = document.getElementById("originalPreview");
const detectBtn = document.getElementById("detectBtn");
const loading = document.getElementById("loading");
const emptyState = document.getElementById("emptyState");
const resultContent = document.getElementById("resultContent");
const resultImage = document.getElementById("resultImage");
const statsSummary = document.getElementById("statsSummary");
const objectList = document.getElementById("objectList");

// 用来存用户选择的文件
let selectedFile = null;

// ========== 2. 上传区域交互 ==========

// 点击上传区域 → 弹出文件选择框
dropZone.addEventListener("click", () => {
    fileInput.click();
});

// 用户选择了文件
fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
});

// 拖拽文件到上传区域
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();           // 阻止浏览器默认行为（否则会直接打开文件）
    dropZone.classList.add("drag-over");  // 加个高亮样式
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");  // 移除高亮样式
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) {
        handleFile(file);
    }
});

// ========== 3. 处理上传的文件 ==========
function handleFile(file) {
    // 检查文件类型：只允许图片
    if (!file.type.startsWith("image/")) {
        alert("请上传图片文件（JPG、PNG、WEBP 等）！");
        return;
    }

    selectedFile = file;

    // 显示图片预览
    const reader = new FileReader();
    reader.onload = (e) => {
        originalPreview.src = e.target.result;
        previewSection.style.display = "block";
    };
    reader.readAsDataURL(file);

    // 启用检测按钮
    detectBtn.disabled = false;

    // 清空之前的结果
    resetResults();
}

// ========== 4. 点击"开始检测"按钮 ==========
detectBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    // 显示加载动画，禁用按钮
    loading.style.display = "block";
    detectBtn.disabled = true;
    detectBtn.textContent = "⏳ 检测中...";

    try {
        // -------- 步骤1：获取检测信息 --------
        const formData = new FormData();
        formData.append("image", selectedFile);

        const infoResponse = await fetch("/detect/info", {
            method: "POST",
            body: formData,
        });

        if (!infoResponse.ok) {
            throw new Error("检测失败");
        }

        const infoResult = await infoResponse.json();

        // -------- 步骤2：获取标注图片 --------
        const imageFormData = new FormData();
        imageFormData.append("image", selectedFile);

        const imageResponse = await fetch("/detect", {
            method: "POST",
            body: imageFormData,
        });

        if (!imageResponse.ok) {
            throw new Error("图片处理失败");
        }

        // 把返回的图片数据转成可显示的 URL
        const imageBlob = await imageResponse.blob();
        const imageUrl = URL.createObjectURL(imageBlob);

        // -------- 步骤3：显示结果 --------
        displayResults(infoResult, imageUrl);

    } catch (error) {
        alert("检测出错：" + error.message);
        console.error(error);
    } finally {
        // 恢复按钮状态
        loading.style.display = "none";
        detectBtn.disabled = false;
        detectBtn.textContent = "🚀 开始检测";
    }
});

// ========== 5. 显示检测结果 ==========
function displayResults(info, imageUrl) {
    // 隐藏空状态，显示结果区
    emptyState.style.display = "none";
    resultContent.style.display = "block";

    // 显示标注图片
    resultImage.src = imageUrl;

    // 显示统计摘要
    if (info.count > 0) {
        statsSummary.textContent = `✅ 共检测到 ${info.count} 个物体`;
    } else {
        statsSummary.textContent = "😕 未检测到物体，请换一张图片试试";
    }

    // 显示物体列表
    objectList.innerHTML = "";
    info.objects.forEach((obj) => {
        const li = document.createElement("li");
        li.innerHTML = `
            <span class="object-name">${getEmoji(obj.name_en)} ${obj.name}</span>
            <span class="object-conf">${obj.confidence}%</span>
        `;
        objectList.appendChild(li);
    });
}

// ========== 6. 重置结果 ==========
function resetResults() {
    emptyState.style.display = "block";
    resultContent.style.display = "none";
    resultImage.src = "";
    statsSummary.textContent = "";
    objectList.innerHTML = "";
}

// ========== 7. 辅助：给物体加 emoji ==========
function getEmoji(nameEn) {
    const emojiMap = {
        "person": "🧑", "car": "🚗", "bicycle": "🚲",
        "motorcycle": "🏍️", "airplane": "✈️", "bus": "🚌",
        "train": "🚆", "truck": "🚛", "boat": "🚢",
        "dog": "🐕", "cat": "🐱", "bird": "🐦",
        "horse": "🐴", "sheep": "🐑", "cow": "🐄",
        "elephant": "🐘", "bear": "🐻", "zebra": "🦓",
        "giraffe": "🦒", "backpack": "🎒", "umbrella": "☂️",
        "cell phone": "📱", "laptop": "💻", "book": "📖",
        "pizza": "🍕", "cake": "🎂", "apple": "🍎",
        "banana": "🍌", "orange": "🍊", "bottle": "🍾",
        "cup": "☕", "wine glass": "🍷", "chair": "🪑",
        "bed": "🛏️", "tv": "📺", "clock": "🕐",
        "sports ball": "⚽", "kite": "🪁", "teddy bear": "🧸",
    };
    return emojiMap[nameEn] || "📦";
}
