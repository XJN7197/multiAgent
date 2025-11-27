<script setup lang="ts">
import { ref, computed } from 'vue';
import axios from 'axios';

interface PreliminaryCheck {
  has_risk: boolean;
  matched_keywords: string[];
}

interface LlmCheck {
  risk_level: string;
  reasoning: string;
  suggestion: string;
  error?: string;
}

interface ModerationResponse {
  ocr_text: string;
  preliminary_check: PreliminaryCheck;
  llm_check: LlmCheck | null;
  final_decision: string;
}

const selectedFile = ref<File | null>(null);
const imageUrl = ref<string | null>(null);
const moderationResult = ref<ModerationResponse | null>(null);
const isLoading = ref<boolean>(false);
const error = ref<string | null>(null);

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0 && target.files[0]) {
      selectedFile.value = target.files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        imageUrl.value = e.target?.result as string;
      };
      if (selectedFile.value) {
        reader.readAsDataURL(selectedFile.value);
      }
      // Clear previous results
      moderationResult.value = null;
      error.value = null;
    } else {
      selectedFile.value = null;
      imageUrl.value = null;
    }
};

const uploadAndModerate = async () => {
  if (!selectedFile.value) {
    alert('请先选择一张图片！');
    return;
  }

  isLoading.value = true;
  error.value = null;
  moderationResult.value = null;

  try {
    const base64Image = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (reader.result) {
          const resultString = reader.result as string;
          const parts = resultString.split(',');
          if (parts.length > 1) {
            resolve(parts[1] || '');
          } else {
            reject(new Error("Invalid data URL format."));
          }
        } else {
          reject(new Error("Failed to read file."));
        }
      };
      reader.onerror = reject;
      if (selectedFile.value) {
        reader.readAsDataURL(selectedFile.value);
      } else {
        reject(new Error("No file selected."));
      }
    });

    const response = await axios.post('http://localhost:5001/moderate_image', {
      image: base64Image,
    });
    moderationResult.value = response.data;
  } catch (err: any) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.error || err.message;
    } else {
      error.value = '发生未知错误。';
    }
    console.error('图片审核失败:', err);
  } finally {
    isLoading.value = false;
  }
};

const finalDecisionColor = computed(() => {
  if (!moderationResult.value) return 'gray';
  switch (moderationResult.value.final_decision) {
    case 'pass': return '#28a745';
    case 'reject': return '#dc3545';
    case 'manual_review': return '#ffc107';
    default: return 'gray';
  }
});

const finalDecisionText = computed(() => {
  if (!moderationResult.value) return '';
  switch (moderationResult.value.final_decision) {
    case 'pass': return '审核通过';
    case 'reject': return '审核拒绝';
    case 'manual_review': return '需人工复审';
    default: return moderationResult.value.final_decision;
  }
});
</script>

<template>
  <div class="container">
    <header>
      <h1>图片内容智能审核系统</h1>
      <p class="subtitle">基于 OCR 与 大模型的多重审核机制</p>
    </header>

    <div class="main-content">
      <!-- 左侧：上传与预览 -->
      <div class="left-panel">
        <div class="upload-card">
          <div class="upload-area">
            <input type="file" id="fileInput" @change="handleFileChange" accept="image/*" />
            <label for="fileInput" class="upload-label">
              <span v-if="!imageUrl">点击上传图片</span>
              <span v-else>点击更换图片</span>
            </label>
          </div>
          
          <button class="moderate-btn" @click="uploadAndModerate" :disabled="!selectedFile || isLoading">
            {{ isLoading ? '正在分析中...' : '开始审核' }}
          </button>
        </div>

        <div v-if="imageUrl" class="preview-card">
          <h3>图片预览</h3>
          <div class="image-wrapper">
            <img :src="imageUrl" alt="Selected Image" />
          </div>
        </div>
      </div>

      <!-- 右侧：审核流程展示 -->
      <div class="right-panel">
        <div v-if="error" class="error-card">
          <h3>错误</h3>
          <p>{{ error }}</p>
        </div>

        <div v-if="!moderationResult && !isLoading && !error" class="placeholder-card">
          <p>请上传图片并点击审核以查看详细分析报告。</p>
        </div>

        <div v-if="isLoading" class="loading-card">
          <div class="spinner"></div>
          <p>系统正在进行多维度分析...</p>
        </div>

        <div v-if="moderationResult" class="result-container">
          <!-- 步骤 1: OCR 识别 -->
          <div class="process-step">
            <div class="step-header">
              <span class="step-number">1</span>
              <h4>OCR 文字提取</h4>
            </div>
            <div class="step-content">
              <p v-if="moderationResult.ocr_text" class="ocr-text">{{ moderationResult.ocr_text }}</p>
              <p v-else class="text-muted">未在图片中识别到文字。</p>
            </div>
          </div>

          <!-- 步骤 2: 初步风险筛查 -->
          <div class="process-step">
            <div class="step-header">
              <span class="step-number">2</span>
              <h4>初步风险筛查 (敏感词库)</h4>
              <span class="status-badge" :class="moderationResult.preliminary_check.has_risk ? 'danger' : 'success'">
                {{ moderationResult.preliminary_check.has_risk ? '发现风险' : '通过' }}
              </span>
            </div>
            <div class="step-content" v-if="moderationResult.preliminary_check.has_risk">
              <p>命中敏感词:</p>
              <div class="tags">
                <span v-for="keyword in moderationResult.preliminary_check.matched_keywords" :key="keyword" class="tag">
                  {{ keyword }}
                </span>
              </div>
            </div>
          </div>

          <!-- 步骤 3: 大模型分析 -->
          <div class="process-step" v-if="moderationResult.llm_check">
            <div class="step-header">
              <span class="step-number">3</span>
              <h4>AI 深度分析 (语义理解)</h4>
            </div>
            <div class="step-content">
              <div class="info-row">
                <span class="label">风险等级:</span>
                <span class="value risk-level" :class="moderationResult.llm_check.risk_level">
                  {{ moderationResult.llm_check.risk_level.toUpperCase() }}
                </span>
              </div>
              <div class="info-row">
                <span class="label">建议操作:</span>
                <span class="value">{{ moderationResult.llm_check.suggestion.toUpperCase() }}</span>
              </div>
              <div class="info-block">
                <span class="label">分析依据:</span>
                <p class="reasoning-text">{{ moderationResult.llm_check.reasoning }}</p>
              </div>
            </div>
          </div>

          <!-- 步骤 4: 最终结论 -->
          <div class="final-result" :style="{ borderColor: finalDecisionColor, backgroundColor: finalDecisionColor + '10' }">
            <h3>最终审核结论</h3>
            <div class="decision-box" :style="{ color: finalDecisionColor }">
              {{ finalDecisionText }}
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: #333;
}

