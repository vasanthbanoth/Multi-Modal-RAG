import axios from 'axios';

// 1. Configuration
// Change this to your actual backend URL (FastAPI defaults to port 8000 usually)
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// 2. Create Axios Instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 3. Request Interceptor: Attach Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 4. Response Interceptor: Handle Auth Errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // If 401 Unauthorized, clear token and redirect (optional logic)
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      localStorage.removeItem('access_token');
      // window.location.href = '/login'; // Uncomment to auto-redirect
    }
    return Promise.reject(error);
  }
);

// =============================================================================
// API METHODS (Mapped 1:1 to your OpenAPI Spec)
// =============================================================================

export const api = {
  // --- Authentication ---

  /**
   * Login to get access token
   * Endpoint: POST /auth/token
   * Content-Type: application/x-www-form-urlencoded (Per Spec)
   */
  login: async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    // Grant type usually defaults to password in FastAPI OAuth2
    params.append('grant_type', 'password');

    const response = await apiClient.post('/auth/token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    
    // Auto-save token for convenience
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  },

  /**
   * Get current user details
   * Endpoint: GET /auth/users/me/
   */
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/users/me/');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
  },

  // --- Core API ---

  /**
   * Health Check
   * Endpoint: GET /
   */
  checkHealth: async () => {
    const response = await apiClient.get('/');
    return response.data;
  },

  /**
   * Perform RAG Query
   * Endpoint: POST /query/
   * Content-Type: application/x-www-form-urlencoded (Per Spec)
   */
  performQuery: async (queryText, kbType = 'gkb') => {
    const params = new URLSearchParams();
    params.append('query', queryText);
    params.append('kb_type', kbType);

    const response = await apiClient.post('/query/', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  /**
   * Create Embedding
   * Endpoint: POST /embeddings/
   * Content-Type: multipart/form-data
   * @param {Object} data - { text?: string, image?: File, kb_type: string, context_id?: string }
   */
  createEmbedding: async ({ text, image, kbType = 'gkb', contextId }) => {
    const formData = new FormData();
    if (text) formData.append('text', text);
    if (image) formData.append('image', image);
    formData.append('kb_type', kbType);
    if (contextId) formData.append('context_id', contextId);

    const response = await apiClient.post('/embeddings/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Extract from Document
   * Endpoint: POST /documents/extract/
   * Content-Type: multipart/form-data
   */
  extractFromDocument: async (fileObject) => {
    const formData = new FormData();
    formData.append('file', fileObject);

    const response = await apiClient.post('/documents/extract/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

export default api;