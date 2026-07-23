import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1/voice';

export const VoiceService = {
  async getConfig() {
    const response = await axios.get(`${API_BASE}/config`);
    return response.data;
  },

  async getVoices() {
    const response = await axios.get(`${API_BASE}/voices`);
    return response.data;
  },

  async generateSpeech(text, voiceId, candidateId) {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('voice_id', voiceId);
    if (candidateId) {
      formData.append('candidate_id', candidateId);
    }
    const response = await axios.post(`${API_BASE}/tts`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async triggerOutboundCall(phone, agentId) {
    const formData = new FormData();
    formData.append('phone', phone);
    formData.append('agent_id', agentId);
    const response = await axios.post(`${API_BASE}/outbound-call`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async getCallStatus(callId) {
    const response = await axios.get(`${API_BASE}/call-status/${callId}`);
    return response.data;
  },

  async getHistory() {
    const response = await axios.get(`${API_BASE}/history`);
    return response.data;
  }
};
