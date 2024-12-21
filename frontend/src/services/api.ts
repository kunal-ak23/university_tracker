import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});


interface ContractUpdateDTO {
  // ... other contract fields
  files_to_delete?: number[];
  uploaded_files?: File[];
  file_descriptions?: string[];
}

// Function to update contract with files
export const updateContract = async (contractId: number, data: ContractUpdateDTO) => {
  const formData = new FormData();

  // Add basic fields
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined && !['uploaded_files', 'file_descriptions', 'files_to_delete'].includes(key)) {
      formData.append(key, value.toString());
    }
  });

  // Add files to be deleted
  if (data.files_to_delete?.length) {
    data.files_to_delete.forEach(fileId => {
      formData.append('files_to_delete[]', fileId.toString());
    });
  }

  // Add new files and their descriptions
  if (data.uploaded_files?.length) {
    data.uploaded_files.forEach((file, index) => {
      formData.append('uploaded_files[]', file);
      // Make sure we have a description for each file
      const description = data.file_descriptions?.[index] || `File ${index + 1}`;
      formData.append('file_descriptions[]', description);
    });
  }

  try {
    const response = await api.patch(`/contracts/${contractId}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Contract update error:', error.response?.data || error);
    throw error;
  }
};

export default api; 