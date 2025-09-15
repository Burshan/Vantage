import { useAuth } from '@clerk/clerk-react';
import { API_BASE_URL } from '../config/api';

const useVantageAPI = () => {
  const { getToken } = useAuth();

  const apiCall = async (endpoint, options = {}) => {
    console.log(`🌐 useVantageAPI: Starting call to ${endpoint}`, options);
    
    const token = await getToken({ skipCache: true });
    console.log(`🎟️ useVantageAPI: Token obtained: ${token ? 'Present' : 'Missing'}`);
    
    if (!token) {
      console.error('❌ useVantageAPI: No auth token from Clerk');
      throw new Error('No auth token from Clerk');
    }
  
    const requestOptions = {
      method: options.method || 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      body: options.body,
      mode: 'cors',
    };
    
    console.log(`📡 useVantageAPI: Making request to ${API_BASE_URL}${endpoint}`, requestOptions);
  
    const res = await fetch(`${API_BASE_URL}${endpoint}`, requestOptions);
    
    console.log(`📥 useVantageAPI: Response status: ${res.status} ${res.statusText}`);
  
    const text = await res.text();
    console.log(`📄 useVantageAPI: Response text:`, text);
    
    let json; 
    try { 
      json = text ? JSON.parse(text) : {}; 
    } catch (parseError) { 
      console.error('❌ useVantageAPI: JSON parse error:', parseError);
      json = { error: text }; 
    }
    
    if (!res.ok) {
      console.error(`❌ useVantageAPI: HTTP error ${res.status}:`, json.error);
      throw new Error(json.error || `HTTP ${res.status}`);
    }
    
    console.log(`✅ useVantageAPI: Success response:`, json);
    return json;
  };

  return { apiCall };
};

export default useVantageAPI;