header {
  text-align: center;
  margin-bottom: 40px;
}

h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
}

.subtitle {
  color: #7f8c8d;
  font-size: 1.2rem;
}

.main-content {
  display: flex;
  gap: 40px;
  align-items: flex-start;
}

.left-panel {
  flex: 1;
  max-width: 400px;
}

.right-panel {
  flex: 2;
}

/* Upload Card */
.upload-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.upload-area input {
  display: none;
}

.upload-label {
  display: block;
  width: 100%;
  padding: 40px 0;
  border: 2px dashed #cbd5e0;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  color: #718096;
  transition: all 0.3s ease;
}

.upload-label:hover {
  border-color: #4299e1;
  color: #4299e1;
  background-color: #ebf8ff;
}

.moderate-btn {
  width: 100%;
  margin-top: 20px;
  padding: 12px;
  background-color: #4299e1;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.moderate-btn:hover {
  background-color: #3182ce;
}

.moderate-btn:disabled {
  background-color: #cbd5e0;
  cursor: not-allowed;
}

/* Preview Card */
.preview-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.preview-card h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #4a5568;
}

.image-wrapper img {
  width: 100%;
  border-radius: 8px;
}

/* Process Steps */
.result-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.process-step {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  border-left: 4px solid #e2e8f0;
}

.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.step-number {
  background-color: #4299e1;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 12px;
}

.step-header h4 {
  margin: 0;
  font-size: 1.1rem;
  color: #2d3748;
  flex-grow: 1;
}

.step-content {
  padding-left: 40px;
}

.ocr-text {
  background-color: #f7fafc;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #edf2f7;
  font-family: monospace;
  white-space: pre-wrap;
}

.text-muted {
  color: #a0aec0;
  font-style: italic;
}

/* Status Badge */
.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.success {
  background-color: #c6f6d5;
  color: #276749;
}

.status-badge.danger {
  background-color: #fed7d7;
  color: #9b2c2c;
}

/* Tags */
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.tag {
  background-color: #fff5f5;
  color: #c53030;
  border: 1px solid #feb2b2;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 0.9rem;
}

/* Info Rows */
.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-block {
  margin-top: 12px;
}

.label {
  font-weight: 600;
  color: #718096;
  width: 100px;
  display: inline-block;
}

.value {
  font-weight: 500;
}

.risk-level.high { color: #e53e3e; }
.risk-level.medium { color: #dd6b20; }
.risk-level.low { color: #d69e2e; }
.risk-level.safe { color: #38a169; }

.reasoning-text {
  margin-top: 5px;
  line-height: 1.6;
  color: #4a5568;
}

/* Final Result */
.final-result {
  background: white;
  padding: 30px;
  border-radius: 12px;
  text-align: center;
  border: 2px solid #cbd5e0;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.final-result h3 {
  margin: 0 0 15px 0;
  color: #4a5568;
}

.decision-box {
  font-size: 2rem;
  font-weight: 800;
}

/* Loading & Placeholder */
.loading-card, .placeholder-card, .error-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  color: #718096;
}

.error-card {
  border-left: 4px solid #e53e3e;
  color: #e53e3e;
  margin-bottom: 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #4299e1;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  .left-panel, .right-panel {
    max-width: 100%;
  }
}
</style>
