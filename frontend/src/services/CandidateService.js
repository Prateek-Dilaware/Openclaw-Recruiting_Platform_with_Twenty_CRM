import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1/candidates';

export const CandidateService = {
  async getCandidates() {
    const response = await axios.get(API_BASE);
    return response.data;
  },

  async getCandidateById(id) {
    const response = await axios.get(`${API_BASE}/${id}`);
    return response.data;
  },

  async createCandidate(data) {
    const response = await axios.post(API_BASE, data);
    return response.data;
  },

  async updateCandidate(id, data) {
    const response = await axios.patch(`${API_BASE}/${id}`, data);
    return response.data;
  },

  async deleteCandidate(id) {
    const response = await axios.delete(`${API_BASE}/${id}`);
    return response.data;
  },

  async scheduleInterview(candidateId, candidateAvailability, interviewerSlots, voiceId) {
    const formData = new FormData();
    formData.append('candidate_availability', candidateAvailability);
    formData.append('interviewer_slots', interviewerSlots);
    formData.append('voice_id', voiceId);
    
    const response = await axios.post(`${API_BASE}/${candidateId}/schedule`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async evaluateScreening(candidateId, file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE}/${candidateId}/evaluate-screening`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async generateRetrospective(candidateId) {
    const response = await axios.post(`${API_BASE}/${candidateId}/retrospective`);
    return response.data;
  },

  async triggerOutboundCall(candidateId, phone, agentId) {
    const formData = new FormData();
    formData.append('phone', phone);
    formData.append('agent_id', agentId);
    
    const response = await axios.post(`${API_BASE}/${candidateId}/trigger-outbound-call`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async fetchCallEvaluation(candidateId, callId) {
    const formData = new FormData();
    formData.append('call_id', callId);
    
    const response = await axios.post(`${API_BASE}/${candidateId}/fetch-call-evaluation`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async fetchLatestWebTranscript(candidateId, agentId) {
    const formData = new FormData();
    formData.append('agent_id', agentId);
    
    const response = await axios.post(`${API_BASE}/${candidateId}/fetch-latest-web-transcript`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
};
