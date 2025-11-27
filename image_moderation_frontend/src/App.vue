<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';

const selectedFile = ref<File | null>(null);
const imageUrl = ref<string | null>(null);
const moderationResult = ref<string | null>(null);
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
    moderationResult.value = response.data.result;
  } catch (err) {
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
</script>

<template>
  <div class="container">
    <h1>图片审核系统</h1>
    <div class="upload-section">
      <input type="file" @change="handleFileChange" accept="image/*" />
      <button @click="uploadAndModerate" :disabled="!selectedFile || isLoading">
        {{ isLoading ? '审核中...' : '审核' }}
      </button>
    </div>

    <div v-if="imageUrl" class="image-preview">
      <h2>预览图片:</h2>
      <img :src="imageUrl" alt="Selected Image" />
    </div>

    <div v-if="moderationResult" class="result-section">
      <h2>审核结果:</h2>
      <p>{{ moderationResult }}</p>
    </div>

    <div v-if="error" class="error-section">
      <h2>错误:</h2>
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 800px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-family: Arial, sans-serif;
}

h1, h2 {
  color: #333;
  text-align: center;
}

.upload-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  justify-content: center;
  align-items: center;
}

.upload-section input[type="file"] {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.upload-section button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.upload-section button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.image-preview {
  margin-top: 20px;
  text-align: center;
}

.image-preview img {
  max-width: 100%;
  height: auto;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-top: 10px;
}

.result-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #e9f7ef;
  border: 1px solid #d4edda;
  border-radius: 4px;
  color: #155724;
}

.error-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
}
</style>
