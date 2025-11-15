/**
 * API Hook using React Query
 */
import { useQuery, useMutation, UseQueryOptions } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const useApi = <T = any>(
  endpoint: string,
  options?: UseQueryOptions<T>
) => {
  return useQuery<T>({
    queryKey: [endpoint],
    queryFn: async () => {
      const { data } = await apiClient.get(endpoint);
      return data;
    },
    refetchInterval: 5000, // Refetch every 5 seconds
    ...options,
  });
};

export const useApiMutation = <TData = any, TVariables = any>(
  endpoint: string,
  method: 'POST' | 'PUT' | 'DELETE' = 'POST'
) => {
  return useMutation<TData, Error, TVariables>({
    mutationFn: async (variables) => {
      const { data } = await apiClient.request({
        method,
        url: endpoint,
        data: variables,
      });
      return data;
    },
  });
};
