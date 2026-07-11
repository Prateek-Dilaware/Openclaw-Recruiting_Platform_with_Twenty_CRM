import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1/interviews';

export const InterviewService = {
  async getInterviews() {
    const response = await axios.get(API_BASE);
    return response.data;
  },

  async createInterview(data) {
    const response = await axios.post(API_BASE, data);
    return response.data;
  },

  async deleteInterview(id) {
    const response = await axios.delete(`${API_BASE}/${id}`);
    return response.data;
  }
};
