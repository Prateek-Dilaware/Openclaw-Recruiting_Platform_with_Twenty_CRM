import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1/requisitions';

export const RequisitionService = {
  async getRequisitions() {
    const response = await axios.get(API_BASE);
    return response.data;
  },

  async getRequisitionById(id) {
    const response = await axios.get(`${API_BASE}/${id}`);
    return response.data;
  },

  async createRequisition(data) {
    const response = await axios.post(API_BASE, data);
    return response.data;
  },

  async updateRequisition(id, data) {
    const response = await axios.patch(`${API_BASE}/${id}`, data);
    return response.data;
  },

  async deleteRequisition(id) {
    const response = await axios.delete(`${API_BASE}/${id}`);
    return response.data;
  },

  async parseJD(requirements) {
    const formData = new FormData();
    formData.append('requirements', requirements);
    
    const response = await axios.post(`${API_BASE}/parse-jd`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
};
